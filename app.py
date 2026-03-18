"""
🐟 Baitwatch — Fish Detector
=============================
Point d'entrée de l'application Streamlit.

Architecture :
    app.py      → ce fichier (flux principal)
    config.py   → constantes, traductions, t()
    api.py      → appel API, interprétation résultat
    ui.py       → affichage CSS, résultats, bulles
    assets/     → images (fondmarin.jpg, image_manta.jpg)

Lancer : streamlit run app.py
"""

import streamlit as st
import base64
from PIL import Image

from config import LOGO_PATH, t
from api import appel_api, interpreter_resultat
from ui import charger_fond, afficher_resultat, afficher_erreur, afficher_bulles, afficher_requin


def main():
    """
    Point d'entrée de l'application.

    Flux :
        0. L'utilisateur choisit la langue (VF / VFISH)
        1. Il choisit "fonf" ou "ifsp"
        2. Il uploade une image BRUV
        3. On envoie l'image à l'API
        4. On interprète la réponse
        5. On affiche le résultat + bulles
    """
    # ── Config page (DOIT être le 1er appel Streamlit) ───
    st.set_page_config(
        page_title="Baitwatch — Fish Detector",
        page_icon=Image.open(LOGO_PATH),
        layout="centered",
    )

    # ── Initialiser la langue dans session_state ─────────
    if "lang" not in st.session_state:
        st.session_state["lang"] = "fr"

    # ── Style ────────────────────────────────────────────
    charger_fond()

    # ── Bouton langue (en haut à droite) ─────────────────
    _, col_lang = st.columns([5, 1])
    with col_lang:
        if st.session_state["lang"] == "fr":
            bouton_label = "🐟 VFISH"
        else:
            bouton_label = "🇫🇷 VF"

        if st.button(bouton_label, use_container_width=True):
            st.session_state["lang"] = "en" if st.session_state["lang"] == "fr" else "fr"
            st.rerun()

    # ── En-tête ──────────────────────────────────────────
    with open(LOGO_PATH, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()

    st.markdown(f"""
    <h1 style="display: flex; align-items: center; justify-content: center; gap: 0.6rem;">
        <img src="data:image/jpeg;base64,{logo_b64}"
             style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;" />
        Baitwatch
    </h1>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <p style="text-align: center; color: white; font-size: 1rem; margin-top: -0.5rem; margin-bottom: 1.5rem;">
        {t("subtitle")}
    </p>
    """, unsafe_allow_html=True)
    st.divider()

    # ── Étape 1 : choix du modèle ────────────────────────
    detection_type = st.radio(
        t("radio_label"),
        options=["fonf", "ifsp"],
        format_func=lambda x: t("model_fonf") if x == "fonf" else t("model_ifsp"),
        horizontal=True,
    )

    # ── Étape 2 : upload de l'image ──────────────────────
    uploaded = st.file_uploader(
        t("upload_label"),
        type=["jpg", "jpeg", "png"],
    )

    if uploaded is None:
        st.info(t("upload_hint"))
        return

    # ── Étape 3 : affichage image + résultat côte à côte ─
    image = Image.open(uploaded)
    col_img, col_result = st.columns(2)

    with col_img:
        st.image(image, caption=t("image_caption"), use_container_width=True)

    with col_result:

        # Étape 4 : appel API
        with st.spinner(t("spinner")):
            try:
                result_brut = appel_api(image, detection_type)
            except Exception as e:
                afficher_erreur(e)
                return

        # Étape 5 : interpréter + afficher
        data = interpreter_resultat(result_brut, detection_type)
        afficher_resultat(data)

        # Debug : voir ce que l'API renvoie (à retirer en prod)
        with st.expander(t("debug_label")):
            st.json(result_brut)

    # ── Animation post-analyse ─────────────────────────────
    # > 75% → bulles paisibles 🫧
    # ≤ 75% → requin qui fonce 🦈
    if data["proba"] > 0.75:
        afficher_bulles()
    else:
        afficher_requin()

    # ── Footer ───────────────────────────────────────────
    st.divider()
    st.caption(t("footer"))


if __name__ == "__main__":
    main()
