import streamlit as st
import api_service

st.set_page_config(page_title="SN-Career-AI | Votre Coach", page_icon="🚀", layout="centered")

st.title("🚀 SN-Career-AI")
st.markdown("Échangez en direct avec votre coach de carrière virtuel.")

if not api_service.check_health():
    st.error("⚠️ Moteur hors ligne.")
    st.stop()

# Gestion de l'état (Mémoire de la session)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar pour l'upload du CV (garde l'interface principale propre pour le chat)
with st.sidebar:
    st.header("📄 Votre Profil")
    uploaded_file = st.file_uploader("Téléchargez votre CV (PDF)", type=["pdf"])
    
    if uploaded_file:
        if "uploaded_filename" not in st.session_state or st.session_state.uploaded_filename != uploaded_file.name:
            with st.spinner("Ingestion du profil..."):
                res = api_service.upload_pdf(uploaded_file.name, uploaded_file.getvalue())
                if res.status_code == 200:
                    st.session_state.uploaded_filename = uploaded_file.name
                    st.session_state.messages = [] # On vide le chat si nouveau CV
                    st.success("CV prêt !")
                else:
                    st.error("Erreur d'ingestion.")

# Affichage de l'historique des messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Champ de saisie interactif (bloqué si pas de CV)
prompt = st.chat_input("Ex: Analyse mon profil pour cette offre...", disabled="uploaded_filename" not in st.session_state)

if prompt:
    # 1. Afficher le message de l'utilisateur
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 2. Sauvegarder dans l'historique
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 3. Interroger l'API avec tout l'historique
    with st.chat_message("assistant"):
        with st.spinner("Analyse en cours..."):
            res = api_service.ask_question(prompt, st.session_state.messages[:-1]) # On envoie l'historique sans la dernière question
            
            if res.status_code == 200:
                answer = res.json()["answer"]
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error("Erreur lors de la génération de la réponse.")