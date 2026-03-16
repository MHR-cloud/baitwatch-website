import streamlit as st
import numpy as np
import base64
import time
import requests
import io
from PIL import Image

# ── Config ───────────────────────────────────────────────
API_URL = "https://baitwatch-98031171918.europe-west1.run.app/detect-fishes/"
BG_PATH = 'fondmarin.jpg'

# ── Page config ──────────────────────────────────────────
st.set_page_config(
    page_title="Baitwatch — Fish Detector",
    page_icon="🐟",
    layout="centered"
)

# ── Background local ─────────────────────────────────────
def get_base64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

bg = get_base64(BG_PATH)

# ── CSS ──────────────────────────────────────────────────
st.markdown(f"""
<style>
.stApp {{
    background-image: url("data:image/jpeg;base64,{bg}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}
section[data-testid="stMain"] > div {{
    background-color: rgba(0, 10, 30, 0.72);
    padding: 2.5rem 3rem;
    border-radius: 20px;
    max-width: 900px;
    margin: auto;
}}
h1 {{
    text-align: center;
    color: #00d4ff !important;
    font-size: 2.8rem !important;
    text-shadow: 0 0 25px rgba(0,212,255,0.6);
    letter-spacing: 2px;
}}
.subtitle {{
    text-align: center;
    color: #a0d8ef;
    font-size: 1rem;
    margin-bottom: 2rem;
    opacity: 0.85;
}}
[data-testid="stFileUploader"] {{
    background: rgba(0,212,255,0.05);
    border: 2px dashed rgba(0,212,255,0.35);
    border-radius: 14px;
    padding: 1rem;
}}
[data-testid="stMetric"] {{
    background: rgba(0,212,255,0.08);
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid rgba(0,212,255,0.2);
}}
[data-testid="stMetricValue"] {{
    color: #00d4ff !important;
    font-size: 2.5rem !important;
}}
.stProgress > div > div {{
    background: linear-gradient(90deg, #0077b6, #00d4ff) !important;
    border-radius: 10px;
}}
hr {{ border-color: rgba(0,212,255,0.2); }}
.stCaption {{ color: #7fb3c8 !important; }}
</style>
""", unsafe_allow_html=True)

# ── Interface ────────────────────────────────────────────
st.title("Baitwatch — Fish Detector")
st.markdown('<p class="subtitle">Détection automatique de poissons dans des images BRUV sous-marines</p>', unsafe_allow_html=True)
st.divider()

uploaded_file = st.file_uploader("📂 Uploade une image BRUV", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:

    col1, col2 = st.columns([1, 1])

    with col1:
        image = Image.open(uploaded_file)
        st.image(image, caption="Image analysée", width=400)

    with col2:
        with st.spinner("🔍 Analyse en cours..."):

            # Envoie l'image à l'API
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='JPEG')
            img_bytes.seek(0)

            response = requests.post(
                API_URL,
                params={"detection_type": "fonf"},
                files={"image_file": ("image.jpg", img_bytes, "image/jpeg")}
            )
            result = response.json()
            proba  = float(result.get("probability", 0))

        st.markdown("### Résultat")
        st.metric(label="Probabilité de présence d'un poisson", value=f"{proba:.1%}")
        st.progress(proba)
        st.divider()

        if proba > 0.8:
            st.success("**Poisson détecté avec haute confiance !**")

            placeholder = st.empty()
            positions = [5, 20, 35, 50, 65, 80]
            for step in range(40):
                x = (step * 3) % 115
                fish_html = f"""
                <div style="position:relative; height:70px; overflow:hidden;">
                {"".join([f'''
                <svg style="position:absolute; left:{(x + p) % 115}%;"
                     width="70" height="35" viewBox="0 0 120 60">
                  <ellipse cx="60" cy="30" rx="45" ry="15" fill="#f4a832" opacity="0.95"/>
                  <ellipse cx="60" cy="35" rx="38" ry="9" fill="#ffd580" opacity="0.5"/>
                  <polygon points="15,25 0,10 18,25" fill="#e07b10"/>
                  <polygon points="15,35 0,50 18,35" fill="#e07b10"/>
                  <polygon points="55,17 65,5 72,17" fill="#e07b10"/>
                  <circle cx="95" cy="27" r="4" fill="white"/>
                  <circle cx="96" cy="27" r="2" fill="#1a1a2e"/>
                </svg>''' for p in positions])}
                </div>
                """
                placeholder.markdown(fish_html, unsafe_allow_html=True)
                time.sleep(0.04)
            placeholder.empty()

        elif proba > 0.5:
            st.warning("**Poisson probablement présent**")
        else:
            st.error("**Aucun poisson détecté**")

        st.caption(f"Confiance : {proba:.4f} | Seuil de décision : 0.50")
