"""
🔌 api.py — Logique Backend / API
===================================
Gère tout ce qui touche à l'API :
    - Envoi d'image à l'API Cloud Run
    - Interprétation de la réponse JSON

Zéro Streamlit ici (sauf st.session_state pour la langue).
Si l'API change son format → on modifie ce fichier seulement.
"""

import streamlit as st
import requests
import io
from PIL import Image

from config import API_URL, SPECIES, SEUIL_HAUT, SEUIL_MOYEN, t


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
