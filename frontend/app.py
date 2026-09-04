import streamlit as st
import api_service

# Configuration de la page
st.set_page_config(page_title="SN-Career-AI | Votre Coach", page_icon="🚀", layout="centered")

# Initialisation de la mémoire de session
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- BARRE LATÉRALE (Contrôles et Upload) ---
with st.sidebar:
    st.header("📄 Votre Profil")
    uploaded_file = st.file_uploader("Téléchargez votre CV (PDF)", type=["pdf"])
    
    if uploaded_file:
        # Vérifie si c'est un nouveau fichier pour lancer l'upload
        if "uploaded_filename" not in st.session_state or st.session_state.uploaded_filename != uploaded_file.name:
            with st.spinner("Ingestion de votre profil..."):
                res = api_service.upload_pdf(uploaded_file.name, uploaded_file.getvalue())
                if res.status_code == 200:
                    st.session_state.uploaded_filename = uploaded_file.name
                    st.session_state.messages = [] # On vide le chat si c'est un nouveau CV
                    st.success("✅ CV prêt et analysé !")
                else:
                    st.error("Erreur lors de l'analyse du CV.")
    
    st.divider()
    
    st.markdown("### ⚙️ Gestion")
    # Le fameux bouton pour réinitialiser la conversation
    if st.button("🔄 Nouveau Coach", help="Effacer l'historique et recommencer", use_container_width=True):
        st.session_state.messages = []
        st.rerun() # Rafraîchit l'interface instantanément

# --- PAGE PRINCIPALE (Chat) ---
st.title("🚀 SN-Career-AI")
st.markdown("Échangez en direct avec votre coach de carrière virtuel. Posez des questions sur vos compétences ou analysez une offre d'emploi cible.")

# Vérification silencieuse du backend
if not api_service.check_health():
    st.error("⚠️ Le moteur d'intelligence artificielle est actuellement inaccessible. Veuillez patienter.")
    st.stop()

# Affichage de l'historique complet des messages
for msg in st.session_state.messages:
    # Attribution d'un avatar visuel selon l'auteur
    avatar_icon = "🧑‍💻" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])

# Message d'accueil automatique si le chat est vide mais que le CV est chargé
if not st.session_state.messages and "uploaded_filename" in st.session_state:
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(f"Bonjour ! J'ai parfaitement assimilé votre profil (**{st.session_state.uploaded_filename}**). Que souhaitez-vous accomplir ? Vous pouvez me copier-coller une offre d'emploi, ou me demander comment améliorer votre présentation.")

# Champ de saisie interactif (désactivé si le CV n'est pas encore là)
prompt = st.chat_input("Ex: Analyse mon profil pour cette offre de Consultant...", disabled="uploaded_filename" not in st.session_state)

if prompt:
    # 1. Affichage de la question de l'utilisateur
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)
    
    # 2. Sauvegarde de la question dans la mémoire
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 3. Interrogation de l'API et affichage de la réponse
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Analyse en cours..."):
            # On envoie l'historique à l'API (sans inclure la question actuelle qui est envoyée séparément)
            history_for_api = st.session_state.messages[:-1] 
            res = api_service.ask_question(prompt, history_for_api)
            
            if res.status_code == 200:
                answer = res.json()["answer"]
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error("Une erreur est survenue lors de l'analyse.")