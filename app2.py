"""
🐟 Baitwatch — Fish Detector
=============================
Application Streamlit pour détecter des poissons dans des images BRUV sous-marines.

L'app envoie une image à notre API (hébergée sur Cloud Run) et affiche le résultat.

Notre API accepte :
    - Une image (jpg/png)
    - Un paramètre "detection_type" qui peut être :
        • "fonf" → Fish or No Fish (est-ce qu'il y a un poisson ?)
        • "ifsp" → Identify Fish Species (quelle espèce ?)

Notre API renvoie un dictionnaire JSON :
    {
        "probability": float,   # entre 0.0 et 1.0
        "class_id": int         # identifiant de la classe prédite
    }
"""

import streamlit as st
import requests
import io
import base64
from PIL import Image


# ═══════════════════════════════════════════════════════════
# 1. CONFIGURATION
#    Tout ce qui est paramétrable est ici, facile à modifier.
# ═══════════════════════════════════════════════════════════

# URL de notre API sur Cloud Run
API_URL = "https://baitwatch-98031171918.europe-west1.run.app/detect-fishes/"

# Image de fond (doit être dans le même dossier que app.py)
BG_PATH = "fondmarin.jpg"

# Logo manta (utilisé pour l'icône de page + titre)
LOGO_PATH = "image_manta.jpg"

# Mapping des espèces : relie chaque class_id à un nom lisible
# → À compléter avec les vraies classes de ton modèle
SPECIES = {
    "fr": {
        0: "Aucun poisson",
        1: "Poisson (générique)",
        2: "Espèce A",
        3: "Espèce B",
        4: "Espèce C",
        5: "Espèce D",
        6: "Espèce E",
    },
    "en": {
        0: "No fish",
        1: "Fish (generic)",
        2: "Species A",
        3: "Species B",
        4: "Species C",
        5: "Species D",
        6: "Species E",
    },
}

# Seuils de confiance pour l'interprétation
SEUIL_HAUT = 0.80   # au-dessus → "haute confiance"
SEUIL_MOYEN = 0.50  # au-dessus → "confiance moyenne"


# ═══════════════════════════════════════════════════════════
# 1b. TRADUCTIONS
#     Toutes les chaînes de texte de l'app, en FR et EN.
#     Pour ajouter une langue : ajouter une clé ("es", "de"...)
#     Pour ajouter un texte : ajouter une ligne dans chaque langue.
# ═══════════════════════════════════════════════════════════

TEXTES = {
    "fr": {
        # En-tête
        "subtitle":         "Détection automatique de poissons · Images BRUV sous-marines",

        # Choix du modèle
        "radio_label":      "Type d'analyse :",
        "model_fonf":       "🐟 Fish or No Fish",
        "model_ifsp":       "🔬 Identifier l'espèce",

        # Upload
        "upload_label":     "📂 Uploade une image BRUV",
        "upload_hint":      "☝️ Uploade une image pour lancer l'analyse.",
        "image_caption":    "Image analysée",

        # Analyse
        "spinner":          "🔍 Analyse en cours...",

        # Résultats
        "result_label":     "Résultat",
        "confidence_label": "Confiance",
        "conf_high":        "Haute confiance dans le résultat.",
        "conf_medium":      "Confiance moyenne — résultat à vérifier.",
        "conf_low":         "Confiance faible — résultat peu fiable.",
        "class_detail":     "Classe : {class_id} · Confiance : {proba:.4f}",

        # Labels détection fonf
        "fish_detected":    "Poisson détecté",
        "no_fish":          "Aucun poisson",
        "unknown_class":    "Classe inconnue ({class_id})",

        # Erreurs
        "err_connection":   "❌ Impossible de joindre l'API. Le service est peut-être inactif.",
        "err_timeout":      "⏱️ L'API met trop de temps à répondre (timeout 30s).",
        "err_http":         "❌ Erreur HTTP : {status}",
        "err_unknown":      "❌ Erreur inattendue : {error}",

        # Debug & footer
        "debug_label":      "🛠️ Réponse brute API",
        "footer":           "Baitwatch · Le Wagon 2026 · YOLO · Cloud Run",
    },

    "en": {
        # Header
        "subtitle":         "Automatic fish detection · Underwater BRUV images",

        # Model choice
        "radio_label":      "Analysis type:",
        "model_fonf":       "🐟 Fish or No Fish",
        "model_ifsp":       "🔬 Identify Species",

        # Upload
        "upload_label":     "📂 Upload a BRUV image",
        "upload_hint":      "☝️ Upload an image to start the analysis.",
        "image_caption":    "Analyzed image",

        # Analysis
        "spinner":          "🔍 Analyzing...",

        # Results
        "result_label":     "Result",
        "confidence_label": "Confidence",
        "conf_high":        "High confidence in this result.",
        "conf_medium":      "Medium confidence — please verify.",
        "conf_low":         "Low confidence — unreliable result.",
        "class_detail":     "Class: {class_id} · Confidence: {proba:.4f}",

        # Detection labels fonf
        "fish_detected":    "Fish detected",
        "no_fish":          "No fish detected",
        "unknown_class":    "Unknown class ({class_id})",

        # Errors
        "err_connection":   "❌ Cannot reach the API. The service may be down.",
        "err_timeout":      "⏱️ The API is not responding (30s timeout).",
        "err_http":         "❌ HTTP error: {status}",
        "err_unknown":      "❌ Unexpected error: {error}",

        # Debug & footer
        "debug_label":      "🛠️ Raw API response",
        "footer":           "Baitwatch · Le Wagon 2026 · YOLO · Cloud Run",
    },
}


def t(key: str, **kwargs) -> str:
    """
    Retourne le texte traduit selon la langue active.

    Utilisation :
        t("subtitle")                          → texte simple
        t("err_http", status=404)              → texte avec variable
        t("class_detail", class_id=1, proba=0.9)  → texte formaté

    La langue est stockée dans st.session_state["lang"] ("fr" ou "en").
    """
    lang = st.session_state.get("lang", "fr")
    texte = TEXTES[lang].get(key, key)  # fallback = la clé elle-même

    # Si des kwargs sont passés, formater le texte
    if kwargs:
        return texte.format(**kwargs)
    return texte


# ═══════════════════════════════════════════════════════════
# 2. BACKEND — Logique API
#    Ici on gère : l'appel API, l'interprétation, les erreurs.
#    Zéro Streamlit dans cette section (séparation propre).
# ═══════════════════════════════════════════════════════════

def appel_api(image: Image.Image, detection_type: str) -> dict:
    """
    Envoie une image à l'API Baitwatch et retourne la réponse brute.

    Étapes :
        1. Convertir l'image PIL → bytes JPEG (format attendu par l'API)
        2. Envoyer en POST avec le paramètre detection_type
        3. Retourner le JSON de réponse

    Args:
        image:          L'image PIL uploadée par l'utilisateur.
        detection_type: "fonf" (fish or no fish) ou "ifsp" (identify species).

    Returns:
        dict — ex: {"probability": 0.92, "class_id": 1}

    Raises:
        requests.exceptions.ConnectionError: API injoignable
        requests.exceptions.Timeout: Pas de réponse en 30s
        requests.exceptions.HTTPError: Status HTTP != 200
    """
    # Étape 1 : convertir image PIL → bytes JPEG
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)  # ⚠️ Important : rembobiner sinon l'API reçoit 0 bytes

    # Étape 2 : POST vers l'API
    response = requests.post(
        API_URL,
        params={"detection_type": detection_type},
        files={"image_file": ("image.jpg", buffer, "image/jpeg")},
        timeout=30,
    )

    # Étape 3 : vérifier que tout s'est bien passé
    response.raise_for_status()

    return response.json()


def interpreter_resultat(result: dict, detection_type: str) -> dict:
    """
    Transforme la réponse brute de l'API en données prêtes à afficher.

    Pourquoi cette fonction existe :
        → Si l'API change son format de réponse, on modifie ICI seulement.
        → L'affichage (Streamlit) ne touche jamais au JSON brut directement.

    Args:
        result:         Réponse JSON brute {"probability": ..., "class_id": ...}
        detection_type: "fonf" ou "ifsp"

    Returns:
        dict avec :
            - proba    (float) : probabilité entre 0 et 1
            - class_id (int)   : ID de la classe prédite
            - label    (str)   : texte lisible traduit
            - niveau   (str)   : "haut" / "moyen" / "bas"
            - emoji    (str)   : ✅ / ⚠️ / ❌
    """
    proba = float(result.get("probability", 0))
    class_id = int(result.get("class_id", 0))

    # ── Niveau de confiance (commun aux deux modes) ──
    if proba > SEUIL_HAUT:
        niveau, emoji = "haut", "✅"
    elif proba > SEUIL_MOYEN:
        niveau, emoji = "moyen", "⚠️"
    else:
        niveau, emoji = "bas", "❌"

    # ── Label selon le mode de détection ──
    if detection_type == "fonf":
        label = t("fish_detected") if class_id == 1 else t("no_fish")
        if class_id != 1:
            emoji = "❌"
    else:
        # Mode espèces : chercher dans le mapping traduit
        lang = st.session_state.get("lang", "fr")
        species_map = SPECIES.get(lang, SPECIES["en"])
        label = species_map.get(class_id, t("unknown_class", class_id=class_id))

    return {
        "proba": proba,
        "class_id": class_id,
        "label": label,
        "niveau": niveau,
        "emoji": emoji,
    }


# ═══════════════════════════════════════════════════════════
# 3. FRONTEND — Affichage Streamlit
#    Ici on gère : le style CSS, l'affichage des résultats.
#    Cette section utilise Streamlit, mais pas requests.
# ═══════════════════════════════════════════════════════════

def charger_fond():
    """
    Charge l'image de fond en base64 et injecte le CSS.

    Pourquoi base64 ?
        → Streamlit ne sert pas les fichiers statiques facilement.
        → On encode l'image dans le CSS directement.
    """
    with open(BG_PATH, "rb") as f:
        bg_base64 = base64.b64encode(f.read()).decode()

    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{bg_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    section[data-testid="stMain"] > div {{
        background-color: rgba(0, 10, 30, 0.75);
        padding: 2.5rem 3rem;
        border-radius: 20px;
        max-width: 920px;
        margin: auto;
    }}
    h1 {{
        text-align: center;
        color: #00d4ff !important;
        font-size: 2.8rem !important;
        text-shadow: 0 0 25px rgba(0,212,255,0.5);
    }}

    /* ── Radio buttons (choix du modèle) en blanc ── */
    [data-testid="stRadio"] label,
    [data-testid="stRadio"] p,
    [data-testid="stRadio"] div {{
        color: white !important;
    }}

    /* ── Métriques : fond + texte blanc ── */
    [data-testid="stMetric"] {{
        background: rgba(0,212,255,0.08);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid rgba(0,212,255,0.2);
    }}
    [data-testid="stMetricLabel"] {{
        color: white !important;
    }}
    [data-testid="stMetricValue"] {{
        color: white !important;
        font-size: 2.2rem !important;
    }}

    /* ── Alertes (success/warning/error) en blanc ── */
    [data-testid="stAlert"] p {{
        color: white !important;
    }}

    /* ── Captions en blanc (y compris le code inline) ── */
    .stCaption, [data-testid="stCaption"] {{
        color: white !important;
    }}
    .stCaption code, [data-testid="stCaption"] code {{
        color: white !important;
        background: rgba(0,212,255,0.15) !important;
        border: 1px solid rgba(0,212,255,0.3) !important;
        border-radius: 4px !important;
        padding: 0.1rem 0.4rem !important;
    }}

    /* ── File uploader : label en blanc ── */
    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span {{
        color: white !important;
    }}

    /* ── File uploader : zone de drop style océan ── */
    [data-testid="stFileUploader"] section {{
        background: rgba(0,212,255,0.05) !important;
        border: 2px dashed rgba(0,212,255,0.35) !important;
        border-radius: 14px !important;
    }}
    [data-testid="stFileUploader"] section small,
    [data-testid="stFileUploader"] section span,
    [data-testid="stFileUploader"] section div {{
        color: white !important;
    }}
    /* Bouton "Browse files" */
    [data-testid="stFileUploader"] section button {{
        background: rgba(0,212,255,0.15) !important;
        border: 1px solid rgba(0,212,255,0.4) !important;
        color: white !important;
        border-radius: 8px !important;
    }}

    .stProgress > div > div {{
        background: linear-gradient(90deg, #0077b6, #00d4ff) !important;
    }}

    /* ── Bouton langue : style custom ── */
    .lang-btn {{
        position: fixed;
        top: 0.8rem;
        right: 1rem;
        z-index: 999;
        background: rgba(0, 10, 30, 0.85);
        border: 1px solid rgba(0,212,255,0.4);
        border-radius: 20px;
        padding: 0.35rem 0.9rem;
        color: #00d4ff;
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 1px;
        cursor: pointer;
        backdrop-filter: blur(6px);
    }}
    </style>
    """, unsafe_allow_html=True)


def afficher_resultat(data: dict):
    """
    Affiche le résultat interprété dans l'interface Streamlit.

    Args:
        data: dict retourné par interpreter_resultat()
    """
    # Métriques côte à côte
    col_a, col_b = st.columns(2)

    # Résultat : en HTML custom pour contrôler la taille de police
    with col_a:
        st.markdown(f"""
        <div style="
            background: rgba(0,212,255,0.08);
            border: 1px solid rgba(0,212,255,0.2);
            border-radius: 12px;
            padding: 1rem;
        ">
            <p style="color: white; font-size: 0.85rem; margin: 0 0 0.3rem 0;">{t('result_label')}</p>
            <p style="color: white; font-size: 1.3rem; font-weight: 600; margin: 0;">
                {data['emoji']} {data['label']}
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Confiance : st.metric normal (taille par défaut)
    col_b.metric(t("confidence_label"), f"{data['proba']:.1%}")

    # Barre de progression visuelle
    st.progress(data["proba"])

    # Message coloré selon le niveau de confiance
    messages = {
        "haut":  ("success", t("conf_high")),
        "moyen": ("warning", t("conf_medium")),
        "bas":   ("error",   t("conf_low")),
    }
    msg_type, msg_text = messages[data["niveau"]]
    getattr(st, msg_type)(msg_text)

    # Détails techniques
    st.caption(t("class_detail", class_id=data["class_id"], proba=data["proba"]))


def afficher_erreur(error: Exception):
    """
    Affiche un message d'erreur lisible selon le type de problème.

    Évite de montrer un traceback technique à l'utilisateur.
    """
    if isinstance(error, requests.exceptions.ConnectionError):
        st.error(t("err_connection"))
    elif isinstance(error, requests.exceptions.Timeout):
        st.error(t("err_timeout"))
    elif isinstance(error, requests.exceptions.HTTPError):
        st.error(t("err_http", status=error.response.status_code))
    else:
        st.error(t("err_unknown", error=error))


# ═══════════════════════════════════════════════════════════
# 4. APP PRINCIPALE
#    Le flux est simple :
#    Langue → Choisir modèle → Uploader image → Appeler API → Afficher
# ═══════════════════════════════════════════════════════════

def main():
    """
    Point d'entrée de l'application.

    Flux :
        0. L'utilisateur choisit la langue (VF / VFISH)
        1. Il choisit "fonf" ou "ifsp"
        2. Il uploade une image BRUV
        3. On envoie l'image à l'API
        4. On interprète la réponse
        5. On affiche le résultat
    """
    # ── Config page (DOIT être le 1er appel Streamlit) ───
    st.set_page_config(
        page_title="Baitwatch — Fish Detector",
        page_icon=Image.open(LOGO_PATH),
        layout="centered",
    )

    # ── Initialiser la langue dans session_state ─────────
    # session_state persiste entre les reruns de Streamlit
    if "lang" not in st.session_state:
        st.session_state["lang"] = "fr"

    # ── Style ────────────────────────────────────────────
    charger_fond()

    # ── Bouton langue (en haut à droite) ─────────────────
    # On utilise st.columns pour placer le bouton à droite
    _, col_lang = st.columns([5, 1])
    with col_lang:
        # Le label du bouton montre la langue OPPOSÉE (celle vers laquelle on switch)
        if st.session_state["lang"] == "fr":
            bouton_label = "🐟 VFISH"   # cliquer → passer en anglais
        else:
            bouton_label = "🇫🇷 VF"     # cliquer → passer en français

        if st.button(bouton_label, use_container_width=True):
            # Toggle : fr ↔ en
            st.session_state["lang"] = "en" if st.session_state["lang"] == "fr" else "fr"
            st.rerun()  # recharger toute la page avec la nouvelle langue

    # ── En-tête ──────────────────────────────────────────
    # Titre avec le logo manta en inline (encodé en base64)
    with open(LOGO_PATH, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()

    st.markdown(f"""
    <h1 style="display: flex; align-items: center; justify-content: center; gap: 0.6rem;">
        <img src="data:image/jpeg;base64,{logo_b64}"
             style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;" />
        Baitwatch
    </h1>
    """, unsafe_allow_html=True)

    # Sous-titre centré en blanc (HTML au lieu de st.caption pour le contrôle)
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

    # Pas d'image → on s'arrête là
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

    # ── Footer ───────────────────────────────────────────
    st.divider()
    st.caption(t("footer"))


# ── Lancement ────────────────────────────────────────────
if __name__ == "__main__":
    main()
