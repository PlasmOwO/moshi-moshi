# mochi_mochi_app.py
import streamlit as st
import time
import io
import base64
from PIL import Image
from api_services import transcribe_audio, translate_text, text_to_speech

# Configuration de la page
def setup_page():
    st.set_page_config(
        page_title="Mochi Mochi - Traduction JP-FR",
        page_icon="🍡",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    apply_custom_css()
    setup_session_state()

# Fonction pour initialiser l'état de session
def setup_session_state():
    if 'direction' not in st.session_state:
        st.session_state.direction = "ja-fr"
    if 'input_text' not in st.session_state:
        st.session_state.input_text = ""
    if 'translated_text' not in st.session_state:
        st.session_state.translated_text = ""
    if 'is_translated' not in st.session_state:
        st.session_state.is_translated = False
    if 'audio_data' not in st.session_state:
        st.session_state.audio_data = None

# Fonction pour générer du CSS personnalisé
def apply_custom_css():
    st.markdown("""
    <style>
        /* Styles généraux */
        .stApp {
            background-image: linear-gradient(to bottom, #fdf2f8, #ede9fe);
        }
        
        /* Personnalisation du titre */
        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(90deg, #ec4899, #6366f1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        /* Conteneurs personnalisés */
        .container {
            background-color: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        /* Étiquettes */
        .label {
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: 8px;
            display: inline-block;
            padding: 5px 10px;
            border-radius: 8px;
        }
        
        .label-ja {
            background-color: #fbcfe8;
            color: #be185d;
        }
        
        .label-fr {
            background-color: #e0e7ff;
            color: #4338ca;
        }
        
        /* Boutons */
        .translate-button {
            background: linear-gradient(90deg, #ec4899, #6366f1);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 50px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: block;
            width: 100%;
            text-align: center;
            margin: 20px 0;
        }
        
        .translate-button:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }
        
        /* Containers d'entrée et sortie */
        .text-area {
            border: 2px solid #f9a8d4;
            border-radius: 12px;
            padding: 10px;
        }
        
        .result-area {
            border: 2px solid #a5b4fc;
            border-radius: 12px;
            padding: 15px;
            background-color: #f9fafb;
            min-height: 100px;
        }
        
        /* Direction de traduction */
        .direction-switch {
            text-align: center;
            margin: 20px 0;
        }
        
        .footer {
            text-align: center;
            font-size: 0.7rem;
            color: #9ca3af;
            margin-top: 30px;
        }
    </style>
    """, unsafe_allow_html=True)

# Fonction pour créer un logo
def display_logo():
    logo_html = """
    <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 1rem;">
        <div style="width: 60px; height: 60px; background: linear-gradient(45deg, #fda4af, #c4b5fd); 
                    border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                    color: white; font-size: 24px; font-weight: bold; margin-right: 10px;
                    border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            🍡
        </div>
        <h1 class="main-title">Mochi Mochi</h1>
    </div>
    """
    st.markdown(logo_html, unsafe_allow_html=True)

# Fonction pour afficher le sélecteur de direction
def display_direction_selector():
    st.markdown('<div class="direction-switch">', unsafe_allow_html=True)
    cols = st.columns([1, 3, 1])
    with cols[1]:
        direction = st.selectbox(
            "", 
            options=["ja-fr", "fr-ja"],
            format_func=lambda x: "🇯🇵 Japonais → Français 🇫🇷" if x == "ja-fr" else "🇫🇷 Français → Japonais 🇯🇵",
            key="direction_select"
        )
        if direction != st.session_state.direction:
            st.session_state.direction = direction
            st.session_state.input_text = ""
            st.session_state.translated_text = ""
            st.session_state.is_translated = False
            st.session_state.audio_data = None
    st.markdown('</div>', unsafe_allow_html=True)

# Fonction pour afficher la zone d'entrée
def display_input_area():
    lang_label = "ja" if st.session_state.direction == "ja-fr" else "fr"
    lang_text = "日本語" if st.session_state.direction == "ja-fr" else "Français"
    
    st.markdown(
        f'<div class="label label-{lang_label}">{lang_text}</div>', 
        unsafe_allow_html=True
    )
    
    input_text = st.text_area(
        "",
        value=st.session_state.input_text,
        height=150,
        placeholder=("テキストを入力するか、音声を録音してください..." if st.session_state.direction == "ja-fr" 
                   else "Entrez du texte ou enregistrez votre voix..."),
        key="input_textarea"
    )
    
    if input_text != st.session_state.input_text:
        st.session_state.input_text = input_text
        st.session_state.is_translated = False

# Fonction pour gérer l'enregistrement audio
def handle_audio_recording():
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🎤 Enregistrer", key="record_button"):
            with st.spinner("Enregistrement en cours..."):
                # Simuler l'enregistrement (à remplacer par votre API)
                audio_data = {"status": "recorded", "sample_data": "demo"}
                transcribed_text = transcribe_audio(audio_data, st.session_state.direction.split("-")[0])
                
                st.session_state.input_text = transcribed_text
                st.session_state.is_translated = False
                st.session_state.audio_data = audio_data
                st.experimental_rerun()
    
    with col2:
        uploaded_file = st.file_uploader("📁 Importer un audio", type=["mp3", "wav", "ogg"], key="audio_uploader")
        if uploaded_file is not None:
            with st.spinner("Traitement du fichier audio..."):
                # Lire le fichier et l'envoyer à l'API
                audio_data = uploaded_file.getvalue()
                transcribed_text = transcribe_audio({"file_data": audio_data}, st.session_state.direction.split("-")[0])
                
                st.session_state.input_text = transcribed_text
                st.session_state.is_translated = False
                st.experimental_rerun()

# Fonction pour gérer la traduction
def handle_translation():
    if st.button("Traduire", key="translate_button", disabled=not st.session_state.input_text):
        with st.spinner("Traduction en cours..."):
            source_lang, target_lang = st.session_state.direction.split("-")
            translation = translate_text(st.session_state.input_text, source_lang, target_lang)
            
            st.session_state.translated_text = translation
            st.session_state.is_translated = True
            st.experimental_rerun()

# Fonction pour afficher la zone de résultat
def display_result_area():
    lang_label = "fr" if st.session_state.direction == "ja-fr" else "ja"
    lang_text = "Français" if st.session_state.direction == "ja-fr" else "日本語"
    
    st.markdown(
        f'<div class="label label-{lang_label}">{lang_text}</div>', 
        unsafe_allow_html=True
    )
    
    result_css = f"""
    <div class="result-area" style="opacity: {1 if st.session_state.is_translated else 0.5}">
        {st.session_state.translated_text if st.session_state.translated_text else 
         '<div style="color: #9ca3af; text-align: center; padding: 20px;">La traduction apparaîtra ici...</div>'}
    </div>
    """
    st.markdown(result_css, unsafe_allow_html=True)
    
    # Bouton pour écouter la traduction
    if st.session_state.translated_text:
        if st.button("🔊 Écouter la traduction", key="listen_button"):
            with st.spinner("Génération de l'audio..."):
                target_lang = st.session_state.direction.split("-")[1]
                audio_bytes = text_to_speech(st.session_state.translated_text, target_lang)
                
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
                else:
                    st.info("Fonctionnalité de synthèse vocale simulée. Intégrez votre API TTS ici.")

# Fonction pour afficher le pied de page
def display_footer():
    st.markdown('<div class="footer">Mochi Mochi © 2025 - Transcription et traduction japonais-français</div>', unsafe_allow_html=True)

# Fonction principale
def main():
    setup_page()
    display_logo()
    display_direction_selector()
    display_input_area()
    handle_audio_recording()
    handle_translation()
    display_result_area()
    display_footer()

if __name__ == "__main__":
    main()
