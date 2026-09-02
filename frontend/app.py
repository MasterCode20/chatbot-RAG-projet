import streamlit as st
import requests

API_URL = "http://158.178.197.5:8000"

st.set_page_config(page_title="Assistant RAG Enterprise", page_icon="🤖")
st.title("📄 Assistant Documentaire Intelligent (RAG API)")
st.markdown("Interface connectée au Backend FastAPI.")

# Vérification du backend
try:
    health_res = requests.get(f"{API_URL}/health", timeout=3)
    if health_res.status_code != 200:
        st.error("Le backend FastAPI est inaccessible.")
except Exception:
    st.warning("⚠️ Le serveur Backend FastAPI n'est pas démarré (`uvicorn backend.main:app`).")

uploaded_file = st.file_uploader("Téléchargez un document PDF", type=["pdf"])

if uploaded_file is not None:
    if "uploaded_filename" not in st.session_state or st.session_state.uploaded_filename != uploaded_file.name:
        with st.spinner("Envoi et indexation du document par l'API..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            res = requests.post(f"{API_URL}/upload", files=files)
            
            if res.status_code == 200:
                st.session_state.uploaded_filename = uploaded_file.name
                st.success(f"Fichier '{uploaded_file.name}' indexé avec succès via FastAPI !")
            else:
                st.error(f"Erreur lors de l'indexation : {res.json().get('detail')}")

    if "uploaded_filename" in st.session_state:
        user_query = st.text_input("Posez une question sur votre document :")

        if user_query:
            with st.spinner("Recherche via FastAPI..."):
                payload = {"question": user_query}
                res = requests.post(f"{API_URL}/chat", json=payload)
                
                if res.status_code == 200:
                    st.subheader("Réponse :")
                    st.write(res.json()["answer"])
                else:
                    st.error(f"Erreur : {res.json().get('detail')}")