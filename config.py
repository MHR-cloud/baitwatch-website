"""
⚙️ config.py — Configuration & Traductions
============================================
Tout ce qui est paramétrable est ici :
    - URL de l'API
    - Chemins des images (dans le dossier assets/)
    - Mapping des espèces (FR + EN)
    - Seuils de confiance
    - Textes traduits (FR + EN)
    - Fonction t() pour récupérer un texte traduit

Pour modifier un texte, un seuil ou ajouter une langue → c'est ici.
"""

import streamlit as st
import os

# ═══════════════════════════════════════════════════════════
# CHEMINS
# ═══════════════════════════════════════════════════════════

# Dossier racine du projet (là où se trouve ce fichier)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Dossier des images
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# ═══════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════

# URL de notre API sur Cloud Run
API_URL = "https://baitwatch-98031171918.europe-west1.run.app/detect-fishes/"

# Chemins des images (relatifs au dossier assets/)
BG_PATH = os.path.join(ASSETS_DIR, "fondmarin.jpg")
LOGO_PATH = os.path.join(ASSETS_DIR, "image_manta.jpg")
SHARK_PATH = os.path.join(ASSETS_DIR, "requin.png")

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
# TRADUCTIONS
# Toutes les chaînes de texte de l'app, en FR et EN.
# Pour ajouter une langue : ajouter une clé ("es", "de"...)
# Pour ajouter un texte : ajouter une ligne dans chaque langue.
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
        t("subtitle")                              → texte simple
        t("err_http", status=404)                   → texte avec variable
        t("class_detail", class_id=1, proba=0.9)   → texte formaté

    La langue est stockée dans st.session_state["lang"] ("fr" ou "en").
    """
    lang = st.session_state.get("lang", "fr")
    texte = TEXTES[lang].get(key, key)  # fallback = la clé elle-même

    if kwargs:
        return texte.format(**kwargs)
    return texte
