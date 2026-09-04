import streamlit as st
import requests
import os

API_URL = os.getenv("BACKEND_URL", "http://backend:8000")

# Configuration de la page (Mode Wide pour faire plus professionnel)
st.set_page_config(page_title="SN-Career-AI | Votre Coach ATS", page_icon="🚀", layout="centered")

# --- HEADER ET STORYTELLING ---
st.title("🚀 SN-Career-AI")
st.subheader("Ne lancez plus votre CV dans un trou noir.")
st.markdown("""
Entre les filtres automatisés (ATS) et le manque de retours des recruteurs, les candidats naviguent souvent à l'aveugle. 
**SN-Career-AI** analyse votre CV face à n'importe quelle offre d'emploi et vous livre un plan d'action précis pour faire mouche.
""")
st.divider()

# Vérification du backend en silence
backend_up = False
try:
    health_res = requests.get(f"{API_URL}/health", timeout=3)
    if health_res.status_code == 200:
        backend_up = True
except Exception:
    pass

if not backend_up:
    st.error("⚠️ Le moteur d'analyse SN-Career-AI est actuellement en cours de démarrage. Veuillez patienter quelques instants.")

# --- ETAPE 1 : UPLOAD ---
st.markdown("### 1️⃣ Votre Profil (CV)")
uploaded_file = st.file_uploader("Téléchargez votre CV au format PDF de manière sécurisée", type=["pdf"])

if uploaded_file is not None:
    if "uploaded_filename" not in st.session_state or st.session_state.uploaded_filename != uploaded_file.name:
        with st.spinner("Analyse et vectorisation de votre CV en cours..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            res = requests.post(f"{API_URL}/upload", files=files)
            
            if res.status_code == 200:
                st.session_state.uploaded_filename = uploaded_file.name
                st.success("✅ CV ingéré avec succès ! Le coach est prêt.")
            else:
                st.error(f"Erreur lors de l'indexation : {res.json().get('detail')}")

    # --- ETAPE 2 : ANALYSE ---
    if "uploaded_filename" in st.session_state:
        st.markdown("### 2️⃣ L'Analyse")
        user_query = st.text_area(
            "Collez ici la description du poste que vous visez, ou posez une question sur vos compétences :",
            height=150,
            placeholder="Ex: 'Analyse mon profil pour ce poste de Cloud DevOps : [Coller l'offre ici]...'"
        )

        if st.button("Lancer l'analyse experte", type="primary"):
            if user_query:
                with st.spinner("SN-Career-AI décortique l'offre et votre CV..."):
                    payload = {"question": user_query}
                    res = requests.post(f"{API_URL}/chat", json=payload)
                    
                    if res.status_code == 200:
                        st.divider()
                        st.markdown("### 🎯 Feedback du Coach")
                        # Utilisation d'une boîte d'information pour styliser la réponse
                        st.info(res.json()["answer"])
                    else:
                        st.error(f"Erreur : {res.json().get('detail')}")
            else:
                st.warning("Veuillez entrer une offre d'emploi ou une question avant de lancer l'analyse.")