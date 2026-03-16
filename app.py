"""
🎮 Game Library Manager
App Streamlit per gestire la tua collezione di giochi multi-piattaforma.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from pathlib import Path
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

# Importa servizi
import sys
sys.path.insert(0, str(Path(__file__).parent))
from services.data_manager import (
    load_library, save_library, add_game, update_game,
    remove_game, get_stats, df_to_context, PLATFORMS, STATUSES, GENRES
)
from services.rawg_service import RAWGService
from services.hltb_service import HLTBService
from services.ai_assistant import AIAssistant

# ─── Configurazione pagina ────────────────────────────────────────────────────
st.set_page_config(
    page_title="🎮 Game Library",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS personalizzato ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');

:root {
    --accent: #7C3AED;
    --accent2: #06B6D4;
    --bg-card: rgba(255,255,255,0.03);
    --border: rgba(255,255,255,0.08);
}

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

h1, h2, h3 { font-family: 'Space Mono', monospace !important; }

.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    text-align: center;
    backdrop-filter: blur(10px);
}
.stat-number {
    font-family: 'Space Mono', monospace;
    font-size: 2.2rem;
    font-weight: 700;
    color: #7C3AED;
    line-height: 1;
}
.stat-label {
    font-size: 0.8rem;
    opacity: 0.6;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.platform-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 2px;
}
.status-playing { background: #059669; color: white; }
.status-backlog { background: #D97706; color: white; }
.status-completed { background: #2563EB; color: white; }
.status-dropped { background: #6B7280; color: white; }
.status-on-hold { background: #7C3AED; color: white; }

.game-card {
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem;
    margin: 0.4rem 0;
    background: var(--bg-card);
    transition: border-color 0.2s;
}
.game-card:hover { border-color: #7C3AED; }

.chat-message-user {
    background: #7C3AED22;
    border-left: 3px solid #7C3AED;
    padding: 0.8rem 1rem;
    border-radius: 0 10px 10px 0;
    margin: 0.5rem 0;
}
.chat-message-assistant {
    background: #06B6D422;
    border-left: 3px solid #06B6D4;
    padding: 0.8rem 1rem;
    border-radius: 0 10px 10px 0;
    margin: 0.5rem 0;
}

div[data-testid="metric-container"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.8rem;
}
</style>
""", unsafe_allow_html=True)

# ─── Inizializzazione session state ──────────────────────────────────────────
if "library" not in st.session_state:
    st.session_state.library = load_library()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "rawg" not in st.session_state:
    st.session_state.rawg = RAWGService()

if "hltb" not in st.session_state:
    st.session_state.hltb = HLTBService()

if "ai" not in st.session_state:
    st.session_state.ai = AIAssistant()

# Shorthand
df = st.session_state.library
rawg: RAWGService = st.session_state.rawg
hltb: HLTBService = st.session_state.hltb
ai: AIAssistant = st.session_state.ai


# ─── Helper ───────────────────────────────────────────────────────────────────
STATUS_EMOJI = {
    "Playing": "🟢",
    "Backlog": "🟡",
    "Completed": "🔵",
    "Dropped": "⚫",
    "On Hold": "🟣",
}

PLATFORM_COLOR = {
    "Steam": "#1b2838",
    "Epic Games": "#313131",
    "GOG": "#a162da",
    "Xbox / Game Pass": "#107c10",
    "PlayStation": "#003791",
    "Nintendo": "#e60012",
}

def status_badge(status):
    css = status.lower().replace(" ", "-")
    emoji = STATUS_EMOJI.get(status, "⚪")
    return f'<span class="platform-badge status-{css}">{emoji} {status}</span>'


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🎮 Game Library")
    st.markdown("---")

    # Carica dati
    st.markdown("### 📂 Libreria")
    uploaded = st.file_uploader(
        "Carica il tuo CSV",
        type=["csv"],
        help="Colonne: title, platform, status, genre, year, personal_rating, notes"
    )
    if uploaded:
        st.session_state.library = load_library(uploaded)
        df = st.session_state.library
        st.success(f"✅ Caricati {len(df)} giochi!")

    if st.button("📥 Usa dati di esempio", use_container_width=True):
        st.session_state.library = load_library()
        df = st.session_state.library
        st.rerun()

    if len(df) > 0:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "💾 Esporta CSV",
            data=csv,
            file_name="my_games.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.markdown("---")

    # Filtri
    st.markdown("### 🔍 Filtri")
    filter_platform = st.multiselect(
        "Piattaforma",
        options=df["platform"].unique().tolist() if len(df) > 0 else PLATFORMS
    )
    filter_status = st.multiselect(
        "Stato",
        options=STATUSES
    )
    filter_genre = st.multiselect(
        "Genere",
        options=df["genre"].unique().tolist() if len(df) > 0 else GENRES
    )
    search_query = st.text_input("🔎 Cerca gioco", placeholder="es. Witcher")

    st.markdown("---")

    # API Status
    st.markdown("### ⚙️ Stato API")
    st.markdown(f"{'🟢' if rawg.available else '🔴'} **RAWG** {'Attivo' if rawg.available else 'Non configurato'}")
    st.markdown(f"{'🟢' if ai.available else '🔴'} **AI Assistant** {'Attivo' if ai.available else 'Non configurato'}")
    st.markdown("🟡 **HLTB** Attivo (scraping)")

    if not rawg.available or not ai.available:
        with st.expander("Come configurare"):
            st.markdown("""
1. Copia `.env.example` in `.env`
2. Aggiungi le tue API key
3. Riavvia l'app

**RAWG**: Registrati su [rawg.io/apidocs](https://rawg.io/apidocs) — gratis, nessun OAuth!
**AI**: Prendi la key su [console.anthropic.com](https://console.anthropic.com)
""")


# ─── Applica filtri ───────────────────────────────────────────────────────────
filtered_df = df.copy()
if filter_platform:
    filtered_df = filtered_df[filtered_df["platform"].isin(filter_platform)]
if filter_status:
    filtered_df = filtered_df[filtered_df["status"].isin(filter_status)]
if filter_genre:
    filtered_df = filtered_df[filtered_df["genre"].isin(filter_genre)]
if search_query:
    filtered_df = filtered_df[
        filtered_df["title"].str.contains(search_query, case=False, na=False)
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT - Tab navigation
# ═══════════════════════════════════════════════════════════════════════════════
tab_library, tab_stats, tab_detail, tab_add, tab_enrich, tab_ai = st.tabs([
    "📚 Libreria",
    "📊 Statistiche",
    "🔍 Dettaglio",
    "➕ Aggiungi",
    "🚀 Arricchisci",
    "🤖 AI Assistant"
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: LIBRERIA
# ═══════════════════════════════════════════════════════════════════════════════
with tab_library:
    stats = get_stats(df)

    # KPI row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("🎮 Totale", stats["total"])
    with col2:
        st.metric("🟢 In gioco", stats["playing_count"])
    with col3:
        st.metric("🟡 Backlog", stats["backlog_count"])
    with col4:
        st.metric("🔵 Completati", stats["completed_count"])
    with col5:
        avg = stats["avg_rating"]
        st.metric("⭐ Voto medio", f"{avg}/10" if avg else "N/D")

    st.markdown("---")

    # Opzioni visualizzazione
    view_mode = st.radio(
        "Vista",
        ["📋 Tabella", "🗂️ Card"],
        horizontal=True,
        label_visibility="collapsed"
    )
    sort_by = st.selectbox(
        "Ordina per",
        ["title", "platform", "status", "personal_rating", "year"],
        label_visibility="collapsed"
    )

    sorted_df = filtered_df.sort_values(sort_by, ascending=True, na_position="last")
    st.caption(f"Mostrando **{len(sorted_df)}** giochi su {len(df)} totali")

    if view_mode == "📋 Tabella":
        display_cols = ["title", "platform", "status", "genre", "year", "personal_rating"]
        display_cols = [c for c in display_cols if c in sorted_df.columns]
        st.dataframe(
            sorted_df[display_cols].rename(columns={
                "title": "Titolo",
                "platform": "Piattaforma",
                "status": "Stato",
                "genre": "Genere",
                "year": "Anno",
                "personal_rating": "Voto"
            }),
            use_container_width=True,
            height=500,
            hide_index=True
        )
    else:
        # Vista card
        cols_per_row = 3
        rows = [sorted_df.iloc[i:i+cols_per_row] for i in range(0, len(sorted_df), cols_per_row)]
        for row in rows:
            cols = st.columns(cols_per_row)
            for col, (_, game) in zip(cols, row.iterrows()):
                with col:
                    emoji = STATUS_EMOJI.get(game.get("status", ""), "⚪")
                    rating_str = f"⭐ {game['personal_rating']}/10" if pd.notna(game.get("personal_rating")) and game.get("personal_rating") != "" else ""
                    hltb_str = f"⏱️ ~{game['hltb_main']:.0f}h" if pd.notna(game.get("hltb_main")) else ""

                    st.markdown(f"""
<div class="game-card">
  <div style="font-weight:600; font-size:1rem; margin-bottom:6px">{emoji} {game['title']}</div>
  <div style="font-size:0.8rem; opacity:0.7; margin-bottom:8px">{game.get('platform','')} · {game.get('genre','')}</div>
  <div>{rating_str} {hltb_str}</div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: STATISTICHE
# ═══════════════════════════════════════════════════════════════════════════════
with tab_stats:
    if len(df) == 0:
        st.info("Carica dei giochi per vedere le statistiche!")
    else:
        stats = get_stats(df)

        col1, col2 = st.columns(2)

        with col1:
            # Grafico stato
            status_data = pd.DataFrame(
                list(stats["by_status"].items()),
                columns=["Stato", "Giochi"]
            )
            colors = ["#059669", "#D97706", "#2563EB", "#6B7280", "#7C3AED"]
            fig1 = px.pie(
                status_data,
                values="Giochi",
                names="Stato",
                title="📊 Distribuzione per Stato",
                color_discrete_sequence=colors,
                hole=0.4
            )
            fig1.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA"
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            # Grafico piattaforma
            plat_data = pd.DataFrame(
                list(stats["by_platform"].items()),
                columns=["Piattaforma", "Giochi"]
            )
            fig2 = px.bar(
                plat_data,
                x="Giochi",
                y="Piattaforma",
                orientation="h",
                title="🏢 Giochi per Piattaforma",
                color="Piattaforma",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
                showlegend=False
            )
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            # Generi top
            genre_data = pd.DataFrame(
                list(stats["by_genre"].items()),
                columns=["Genere", "Giochi"]
            )
            fig3 = px.bar(
                genre_data,
                x="Genere",
                y="Giochi",
                title="🎯 Top Generi",
                color="Giochi",
                color_continuous_scale="Purples"
            )
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
                xaxis_tickangle=-30,
                coloraxis_showscale=False
            )
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            # Distribuzione voti
            rated = df[df["personal_rating"].notna() & (df["personal_rating"].astype(str) != "")]
            if len(rated) > 0:
                fig4 = px.histogram(
                    rated,
                    x="personal_rating",
                    nbins=10,
                    title="⭐ Distribuzione Voti Personali",
                    color_discrete_sequence=["#7C3AED"]
                )
                fig4.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#FAFAFA",
                    xaxis_title="Voto",
                    yaxis_title="Giochi"
                )
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("Aggiungi voti personali per vedere la distribuzione!")

        # Insight backlog
        if stats.get("total_hltb_hours"):
            st.markdown("---")
            st.markdown("### ⏳ Stima Tempo Backlog")
            backlog_df = df[df["status"] == "Backlog"]
            if len(backlog_df) > 0 and "hltb_main" in backlog_df.columns:
                backlog_hours = backlog_df["hltb_main"].sum(skipna=True)
                if backlog_hours > 0:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🕹️ Giochi in Backlog", len(backlog_df))
                    with col2:
                        st.metric("⏱️ Ore totali (stima)", f"{backlog_hours:.0f}h")
                    with col3:
                        days = backlog_hours / 2  # 2h/giorno
                        st.metric("📅 Giorni (2h/giorno)", f"{days:.0f}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: DETTAGLIO GIOCO
# ═══════════════════════════════════════════════════════════════════════════════
with tab_detail:
    st.markdown("### 🔍 Dettaglio Gioco")

    if len(df) == 0:
        st.info("Carica dei giochi prima!")
    else:
        selected_title = st.selectbox(
            "Seleziona un gioco",
            options=sorted(df["title"].tolist())
        )

        game_row = df[df["title"] == selected_title].iloc[0]
        game_idx = df[df["title"] == selected_title].index[0]

        col_info, col_api = st.columns([1, 1])

        # Helper per valori pandas NA-safe
        def safe_val(row, key, default=None):
            v = row.get(key, default)
            return default if v is None or (hasattr(v, '__class__') and v.__class__.__name__ == 'NAType') or (isinstance(v, float) and pd.isna(v)) else v

        with col_info:
            st.markdown(f"## {game_row['title']}")
            st.markdown(f"""
| Campo | Valore |
|-------|--------|
| 🏢 Piattaforma | {safe_val(game_row, 'platform', '—')} |
| 📊 Stato | {safe_val(game_row, 'status', '—')} |
| 🎯 Genere | {safe_val(game_row, 'genre', '—')} |
| 📅 Anno | {safe_val(game_row, 'year', '—')} |
| ⭐ Voto personale | {safe_val(game_row, 'personal_rating', '—')}/10 |
""")

            notes_val = safe_val(game_row, "notes", "")
            if notes_val:
                st.markdown(f"**Note:** {notes_val}")

            # Modifica rapida
            with st.expander("✏️ Modifica"):
                cur_status = safe_val(game_row, "status", "Backlog")
                new_status = st.selectbox("Stato", STATUSES,
                    index=STATUSES.index(cur_status) if cur_status in STATUSES else 0)
                cur_rating = safe_val(game_row, "personal_rating", 0)
                new_rating = st.slider("Voto", 0.0, 10.0, float(cur_rating or 0), 0.5)
                new_notes = st.text_area("Note", value=safe_val(game_row, "notes", ""))

                if st.button("💾 Salva modifiche"):
                    st.session_state.library = update_game(
                        df, game_idx,
                        {"status": new_status, "personal_rating": new_rating, "notes": new_notes}
                    )
                    st.success("✅ Salvato!")
                    st.rerun()

            if st.button("🗑️ Rimuovi gioco", type="secondary"):
                st.session_state.library = remove_game(df, game_idx)
                st.success("Gioco rimosso!")
                st.rerun()

        with col_api:
            # Dati RAWG
            st.markdown("#### 🌐 Info da RAWG")
            if rawg.available:
                if st.button("🔄 Carica da RAWG", key="fetch_rawg"):
                    with st.spinner("Cerco su RAWG..."):
                        rawg_data = rawg.search_game(selected_title)
                        if rawg_data:
                            st.session_state.library = update_game(
                                st.session_state.library, game_idx, {
                                    "cover_url": rawg_data.get("cover_url", ""),
                                    "summary": rawg_data.get("summary", ""),
                                    "rawg_rating": rawg_data.get("rawg_rating"),
                                    "metacritic": rawg_data.get("metacritic"),
                                    "developer": rawg_data.get("developer", ""),
                                    "year": int(rawg_data["release_year"]) if rawg_data.get("release_year") and pd.isna(game_row.get("year")) else game_row.get("year"),
                                    "genre": rawg_data["genres"][0] if rawg_data.get("genres") and not game_row.get("genre") else game_row.get("genre"),
                                }
                            )
                            st.session_state[f"rawg_{selected_title}"] = rawg_data
                            df = st.session_state.library
                            game_row = df.iloc[game_idx]
                            st.success("✅ Dati RAWG caricati!")
                        else:
                            st.warning("Gioco non trovato su RAWG")
            else:
                st.caption("Configura `RAWG_API_KEY` nel `.env` per caricare copertine e descrizioni")

            # Mostra dati RAWG extra se disponibili
            rawg_extra = st.session_state.get(f"rawg_{selected_title}", {})

            cover = safe_val(game_row, "cover_url", "")
            if cover:
                st.image(cover, width=200)

            summary = safe_val(game_row, "summary", "")
            if summary:
                st.markdown(str(summary)[:400] + ("..." if len(str(summary)) > 400 else ""))

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                mc = safe_val(game_row, "metacritic") or rawg_extra.get("metacritic")
                rr = safe_val(game_row, "rawg_rating") or rawg_extra.get("rawg_rating")
                if mc:
                    st.metric("🎮 Metacritic", f"{int(mc)}/100")
                elif rr:
                    st.metric("⭐ RAWG Rating", f"{rr}/5")
            with col_r2:
                if rawg_extra.get("playtime_avg"):
                    st.metric("⏱️ Durata media", f"~{rawg_extra['playtime_avg']}h")

            dev = safe_val(game_row, "developer", "")
            if dev:
                st.caption(f"🏭 {dev}")
            if rawg_extra.get("publisher"):
                st.caption(f"📦 {rawg_extra['publisher']}")
            if rawg_extra.get("tags"):
                st.caption(f"🏷️ {' · '.join(rawg_extra['tags'][:6])}")

            # Dati HLTB
            st.markdown("#### ⏱️ HowLongToBeat")
            if st.button("🔄 Carica da HLTB", key="fetch_hltb"):
                with st.spinner("Cerco su HowLongToBeat..."):
                    hltb_data = hltb.search(selected_title)
                    if hltb_data:
                        st.session_state.library = update_game(
                            st.session_state.library, game_idx, {
                                "hltb_main": hltb_data.get("main_story"),
                                "hltb_extra": hltb_data.get("main_extra"),
                                "hltb_completionist": hltb_data.get("completionist"),
                            }
                        )
                        df = st.session_state.library
                        game_row = df.iloc[game_idx]
                        st.success("✅ Tempi caricati!")
                    else:
                        st.warning("Gioco non trovato su HLTB")

            if pd.notna(game_row.get("hltb_main")) and str(game_row.get("hltb_main")) not in ["", "nan"]:
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Main Story", hltb.format_time(game_row.get("hltb_main")))
                with col_b:
                    st.metric("Main + Extra", hltb.format_time(game_row.get("hltb_extra")))
                with col_c:
                    st.metric("100%", hltb.format_time(game_row.get("hltb_completionist")))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: AGGIUNGI GIOCO
# ═══════════════════════════════════════════════════════════════════════════════
with tab_add:
    st.markdown("### ➕ Aggiungi Gioco")

    col1, col2 = st.columns(2)
    with col1:
        new_title = st.text_input("Titolo *", placeholder="es. The Witcher 3")
        new_platform = st.selectbox("Piattaforma *", PLATFORMS)
        new_status = st.selectbox("Stato *", STATUSES)
        new_genre = st.selectbox("Genere", GENRES)

    with col2:
        new_year = st.number_input("Anno uscita", min_value=1970, max_value=2030, value=2024)
        new_rating = st.slider("Voto personale", 0.0, 10.0, 0.0, 0.5)
        new_notes = st.text_area("Note", placeholder="Impressioni, consigli...")

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        if st.button("✅ Aggiungi Gioco", type="primary", use_container_width=True):
            if not new_title:
                st.error("Il titolo è obbligatorio!")
            else:
                game_data = {
                    "title": new_title,
                    "platform": new_platform,
                    "status": new_status,
                    "genre": new_genre,
                    "year": new_year,
                    "personal_rating": new_rating if new_rating > 0 else None,
                    "notes": new_notes
                }
                st.session_state.library = add_game(df, game_data)
                save_library(st.session_state.library)
                st.success(f"✅ **{new_title}** aggiunto alla libreria!")
                st.rerun()

    # Import massivo
    st.markdown("---")
    st.markdown("### 📋 Import Massivo")
    st.markdown("""
Puoi importare più giochi da file CSV. Il file deve avere almeno le colonne `title` e `platform`.
Il separatore può essere `,` o `;` (Excel italiano) — viene rilevato automaticamente.
""")
    bulk_upload = st.file_uploader(
        "Carica CSV giochi",
        type=["csv"],
        key="bulk_import",
        help="Vedi il file games_sample.csv per il formato corretto"
    )
    if bulk_upload:
        try:
            new_df = load_library(bulk_upload)
            merged = pd.concat([df, new_df], ignore_index=True).drop_duplicates(subset=["title", "platform"])
            st.session_state.library = merged
            save_library(merged)
            st.success(f"✅ Importati {len(new_df)} giochi! Totale: {len(merged)}")
            st.rerun()
        except Exception as e:
            st.error(f"Errore nel file: {e}")

    # ── Arricchimento massivo ──────────────────────────────────────────────────
    st.info("👉 Vai al tab **🚀 Arricchisci** per scaricare automaticamente copertine, generi, anni e tempi di completamento per tutti i giochi.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: ARRICCHISCI
# ═══════════════════════════════════════════════════════════════════════════════
with tab_enrich:
    st.markdown("### 🚀 Arricchisci tutta la libreria")
    st.markdown("Scarica automaticamente **copertine, descrizioni, anno, genere, Metacritic** (RAWG) e **tempi di completamento** (HowLongToBeat) per tutti i giochi in un colpo solo.")

    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        do_rawg = st.checkbox("🌐 RAWG", value=True, disabled=not rawg.available,
            help="Copertina, descrizione, Metacritic, anno, genere" if rawg.available else "Configura RAWG_API_KEY")
    with col_e2:
        do_hltb = st.checkbox("⏱️ HowLongToBeat", value=True,
            help="Tempi di completamento")
    with col_e3:
        only_missing = st.checkbox("Solo giochi senza dati", value=True,
            help="Salta i giochi che hanno già le info")

    total_lib = len(st.session_state.library)
    st.caption(f"Libreria attuale: **{total_lib} giochi**")

    if not rawg.available and not do_hltb:
        st.warning("Configura almeno una API (RAWG o HLTB) per procedere.")
    elif st.button("▶️ Avvia arricchimento", type="primary", use_container_width=True):
        working_df = st.session_state.library.copy()

        if only_missing:
            if do_rawg and do_hltb:
                mask = working_df["cover_url"].fillna("").eq("") | working_df["hltb_main"].isna()
            elif do_rawg:
                mask = working_df["cover_url"].fillna("").eq("")
            else:
                mask = working_df["hltb_main"].isna()
            to_process = working_df[mask].index.tolist()
        else:
            to_process = working_df.index.tolist()

        total = len(to_process)
        if total == 0:
            st.info("✅ Tutti i giochi hanno già i dati richiesti!")
        else:
            progress_bar = st.progress(0, text=f"0/{total} giochi processati...")
            status_box = st.empty()
            errors = []

            for i, idx in enumerate(to_process):
                title = working_df.at[idx, "title"]
                status_box.markdown(f"🔍 **{title}**")

                if do_rawg:
                    try:
                        rawg_data = rawg.search_game(title)
                        if rawg_data:
                            working_df.at[idx, "cover_url"] = rawg_data.get("cover_url", "")
                            working_df.at[idx, "summary"] = rawg_data.get("summary", "")
                            working_df.at[idx, "rawg_rating"] = rawg_data.get("rawg_rating")
                            working_df.at[idx, "metacritic"] = rawg_data.get("metacritic")
                            working_df.at[idx, "developer"] = rawg_data.get("developer", "")
                            if rawg_data.get("release_year") and pd.isna(working_df.at[idx, "year"]):
                                working_df.at[idx, "year"] = int(rawg_data["release_year"])
                            if rawg_data.get("genres") and not working_df.at[idx, "genre"]:
                                working_df.at[idx, "genre"] = rawg_data["genres"][0]
                    except Exception as e:
                        errors.append(f"{title} (RAWG): {e}")

                if do_hltb:
                    try:
                        hltb_data = hltb.search(title)
                        if hltb_data:
                            working_df.at[idx, "hltb_main"] = hltb_data.get("main_story")
                            working_df.at[idx, "hltb_extra"] = hltb_data.get("main_extra")
                            working_df.at[idx, "hltb_completionist"] = hltb_data.get("completionist")
                    except Exception as e:
                        errors.append(f"{title} (HLTB): {e}")

                progress_bar.progress((i + 1) / total,
                    text=f"{i+1}/{total} giochi processati...")

            st.session_state.library = working_df
            save_library(working_df)
            status_box.empty()
            st.success(f"✅ Completato! {total} giochi aggiornati.")
            if errors:
                with st.expander(f"⚠️ {len(errors)} errori"):
                    for e in errors:
                        st.caption(e)
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6: AI ASSISTANT
# ═══════════════════════════════════════════════════════════════════════════════
with tab_ai:
    st.markdown("### 🤖 GamePal — Il tuo assistente AI")

    if not ai.available:
        st.warning("""
**AI non configurata.** Aggiungi la tua `ANTHROPIC_API_KEY` nel file `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```
Poi riavvia l'app con `streamlit run app.py`
""")
    else:
        library_ctx = df_to_context(df)

        # Quick actions
        st.markdown("**Suggerimenti rapidi:**")
        qcol1, qcol2, qcol3, qcol4 = st.columns(4)

        def send_quick(prompt):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.spinner("GamePal sta pensando..."):
                resp = ai.chat(st.session_state.chat_history, library_ctx)
            st.session_state.chat_history.append({"role": "assistant", "content": resp})

        with qcol1:
            if st.button("🎲 Cosa gioco stasera?", use_container_width=True):
                send_quick("Cosa dovrei giocare stasera? Considera i miei gusti dai voti che ho dato.")
        with qcol2:
            if st.button("⏱️ Ho 1 ora libera", use_container_width=True):
                send_quick("Ho solo un'ora libera. Cosa mi consigli dal backlog considerando i tempi di completamento?")
        with qcol3:
            if st.button("💎 Miglior backlog?", use_container_width=True):
                send_quick("Qual è il gioco migliore nel mio backlog che non dovrei assolutamente perdere?")
        with qcol4:
            if st.button("🗑️ Pulisci chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

        st.markdown("---")

        # Storico chat
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f"""
<div class="chat-message-user">
  <strong>👤 Tu</strong><br>{msg['content']}
</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
<div class="chat-message-assistant">
  <strong>🤖 GamePal</strong><br>{msg['content']}
</div>""", unsafe_allow_html=True)

        # Input chat
        user_input = st.chat_input("Chiedi a GamePal... (es. 'Cosa pensi di Elden Ring?')")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.spinner("GamePal sta pensando..."):
                response = ai.chat(st.session_state.chat_history, library_ctx)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()


# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center; opacity:0.4; font-size:0.8rem'>🎮 Game Library Manager · "
    "IGDB · HowLongToBeat · Claude AI</div>",
    unsafe_allow_html=True
)