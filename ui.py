"""
🎨 ui.py — Affichage Streamlit (Frontend)
==========================================
Gère tout ce qui est visuel :
    - charger_fond()      → CSS + image de fond
    - afficher_resultat() → métriques, barre, message
    - afficher_erreur()   → messages d'erreur lisibles
    - afficher_bulles()   → animation bulles d'aquarium

Cette section utilise Streamlit, mais pas requests.
"""

import streamlit as st
import requests  # uniquement pour isinstance() dans afficher_erreur
import base64

from config import BG_PATH, SHARK_PATH, t


def charger_fond():
    """
    Charge l'image de fond en base64 et injecte le CSS global.

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


def afficher_bulles():
    """
    Affiche une animation de bulles d'aquarium après l'analyse.

    100% CSS, zéro Python random :
        - 12 bulles via nth-child (pas de valeur aléatoire → pas de rerun)
        - Montée du bas vers le haut avec zigzag
        - Tailles, vitesses et délais variés directement en CSS
    """
    # 12 divs identiques, tout le style est géré par nth-child en CSS
    bulles_divs = "".join(['<div class="bulle"></div>' for _ in range(12)])

    st.markdown(f"""
    <style>
    .bulles-container {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 998;
        overflow: hidden;
    }}

    .bulle {{
        position: absolute;
        bottom: -50px;
        border-radius: 50%;
        background: radial-gradient(
            circle at 30% 30%,
            rgba(255,255,255,0.5),
            rgba(0,212,255,0.2) 50%,
            rgba(0,150,255,0.05) 100%
        );
        border: 1px solid rgba(255,255,255,0.3);
        animation: monter 6s ease-in-out forwards;
    }}

    /* ── Chaque bulle a sa propre taille, position, vitesse, délai ── */
    .bulle:nth-child(1)  {{ width:12px; height:12px; left:8%;   animation-duration:5s;   animation-delay:0s;   }}
    .bulle:nth-child(2)  {{ width:25px; height:25px; left:18%;  animation-duration:6.5s; animation-delay:0.5s; }}
    .bulle:nth-child(3)  {{ width:10px; height:10px; left:30%;  animation-duration:4.5s; animation-delay:1.2s; }}
    .bulle:nth-child(4)  {{ width:30px; height:30px; left:42%;  animation-duration:7s;   animation-delay:0.3s; }}
    .bulle:nth-child(5)  {{ width:15px; height:15px; left:55%;  animation-duration:5.5s; animation-delay:1.8s; }}
    .bulle:nth-child(6)  {{ width:20px; height:20px; left:65%;  animation-duration:6s;   animation-delay:0.8s; }}
    .bulle:nth-child(7)  {{ width:35px; height:35px; left:75%;  animation-duration:7.5s; animation-delay:0.2s; }}
    .bulle:nth-child(8)  {{ width:10px; height:10px; left:85%;  animation-duration:4s;   animation-delay:2.5s; }}
    .bulle:nth-child(9)  {{ width:18px; height:18px; left:22%;  animation-duration:5.8s; animation-delay:1.5s; }}
    .bulle:nth-child(10) {{ width:28px; height:28px; left:48%;  animation-duration:6.8s; animation-delay:0.6s; }}
    .bulle:nth-child(11) {{ width:8px;  height:8px;  left:90%;  animation-duration:4.2s; animation-delay:2s;   }}
    .bulle:nth-child(12) {{ width:22px; height:22px; left:12%;  animation-duration:6.2s; animation-delay:1s;   }}

    @keyframes monter {{
        0%   {{ transform: translateX(0)    translateY(0);     opacity: 0.5; }}
        25%  {{ transform: translateX(20px)  translateY(-25vh); opacity: 0.6; }}
        50%  {{ transform: translateX(-15px) translateY(-50vh); opacity: 0.5; }}
        75%  {{ transform: translateX(25px)  translateY(-75vh); opacity: 0.3; }}
        100% {{ transform: translateX(0)     translateY(-110vh);opacity: 0;   }}
    }}
    </style>

    <div class="bulles-container">
        {bulles_divs}
    </div>
    """, unsafe_allow_html=True)


def afficher_requin():
    """
    Affiche un requin de face qui fonce vers l'écran.

    Animation en 3 phases :
        1. Le requin apparaît petit au centre (loin dans l'eau)
        2. Il grossit en fonçant vers nous (scale 0.1 → 2.5)
        3. L'écran "tremble" légèrement quand il est proche
        4. Il ouvre la gueule puis disparaît

    100% CSS + image base64, zéro JS, zéro dépendance.
    """
    # Charger l'image requin en base64
    with open(SHARK_PATH, "rb") as f:
        shark_b64 = base64.b64encode(f.read()).decode()

    st.markdown(f"""
    <style>
    .requin-container {{
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        pointer-events: none;
        z-index: 998;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        animation: tremblement 0.15s ease-in-out 2.5s 6;
    }}

    .requin-img {{
        width: 350px;
        height: 350px;
        object-fit: contain;
        transform: scale(0.05);
        opacity: 0;
        animation: foncer 4s ease-in forwards;
    }}

    @keyframes foncer {{
        0%   {{ transform: scale(0.05); opacity: 0;   }}
        10%  {{ opacity: 1; }}
        60%  {{ transform: scale(0.8);  opacity: 1;   }}
        85%  {{ transform: scale(2.0);  opacity: 0.9; }}
        95%  {{ transform: scale(3.0);  opacity: 0.7; }}
        100% {{ transform: scale(4.0);  opacity: 0;   }}
    }}

    @keyframes tremblement {{
        0%   {{ transform: translate(0, 0);       }}
        25%  {{ transform: translate(-4px, 2px);   }}
        50%  {{ transform: translate(3px, -3px);   }}
        75%  {{ transform: translate(-2px, 4px);   }}
        100% {{ transform: translate(0, 0);        }}
    }}

    /* Bulles de panique */
    .panique-bulle {{
        position: absolute;
        border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.6), rgba(0,180,255,0.1));
        border: 1px solid rgba(255,255,255,0.3);
        animation: fuite 2s ease-out forwards;
    }}
    .panique-bulle:nth-child(1) {{ width:12px; height:12px; top:40%; left:35%; animation-delay:0.8s; --dx:-50px; --dy:-80px; }}
    .panique-bulle:nth-child(2) {{ width:8px;  height:8px;  top:55%; left:60%; animation-delay:1.2s; --dx:60px;  --dy:-70px; }}
    .panique-bulle:nth-child(3) {{ width:15px; height:15px; top:45%; left:55%; animation-delay:0.5s; --dx:-30px; --dy:50px;  }}
    .panique-bulle:nth-child(4) {{ width:6px;  height:6px;  top:50%; left:40%; animation-delay:1.5s; --dx:40px;  --dy:-90px; }}
    .panique-bulle:nth-child(5) {{ width:10px; height:10px; top:60%; left:45%; animation-delay:0.3s; --dx:-60px; --dy:40px;  }}

    @keyframes fuite {{
        0%   {{ transform: translate(0,0) scale(1); opacity: 0.7; }}
        100% {{ transform: translate(var(--dx, 30px), var(--dy, -60px)) scale(0.3); opacity: 0; }}
    }}
    </style>

    <div class="requin-container">
        <div class="panique-bulle"></div>
        <div class="panique-bulle"></div>
        <div class="panique-bulle"></div>
        <div class="panique-bulle"></div>
        <div class="panique-bulle"></div>
        <img class="requin-img" src="data:image/png;base64,{shark_b64}" />
    </div>
    """, unsafe_allow_html=True)
