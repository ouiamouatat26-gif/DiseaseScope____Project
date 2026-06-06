import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
from datetime import datetime
import re
import json
from io import BytesIO


st.set_page_config(
    page_title="DiseaseScope — Medical Research Intelligence",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)



theme_js = """
<script>
(function() {
    const theme = window.getComputedStyle(document.body).getPropertyValue('color-scheme').trim();
    const isDark = document.body.classList.contains('st-dark') || theme === 'dark';
    window.parent.streamlitApi.sendMessage({
        type: 'theme',
        isDark: isDark
    });
})();
</script>
"""


st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {
        --ds-primary: #0D9488;
        --ds-primary-light: #14B8A6;
        --ds-primary-dark: #0F766E;
        --ds-accent: #06B6D4;
        --ds-warning: #F59E0B;
        --ds-danger: #EF4444;
        --ds-success: #10B981;
        --ds-purple: #8B5CF6;
    }

    /* ── Scrollbar ───────────────────────────── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--st-text-color); opacity: 0.15; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { opacity: 0.3; }

    /* ── Global Typography ───────────────────── */
    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

    .stApp {
        background: var(--st-background-color);
        transition: background 0.3s ease;
    }

    .main .block-container {
        padding: 2.5rem 3rem;
        max-width: 1320px;
    }

    /* ── SIDEBAR ───────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
        border-right: none;
    }
    section[data-testid="stSidebar"] .stRadio {
        background: rgba(255,255,255,0.04);
        border-radius: 12px;
        padding: 6px;
    }
    section[data-testid="stSidebar"] label {
        color: rgba(255,255,255,0.7) !important;
        font-size: 0.82rem;
        font-weight: 500;
        padding: 10px 14px;
        border-radius: 8px;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }
    section[data-testid="stSidebar"] label:hover {
        background: rgba(255,255,255,0.08);
        color: #FFFFFF !important;
        border-color: rgba(255,255,255,0.1);
    }
    section[data-testid="stSidebar"] .st-bo { gap: 4px; }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
        color: #FFFFFF;
        font-size: 1.3rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: rgba(255,255,255,0.5);
        font-size: 0.72rem;
        text-align: center;
        line-height: 1.5;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.08);
        margin: 1.25rem 1rem;
    }

    /* ── HEADERS ───────────────────────────────── */
    .main-header {
        font-size: 1.9rem;
        font-weight: 700;
        color: var(--st-text-color);
        letter-spacing: -0.03em;
        margin-bottom: 0.25rem;
        line-height: 1.2;
    }
    .sub-header {
        font-size: 0.9rem;
        font-weight: 400;
        color: var(--st-text-color);
        opacity: 0.55;
        margin-bottom: 2rem;
    }

    /* ── METRIC CARDS ──────────────────────────── */
    .metric-card {
        background: var(--st-secondary-background-color);
        border: 1px solid var(--st-border-color);
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--ds-primary), var(--ds-accent));
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        border-color: var(--ds-primary);
    }
    .metric-card:hover::before { opacity: 1; }
    .metric-card .metric-icon {
        width: 38px; height: 38px;
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.2rem;
        margin-bottom: 0.6rem;
        background: rgba(13,148,136,0.1);
    }
    .metric-card .metric-value {
        font-size: 1.7rem;
        font-weight: 700;
        color: var(--st-text-color);
        letter-spacing: -0.02em;
        line-height: 1.2;
        margin-bottom: 0.2rem;
    }
    .metric-card .metric-label {
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--st-text-color);
        opacity: 0.5;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    /* ── CHART CARDS ───────────────────────────── */
    .chart-card {
        background: var(--st-secondary-background-color);
        border: 1px solid var(--st-border-color);
        border-radius: 14px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: box-shadow 0.3s ease;
    }
    .chart-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.06); }
    .chart-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--st-text-color);
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .chart-title .dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: var(--ds-primary);
    }

    /* ── ARTICLE CARDS ─────────────────────────── */
    .article-card {
        background: var(--st-secondary-background-color);
        border: 1px solid var(--st-border-color);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.6rem;
        transition: all 0.2s ease;
        border-left: 3px solid var(--ds-primary);
    }
    .article-card:hover {
        transform: translateX(3px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        border-left-color: var(--ds-accent);
    }
    .article-card .article-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--st-text-color);
        margin-bottom: 0.4rem;
        line-height: 1.4;
    }
    .article-card .article-meta {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        font-size: 0.72rem;
        color: var(--st-text-color);
        opacity: 0.55;
    }
    .article-card .article-meta span {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        background: var(--st-background-color);
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 500;
        border: 1px solid var(--st-border-color);
    }
    .article-card .article-abstract {
        font-size: 0.8rem;
        color: var(--st-text-color);
        opacity: 0.6;
        line-height: 1.5;
        margin-top: 0.5rem;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .article-card .article-link {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--ds-primary);
        text-decoration: none;
        margin-top: 0.6rem;
        transition: color 0.2s ease;
    }
    .article-card .article-link:hover { color: var(--ds-accent); }

    /* ── FILTER BAR ────────────────────────────── */
    .filter-bar {
        background: var(--st-secondary-background-color);
        border: 1px solid var(--st-border-color);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 1.25rem;
    }
    .filter-title {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--st-text-color);
        opacity: 0.5;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.6rem;
    }

    /* ── EXPANDED ARTICLE ───────────────────────── */
    .article-detail {
        background: var(--st-background-color);
        border-radius: 10px;
        padding: 1rem;
        margin-top: 0.5rem;
        border: 1px solid var(--st-border-color);
    }
    .detail-label {
        font-size: 0.65rem;
        font-weight: 700;
        color: var(--st-text-color);
        opacity: 0.45;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.15rem;
    }
    .detail-value {
        font-size: 0.8rem;
        color: var(--st-text-color);
        opacity: 0.85;
        margin-bottom: 0.6rem;
        line-height: 1.5;
    }

    /* ── ML TEST PAGE ───────────────────────────── */
    .ml-input-card {
        background: var(--st-secondary-background-color);
        border: 1px solid var(--st-border-color);
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
    }
    .prediction-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.6rem 1.25rem;
        border-radius: 50px;
        font-size: 0.9rem;
        font-weight: 700;
        color: #FFFFFF;
        background: linear-gradient(135deg, var(--ds-primary) 0%, var(--ds-accent) 100%);
        box-shadow: 0 4px 12px rgba(13,148,136,0.25);
    }
    .confidence-ring {
        width: 100px; height: 100px;
        border-radius: 50%;
        background: conic-gradient(
            var(--ds-primary) calc(var(--confidence) * 360deg),
            var(--st-border-color) 0deg
        );
        display: flex; align-items: center; justify-content: center;
        position: relative;
    }
    .confidence-ring::before {
        content: '';
        width: 76px; height: 76px;
        border-radius: 50%;
        background: var(--st-secondary-background-color);
        position: absolute;
    }
    .confidence-ring span {
        position: relative;
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--st-text-color);
    }

    /* ── SECTION DIVIDER ────────────────────────── */
    .section-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--st-border-color), transparent);
        margin: 1.75rem 0;
        border: none;
    }

    /* ── BUTTON STYLING ─────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, var(--ds-primary) 0%, var(--ds-primary-dark) 100%);
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 0.55rem 1.4rem;
        font-weight: 600;
        font-size: 0.8rem;
        transition: all 0.25s ease;
        box-shadow: 0 2px 8px rgba(13,148,136,0.2);
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(13,148,136,0.3);
    }

    /* ── PAGINATION ─────────────────────────────── */
    .pagination-info {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 0;
        font-size: 0.8rem;
        color: var(--st-text-color);
        opacity: 0.55;
    }

    /* ── STATUS BADGES ──────────────────────────── */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.68rem;
        font-weight: 600;
        border: 1px solid transparent;
    }
    .badge-success { background: rgba(16,185,129,0.1); color: var(--ds-success); border-color: rgba(16,185,129,0.2); }
    .badge-info    { background: rgba(13,148,136,0.1); color: var(--ds-primary); border-color: rgba(13,148,136,0.2); }
    .badge-warning { background: rgba(245,158,11,0.1); color: var(--ds-warning); border-color: rgba(245,158,11,0.2); }
    .badge-research{ background: rgba(139,92,246,0.1); color: var(--ds-purple); border-color: rgba(139,92,246,0.2); }

    /* ── TABS ─────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--st-secondary-background-color);
        border-radius: 10px;
        padding: 3px;
        border: 1px solid var(--st-border-color);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1.1rem;
        font-weight: 600;
        font-size: 0.8rem;
        color: var(--st-text-color);
        opacity: 0.6;
    }
    .stTabs [aria-selected="true"] {
        background: var(--ds-primary) !important;
        color: #FFFFFF !important;
        opacity: 1 !important;
    }

    /* ── DATAFRAME ──────────────────────────────── */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid var(--st-border-color);
    }

    /* ── SELECT / INPUT ───────────────────────────── */
    .stSelectbox, .stTextInput, .stSlider {
        margin-bottom: 0.4rem;
    }

    /* ── EXPANDER ─────────────────────────────────── */
    .streamlit-expanderHeader {
        background: transparent;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--st-text-color);
        opacity: 0.7;
    }
    .streamlit-expanderContent { border: none; }

    /* ── DARK MODE SPECIFIC TWEAKS ────────────────── */
    /* When Streamlit is in dark mode, these extra rules kick in */
    .st-dark .metric-card:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    }
    .st-dark .article-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .st-dark .chart-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA & MODEL LOADING
# ============================================================
@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_csv("data/articles_topics.csv", encoding="utf-8-sig")
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        return df
    except FileNotFoundError:
        st.error("Fichier `data/articles_topics.csv` non trouvé. Veuillez exécuter le pipeline Stage 1 (python src/topic_modeling.py).")
        return pd.DataFrame()

@st.cache_resource
def load_model():
    try:
        model = joblib.load("models/topic_classifier.joblib")
        vectorizer = joblib.load("models/topic_tfidf.joblib")
        le = joblib.load("models/topic_label_encoder.joblib")
        return model, vectorizer, le
    except FileNotFoundError:
        return None, None, None

def extract_year(date_str):
    if pd.isna(date_str) or str(date_str).strip() == "" or str(date_str).strip().lower() == "unknown":
        return None
    match = re.search(r"(19|20)\d{2}", str(date_str))
    return int(match.group()) if match else None

# Colonne principale pour les topics (macro-catégories propres)
def get_topic_col(df):
    """Retourne la meilleure colonne de topic disponible."""
    if "macro_topic" in df.columns:
        return "macro_topic"
    if "topic_label" in df.columns:
        return "topic_label"
    return "maladie"

def clean_topic_label(raw_label):
    if not raw_label or pd.isna(raw_label):
        return "N/A"
    raw_label = str(raw_label)
    parts = raw_label.split('_')
    if len(parts) > 1 and parts[0].replace('-', '').isdigit():
        words = parts[1:]
    else:
        words = parts
    return ", ".join(words).replace("_", " ").title()

def get_macro_for_raw_label(raw_label):
    if not raw_label or pd.isna(raw_label):
        return "Autres Spécialités"
    raw_label = str(raw_label)
    parts = raw_label.split('_')
    if len(parts) > 1 and parts[0].replace('-', '').isdigit():
        try:
            topic_id = int(parts[0])
            from src.post_process_topics import TOPIC_TO_MACRO
            return TOPIC_TO_MACRO.get(topic_id, "Autres Spécialités")
        except Exception:
            pass
    return "Autres Spécialités"


# Palette de couleurs pour les macro-catégories
MACRO_COLORS = {
    "Oncologie": "#E11D48",
    "Alzheimer & Démence": "#7C3AED",
    "Biologie Moléculaire": "#059669",
    "Cardiologie": "#DC2626",
    "Diabète & Métabolisme": "#D97706",
    "COVID-19 & Pandémies": "#0891B2",
    "Ophtalmologie": "#2563EB",
    "Autres Spécialités": "#6B7280",
    "Neurologie": "#9333EA",
    "Maladies Auto-immunes": "#EA580C",
    "Maladies Infectieuses": "#65A30D",
    "Santé Publique": "#0D9488",
    "Pharmacologie": "#4F46E5",
    "Maladies Respiratoires": "#0284C7",
    "Imagerie & IA Médicale": "#7C3AED",
    "Gastro-entérologie": "#CA8A04",
}

TYPE_COLORS = {
    "Essai clinique": "#10B981",
    "Étude observationnelle": "#0D9488",
    "Méta-analyse": "#8B5CF6",
    "Revue systématique": "#06B6D4",
    "Recherche fondamentale": "#F59E0B",
    "Étude de cas": "#EC4899",
    "Information santé": "#3B82F6",
    "Recommandation clinique": "#14B8A6",
    "Étude génomique": "#6366F1",
    "Autre": "#6B7280",
}

def class_color(class_name):
    cn = str(class_name)
    if cn in MACRO_COLORS:
        return MACRO_COLORS[cn]
    if cn in TYPE_COLORS:
        return TYPE_COLORS[cn]
    import hashlib
    hash_color = hashlib.md5(cn.encode()).hexdigest()[:6]
    return f"#{hash_color}"

def badge_class(class_name):
    mapping = {
        "Essai clinique": "badge-success",
        "Méta-analyse": "badge-research",
        "Revue systématique": "badge-info",
        "Étude observationnelle": "badge-info",
        "Recherche fondamentale": "badge-warning",
        "Étude de cas": "badge-warning",
        "Information santé": "badge-info",
        "Recommandation clinique": "badge-success",
        "Étude génomique": "badge-research",
    }
    return mapping.get(str(class_name), "badge-info")

# ============================================================
# SIDEBAR
# ============================================================
def render_sidebar():
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 1rem 0 0.5rem 0;">
                <div style="font-size: 2.2rem; margin-bottom: 0.4rem;">🧬</div>
                <h1 style="color: #FFFFFF; font-size: 1.35rem; font-weight: 700; letter-spacing: -0.02em; margin: 0;">
                    DiseaseScope
                </h1>
                <p style="color: rgba(255,255,255,0.45); font-size: 0.7rem; margin-top: 0.4rem;">
                    Medical Research Intelligence
                </p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color: rgba(255,255,255,0.08); margin: 1rem 0;'>", unsafe_allow_html=True)

        page = st.radio(
            "",
            ["📊 Dashboard", "🔍 Recherche", "🧪 Test Modèle ML"],
            label_visibility="collapsed"
        )

        st.markdown("""
            <hr style='border-color: rgba(255,255,255,0.08); margin: 1rem 0;'>
            <div style="padding: 0 0.5rem;">
                <p style="color: rgba(255,255,255,0.35); font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700;">
                    À propos
                </p>
                <p style="color: rgba(255,255,255,0.55); font-size: 0.75rem; line-height: 1.5;">
                    Plateforme d'analyse et de monitoring des publications scientifiques sur les maladies infectieuses.
                </p>
            </div>
        """, unsafe_allow_html=True)

        return page

# ============================================================
# DASHBOARD PAGE
# ============================================================
def dashboard_page(df):
    st.markdown(f"""
        <div style="margin-bottom: 1.75rem;">
            <h1 class="main-header">📊 Dashboard Analytics</h1>
            <p class="sub-header">Vue d'ensemble des publications — {datetime.now().strftime('%d %B %Y')}</p>
        </div>
    """, unsafe_allow_html=True)

    if "year" not in df.columns:
        df["year"] = df["date_publication"].apply(extract_year)

    # ── Key Metrics ──────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ("📄", len(df), "Total Articles"),
        ("🏛️", df["source"].nunique(), "Sources"),
        ("🧪", df[get_topic_col(df)].nunique(), "Catégories"),
        ("📑", df["type_contenu"].nunique() if "type_contenu" in df.columns else 0, "Types de Contenu"),
    ]
    for col, (icon, value, label) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-value">{value:,}</div>
                    <div class="metric-label">{label}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # ── Charts Row 1 ─────────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
            <div class="chart-card">
                <div class="chart-title"><span class="dot"></span> Distribution par Catégorie</div>
        """, unsafe_allow_html=True)
        tc = get_topic_col(df)
        topic_counts = df[tc].value_counts().reset_index()
        topic_counts.columns = ["Catégorie", "Nombre"]
        fig_disease = px.bar(
            topic_counts, x="Catégorie", y="Nombre",
            color="Catégorie",
            color_discrete_map={cat: class_color(cat) for cat in topic_counts["Catégorie"]},
            text="Nombre"
        )
        fig_disease.update_traces(textposition="outside", textfont_size=11)
        fig_disease.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="var(--st-text-color)"),
            xaxis=dict(showgrid=False, tickangle=-40, tickfont=dict(size=9), title_font=dict(size=11)),
            yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.08)", tickfont=dict(size=10), title_font=dict(size=11)),
            margin=dict(l=10, r=10, t=10, b=80),
            showlegend=False,
            height=380
        )
        st.plotly_chart(fig_disease, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""
            <div class="chart-card">
                <div class="chart-title"><span class="dot"></span> Répartition par Source</div>
        """, unsafe_allow_html=True)
        source_counts = df["source"].value_counts().reset_index()
        source_counts.columns = ["Source", "Nombre"]
        fig_source = px.pie(
            source_counts, values="Nombre", names="Source", hole=0.55,
            color_discrete_sequence=["#0D9488", "#14B8A6", "#06B6D4", "#0F766E", "#F59E0B", "#8B5CF6", "#10B981"]
        )
        fig_source.update_traces(textinfo="percent+label", textfont_size=11, pull=[0.02] * len(source_counts))
        fig_source.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="var(--st-text-color)"),
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=10)),
            height=320,
            annotations=[dict(text="Sources", x=0.5, y=0.5, font_size=13, font_family="Inter", showarrow=False)]
        )
        st.plotly_chart(fig_source, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Charts Row 2 ─────────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
            <div class="chart-card">
                <div class="chart-title"><span class="dot"></span> Types de Contenu</div>
        """, unsafe_allow_html=True)
        type_counts = df["type_contenu"].value_counts().reset_index()
        type_counts.columns = ["Type", "Nombre"]
        fig_type = px.bar(
            type_counts, x="Type", y="Nombre",
            color="Nombre",
            color_continuous_scale=["#0F766E", "#0D9488", "#14B8A6", "#06B6D4"],
            text="Nombre"
        )
        fig_type.update_traces(textposition="outside", textfont_size=11)
        fig_type.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="var(--st-text-color)"),
            xaxis=dict(showgrid=False, tickangle=-30, tickfont=dict(size=10), title_font=dict(size=11)),
            yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.08)", tickfont=dict(size=10), title_font=dict(size=11)),
            margin=dict(l=10, r=10, t=10, b=10),
            coloraxis_showscale=False,
            height=320
        )
        st.plotly_chart(fig_type, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""
            <div class="chart-card">
                <div class="chart-title"><span class="dot"></span> Évolution Temporelle</div>
        """, unsafe_allow_html=True)
        year_counts = df["year"].value_counts().sort_index().reset_index()
        year_counts.columns = ["Année", "Nombre"]
        fig_year = px.area(
            year_counts, x="Année", y="Nombre",
            color_discrete_sequence=["#0D9488"],
            line_shape="spline"
        )
        fig_year.update_traces(
            fill="tozeroy", fillcolor="rgba(13,148,136,0.12)",
            line=dict(width=2.5), marker=dict(size=5)
        )
        fig_year.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="var(--st-text-color)"),
            xaxis=dict(showgrid=False, tickfont=dict(size=10), title_font=dict(size=11)),
            yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.08)", tickfont=dict(size=10), title_font=dict(size=11)),
            margin=dict(l=10, r=10, t=10, b=10),
            height=320
        )
        st.plotly_chart(fig_year, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # ── Heatmaps ─────────────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
            <div class="chart-card">
                <div class="chart-title"><span class="dot"></span> Matrice Catégorie × Type</div>
        """, unsafe_allow_html=True)
        tc = get_topic_col(df)
        heatmap_data = df.groupby([tc, "type_contenu"]).size().unstack(fill_value=0) if "type_contenu" in df.columns else pd.DataFrame()
        if not heatmap_data.empty:
            fig_hm = px.imshow(
                heatmap_data.T,
                labels=dict(x="Catégorie", y="Type de Contenu", color="Articles"),
                color_continuous_scale=["#F1F5F9", "#99F6E4", "#0D9488", "#0F766E"],
                aspect="auto", text_auto=True
            )
            fig_hm.update_traces(textfont=dict(size=9))
            fig_hm.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", size=10, color="var(--st-text-color)"),
                xaxis=dict(tickangle=-30, tickfont=dict(size=9), title_font=dict(size=10)),
                yaxis=dict(tickfont=dict(size=9), title_font=dict(size=10)),
                coloraxis_colorbar=dict(tickfont=dict(size=9), title_font=dict(size=9)),
                margin=dict(l=10, r=10, t=10, b=10),
                height=360
            )
            st.plotly_chart(fig_hm, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""
            <div class="chart-card">
                <div class="chart-title"><span class="dot"></span> Matrice Catégorie × Source</div>
        """, unsafe_allow_html=True)
        tc = get_topic_col(df)
        source_matrix = df.groupby([tc, "source"]).size().unstack(fill_value=0) if "source" in df.columns else pd.DataFrame()
        if not source_matrix.empty:
            fig_sm = px.imshow(
                source_matrix.T,
                labels=dict(x="Catégorie", y="Source", color="Articles"),
                color_continuous_scale=["#F1F5F9", "#C4B5FD", "#7C3AED", "#5B21B6"],
                aspect="auto", text_auto=True
            )
            fig_sm.update_traces(textfont=dict(size=9))
            fig_sm.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", size=10, color="var(--st-text-color)"),
                xaxis=dict(tickangle=-30, tickfont=dict(size=9), title_font=dict(size=10)),
                yaxis=dict(tickfont=dict(size=9), title_font=dict(size=10)),
                coloraxis_colorbar=dict(tickfont=dict(size=9), title_font=dict(size=9)),
                margin=dict(l=10, r=10, t=10, b=10),
                height=360
            )
            st.plotly_chart(fig_sm, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# SEARCH PAGE
# ============================================================
def search_page(df):
    st.markdown(f"""
        <div style="margin-bottom: 1.75rem;">
            <h1 class="main-header">🔍 Recherche Scientifique</h1>
            <p class="sub-header">Explorez et filtrez les publications par pathologie, source et période</p>
        </div>
    """, unsafe_allow_html=True)

    if "year" not in df.columns:
        df["year"] = df["date_publication"].apply(extract_year)

    # ── Filters ──────────────────────────────────────────────
    st.markdown("""
        <div class="filter-bar">
            <div class="filter-title">Filtres de recherche</div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        topic_col = get_topic_col(df)
        disease_filter = st.selectbox("Catégorie", ["Toutes"] + sorted(df[topic_col].dropna().unique().tolist()))
    with c2:
        content_filter = st.selectbox("Type de Contenu", ["Tous"] + sorted(df["type_contenu"].dropna().unique().tolist())) if "type_contenu" in df.columns else "Tous"
    with c3:
        source_filter = st.selectbox("Source", ["Toutes"] + sorted(df["source"].dropna().unique().tolist())) if "source" in df.columns else "Toutes"

    c1, c2 = st.columns([1, 2])
    with c1:
        valid_years = df["year"].dropna().astype(int)
        yr_min = int(valid_years.min()) if len(valid_years) > 0 else 2000
        yr_max = int(valid_years.max()) if len(valid_years) > 0 else 2026
        year_range = st.slider("Plage d'Années", yr_min, yr_max, (yr_min, yr_max))
    with c2:
        search_query = st.text_input("Rechercher dans le titre ou résumé", placeholder="Mots-clés, pathologie, traitement...")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Apply Filters ────────────────────────────────────────
    filtered = df.copy()
    topic_col = get_topic_col(filtered)
    if disease_filter != "Toutes":
        filtered = filtered[filtered[topic_col] == disease_filter]
    if content_filter != "Tous" and "type_contenu" in filtered.columns:
        filtered = filtered[filtered["type_contenu"] == content_filter]
    if source_filter != "Toutes" and "source" in filtered.columns:
        filtered = filtered[filtered["source"] == source_filter]
    year_mask = filtered["year"].isna() | (
        (filtered["year"] >= year_range[0]) & (filtered["year"] <= year_range[1])
    )
    filtered = filtered[year_mask]
    if search_query.strip():
        sq = search_query.lower()
        filtered = filtered[
            filtered["titre"].astype(str).str.lower().str.contains(sq, na=False) |
            filtered["resume"].astype(str).str.lower().str.contains(sq, na=False)
        ]

    # ── Results Summary ──────────────────────────────────────
    total_found = len(filtered)
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 0.6rem; margin: 1.25rem 0;">
            <span style="font-size: 1.4rem; font-weight: 700; color: var(--ds-primary); letter-spacing: -0.02em;">{total_found}</span>
            <span style="font-size: 0.85rem; color: var(--st-text-color); opacity: 0.55;">article{'s' if total_found != 1 else ''} trouvé{'s' if total_found != 1 else ''}</span>
        </div>
    """, unsafe_allow_html=True)

    if total_found == 0:
        st.info("💡 Ajustez vos filtres pour trouver des articles correspondants.")
        return

    # ── Pagination ───────────────────────────────────────────
    page_size = 8
    total_pages = max(1, (total_found - 1) // page_size + 1)
    page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
    start, end = (page_num - 1) * page_size, min(page_num * page_size, total_found)
    page_df = filtered.iloc[start:end]

    # ── Article List ─────────────────────────────────────────
    for _, row in page_df.iterrows():
        topic_col = get_topic_col(df)
        macro = row.get(topic_col, 'N/A')
        type_c = row.get('type_contenu', 'N/A') if 'type_contenu' in df.columns else 'N/A'
        badge_tc = badge_class(type_c)
        macro_color = class_color(macro)
        title = str(row.get("titre", "Sans titre"))
        st.markdown(f"""
            <div class="article-card">
                <div class="article-title">{title}</div>
                <div class="article-meta">
                    <span style="border-color: {macro_color}40; color: {macro_color};">🏷️ {macro}</span>
                    <span class="badge {badge_tc}">📋 {type_c}</span>
                    <span>🏛️ {row.get('source', 'N/A') if 'source' in df.columns else 'N/A'}</span>
                    <span>📅 {row.get('date_publication', 'N/A')}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.expander("Voir les détails complets"):
            st.markdown(f"""
                <div class="article-detail">
                    <div class="detail-label">Résumé</div>
                    <div class="detail-value">{row.get('resume', 'Non disponible')}</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div>
                            <div class="detail-label">Journal</div>
                            <div class="detail-value">{row.get('journal', 'N/A')}</div>
                        </div>
                        <div>
                            <div class="detail-label">Année</div>
                            <div class="detail-value">{row.get('year', 'N/A')}</div>
                        </div>
                    </div>
                    {"<a class='article-link' href='" + str(row.get('lien')) + "' target='_blank'>🔗 Accéder à l'article</a>" if row.get('lien') else ""}
                </div>
            """, unsafe_allow_html=True)

    # ── Pagination Footer ────────────────────────────────────
    st.markdown(f"""
        <div class="pagination-info">
            <span>Affichage <strong>{start+1}–{end}</strong> sur <strong>{total_found}</strong></span>
            <span>Page {page_num} / {total_pages}</span>
        </div>
    """, unsafe_allow_html=True)

# ============================================================
# ML TEST PAGE
# ============================================================
def ml_test_page(model, vectorizer, le):
    st.markdown(f"""
        <div style="margin-bottom: 1.75rem;">
            <h1 class="main-header">🧪 Classification Topics</h1>
            <p class="sub-header">Testez le classifieur supervisé (LinearSVC) sur vos textes médicaux</p>
        </div>
    """, unsafe_allow_html=True)

    if model is None:
        st.error("Modèle ML non trouvé. Exécutez d'abord le pipeline complet : python src/topic_modeling.py puis python src/train_model.py")
        return

    # ── Model Info ───────────────────────────────────────────
    try:
        with open("models/topic_metrics.json", "r") as f:
            metrics = json.load(f)
        m1, m2 = st.columns(2)
        for col, val, lbl in zip(
            [m1, m2],
            [f"{metrics.get('n_articles', 'N/A'):,}", f"{metrics.get('n_classes', len(metrics.get('classes', [])))}"],
            ["Articles du corpus", "Topics découverts"]
        ):
            with col:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="font-size: 1.5rem;">{val}</div>
                        <div class="metric-label">{lbl}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='margin: 0.75rem 0;'></div>", unsafe_allow_html=True)
        raw_classes = metrics.get("classes", list(le.classes_))
        macro_classes = sorted(list(set(get_macro_for_raw_label(c) for c in raw_classes)))
        class_badges = []
        for c in macro_classes:
            color = class_color(c)
            class_badges.append(f'<span class="badge" style="background-color: {color}18; color: {color}; border-color: {color}30; border: 1px solid; margin-bottom: 0.4rem;">{c}</span>')
        class_badge_html = " ".join(class_badges)
        st.markdown(f"""
            <div style="margin-bottom: 1.25rem;">
                <span style="font-size: 0.7rem; font-weight: 600; color: var(--st-text-color); opacity: 0.5; text-transform: uppercase; letter-spacing: 0.08em;">Macro-catégories supportées</span>
                <div style="margin-top: 0.4rem; display: flex; gap: 0.4rem; flex-wrap: wrap;">{class_badge_html}</div>
            </div>
        """, unsafe_allow_html=True)
    except FileNotFoundError:
        pass

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # ── Input Section ────────────────────────────────────────
    st.markdown("""
        <div class="ml-input-card">
            <div style="font-size: 0.75rem; font-weight: 600; color: var(--st-text-color); opacity: 0.5; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.75rem;">Texte à classifier</div>
    """, unsafe_allow_html=True)

    input_text = st.text_area(
        "",
        height=140,
        placeholder="Collez ici le titre et résumé de l'article à classifier...",
        label_visibility="collapsed"
    )
    classify_btn = st.button("🔮 Lancer la Classification", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if classify_btn and input_text.strip():
        X = vectorizer.transform([input_text.lower()])
        pred = model.predict(X)[0]
        predicted_class = le.inverse_transform([pred])[0]

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0]
        else:
            scores = model.decision_function(X)

            if scores.ndim == 1:
                if len(le.classes_) == 2:
                    scores = np.array([[-scores[0], scores[0]]])
                else:
                    scores = np.array([scores])

            exp_scores = np.exp(scores[0] - np.max(scores[0]))
            proba = exp_scores / exp_scores.sum()

        confidence = float(max(proba))

        st.markdown("""
            <div class="ml-input-card" style="background: var(--st-background-color);">
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.25rem;">
                    <span style="font-size: 0.75rem; font-weight: 600; color: var(--st-text-color); opacity: 0.5; text-transform: uppercase; letter-spacing: 0.08em;">Résultat</span>
                    <div style="flex: 1; height: 1px; background: linear-gradient(90deg, var(--st-border-color), transparent);"></div>
                </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns([1, 1])
        with c1:
            macro_pred = get_macro_for_raw_label(predicted_class)
            pred_color = class_color(macro_pred)
            cleaned_sub = clean_topic_label(predicted_class)
            st.markdown(f"""
                <div style="margin-bottom: 0.75rem;">
                    <div style="font-size: 0.7rem; font-weight: 600; color: var(--st-text-color); opacity: 0.5; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.4rem;">Catégorie Prédite</div>
                    <span class="prediction-badge" style="background: linear-gradient(135deg, {pred_color} 0%, {pred_color}dd 100%); box-shadow: 0 4px 12px {pred_color}40;">
                        {macro_pred.upper()}
                    </span>
                    <div style="font-size: 0.75rem; color: var(--st-text-color); opacity: 0.7; margin-top: 0.6rem;">
                        <strong>Sujet spécifique :</strong> <span style="color: {pred_color}; font-weight: 600;">{cleaned_sub}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
                <div style="margin-bottom: 0.75rem;">
                    <div style="font-size: 0.7rem; font-weight: 600; color: var(--st-text-color); opacity: 0.5; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.4rem;">Confiance</div>
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div class="confidence-ring" style="--confidence: {confidence};">
                            <span>{confidence:.0%}</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # ── Probability Chart ────────────────────────────────
        st.markdown("""
            <div class="chart-card" style="margin-top: 1.25rem;">
                <div class="chart-title"><span class="dot"></span> Top 5 des prédictions les plus probables</div>
        """, unsafe_allow_html=True)

        proba_df = pd.DataFrame({
            "Raw_Classe": le.classes_,
            "Score": proba
        })
        proba_df["Macro"] = proba_df["Raw_Classe"].apply(get_macro_for_raw_label)
        proba_df["Sujet"] = proba_df["Raw_Classe"].apply(clean_topic_label)
        proba_df["Classe"] = proba_df["Macro"] + " (" + proba_df["Sujet"] + ")"
        
        # Sort and take top 5
        proba_df = proba_df.sort_values("Score", ascending=True).tail(5)
        
        colors = [class_color(c) for c in proba_df["Macro"]]
        fig_proba = px.bar(
            proba_df, x="Score", y="Classe", orientation="h",
            text=proba_df["Score"].apply(lambda v: f"{v:.1%}"),
            color="Macro",
            color_discrete_map={m: class_color(m) for m in proba_df["Macro"]}
        )
        fig_proba.update_traces(
            textposition="outside",
            textfont=dict(size=10, family="Inter, sans-serif"),
        )
        fig_proba.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=10, color="var(--st-text-color)"),
            xaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.08)", tickformat=".0%", range=[0, 1.1]),
            yaxis=dict(showgrid=False),
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False,
            height=260,
            bargap=0.3
        )
        st.plotly_chart(fig_proba, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    elif classify_btn:
        st.warning("Veuillez entrer un texte à classifier.")

# ============================================================
# MAIN
# ============================================================
def main():
    df = load_data()
    model, vectorizer, le = load_model()
    page = render_sidebar()

    if df.empty:
        st.error("Aucune donnée disponible. Veuillez exécuter les scripts de classification.")
        return

    if page == "📊 Dashboard":
        dashboard_page(df)
    elif page == "🔍 Recherche":
        search_page(df)
    elif page == "🧪 Test Modèle ML":
        ml_test_page(model, vectorizer, le)

if __name__ == "__main__":
    main()