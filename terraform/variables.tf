variable "tenancy_ocid" {
  type        = string
  description = "OCID de la Tenancy OCI"
}

variable "user_ocid" {
  type        = string
  description = "OCID de l'utilisateur OCI"
}

variable "fingerprint" {
  type        = string
  description = "Fingerprint de la clé API OCI"
}

variable "private_key_path" {
  type        = string
  description = "Chemin absolu vers la clé privée API OCI"
}

variable "region" {
  type        = string
  default     = "eu-paris-1"
  description = "Région Oracle Cloud"
}

variable "compartment_ocid" {
  type        = string
  description = "OCID du compartiment devsecops-k8s"
}

variable "ssh_public_key_path" {
  type        = string
  description = "Chemin vers la clé SSH publique"
}