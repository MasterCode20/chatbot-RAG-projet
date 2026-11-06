# --- 1. RESEAU (VCN & SUBNET) ---

resource "oci_core_vcn" "k8s_vcn" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "k8s-vcn"
  dns_label      = "k8svcn"
}

resource "oci_core_internet_gateway" "k8s_ig" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.k8s_vcn.id
  display_name   = "k8s-internet-gateway"
}

resource "oci_core_route_table" "k8s_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.k8s_vcn.id
  display_name   = "k8s-route-table"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.k8s_ig.id
  }
}

resource "oci_core_security_list" "k8s_sec_list" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.k8s_vcn.id
  display_name   = "k8s-security-list"

  # Traffic sortant totalement autorisé
  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  # SSH (Port 22)
  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 22
      max = 22
    }
  }

  # HTTP (Port 80)
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 80
      max = 80
    }
  }

  # HTTPS (Port 443)
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 443
      max = 443
    }
  }

  # API Kubernetes (Port 6443)
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 6443
      max = 6443
    }
  }

  # Communication interne au sous-réseau (Inter-nodes K8s)
  ingress_security_rules {
    protocol = "all"
    source   = "10.0.1.0/24"
  }
}

resource "oci_core_subnet" "k8s_subnet" {
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.k8s_vcn.id
  cidr_block        = "10.0.1.0/24"
  display_name      = "k8s-public-subnet"
  dns_label         = "k8ssubnet"
  route_table_id    = oci_core_route_table.k8s_rt.id
  security_list_ids = [oci_core_security_list.k8s_sec_list.id]
}

# --- 2. RECHERCHE DE L'IMAGE UBUNTU ARM ---

data "oci_core_images" "ubuntu_arm" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = "VM.Standard.A1.Flex"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

# --- 3. SCRIPTS AUTOMATISES CLOUD-INIT (K3S) ---

locals {
  k3s_token = "DevSecOpsTokenSecret2026!Key"
}

# Script pour le Master Node
data "cloudinit_config" "master_config" {
  gzip          = false
  base64_encode = true

  part {
    content_type = "text/x-shellscript"
    content      = <<-EOF
      #!/bin/bash
      # Autoriser le pare-feu local Ubuntu (iptables)
      iptables -F
      netfilter-persistent save
      # Installation K3s Server (Master)
      curl -sfL https://get.k3s.io | K3S_TOKEN="${local.k3s_token}" sh -s - server --write-kubeconfig-mode 644
    EOF
  }
}

# Script pour le Worker Node
data "cloudinit_config" "worker_config" {
  gzip          = false
  base64_encode = true

  part {
    content_type = "text/x-shellscript"
    content      = <<-EOF
      #!/bin/bash
      iptables -F
      netfilter-persistent save
      # Attente du master puis jonction au cluster via son IP privée (10.0.1.10)
      curl -sfL https://get.k3s.io | K3S_URL="https://10.0.1.10:6443" K3S_TOKEN="${local.k3s_token}" sh -
    EOF
  }
}

# --- 4. COMPUTE INSTANCES (VMs) ---

# Master Node (2 OCPUs / 12 GB RAM)
resource "oci_core_instance" "k8s_master" {
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "k8s-master"
  shape               = "VM.Standard.A1.Flex"

  shape_config {
    ocpus         = 2
    memory_in_gbs = 12
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.k8s_subnet.id
    private_ip       = "10.0.1.10"
    assign_public_ip = true
    display_name     = "vnic-master"
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.ubuntu_arm.images[0].id
  }

  metadata = {
    ssh_authorized_keys = file(var.ssh_public_key_path)
    user_data           = data.cloudinit_config.master_config.rendered
  }
}

# Worker Node (2 OCPUs / 12 GB RAM)
resource "oci_core_instance" "k8s_worker" {
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "k8s-worker"
  shape               = "VM.Standard.A1.Flex"

  shape_config {
    ocpus         = 2
    memory_in_gbs = 12
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.k8s_subnet.id
    assign_public_ip = true
    display_name     = "vnic-worker"
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.ubuntu_arm.images[0].id
  }

  metadata = {
    ssh_authorized_keys = file(var.ssh_public_key_path)
    user_data           = data.cloudinit_config.worker_config.rendered
  }

  depends_on = [oci_core_instance.k8s_master]
}

# --- 5. OUTPUTS (AFFICHAGE DES IPs) ---

output "master_public_ip" {
  value       = oci_core_instance.k8s_master.public_ip
  description = "IP publique du Node Master"
}

output "worker_public_ip" {
  value       = oci_core_instance.k8s_worker.public_ip
  description = "IP publique du Node Worker"
}