"""
Gestione dei dati della libreria giochi.
Supporta caricamento da CSV e salvataggio locale.
"""

import pandas as pd
import os
import json
from pathlib import Path

PLATFORMS = ["Steam", "Epic Games", "GOG", "Xbox / Game Pass", "PlayStation", "Nintendo", "Altro"]
STATUSES = ["Backlog", "Playing", "Completed", "Dropped", "On Hold"]
GENRES = [
    "Action", "Action RPG", "Adventure", "Fighting", "FPS", "Horror",
    "Metroidvania", "Open World", "Platformer", "Puzzle", "Racing",
    "Rhythm Action", "Roguelite", "RPG", "Simulation", "Sports",
    "Strategy", "Survival", "Visual Novel", "Exploration", "Altro"
]

DEFAULT_COLUMNS = {
    "title": str,
    "platform": str,
    "status": str,       # default: "Backlog"
    "genre": str,
    "year": "Int64",
    "personal_rating": "Float64",
    "notes": str,
    # Campi arricchiti da API (opzionali)
    "cover_url": str,
    "summary": str,
    "rawg_rating": "Float64",
    "metacritic": "Int64",
    "developer": str,
    "hltb_main": "Float64",
    "hltb_extra": "Float64",
    "hltb_completionist": "Float64",
}

DATA_PATH = Path("data/my_games.csv")
SAMPLE_PATH = Path("data/games_sample.csv")


def load_library(uploaded_file=None) -> pd.DataFrame:
    """
    Carica la libreria da:
    1. File uploadato dall'utente
    2. File salvato localmente
    3. Dati di esempio
    """
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file,encoding="latin-1", quotechar='"',
            on_bad_lines="skip",
            engine="python")
    elif DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH)
    elif SAMPLE_PATH.exists():
        df = pd.read_csv(SAMPLE_PATH)
    else:
        df = pd.DataFrame(columns=list(DEFAULT_COLUMNS.keys()))

    return _normalize_df(df)


def save_library(df: pd.DataFrame):
    """Salva la libreria su CSV locale."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PATH, index=False)


def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizza il DataFrame accettando CSV minimali (solo title + platform).
    - Rinomina colonne con nomi alternativi comuni
    - Aggiunge colonne mancanti con valori di default
    - Imposta 'Backlog' come stato di default per i giochi senza stato
    """
    # Rinomina colonne con nomi alternativi comuni
    rename_map = {
        "name": "title",
        "game": "title",
        "gioco": "title",
        "titolo": "title",
        "piattaforma": "platform",
        "stato": "status",
        "genere": "genre",
        "anno": "year",
        "voto": "personal_rating",
        "rating": "personal_rating",
        "note": "notes",
    }
    df = df.rename(columns={c: rename_map[c] for c in df.columns if c.lower() in rename_map})
    df.columns = [c.lower().strip() for c in df.columns]

    # Aggiungi colonne mancanti
    for col, dtype in DEFAULT_COLUMNS.items():
        if col not in df.columns:
            df[col] = "" if dtype == str else pd.NA

    # Pulisci stringhe
    for col in ["title", "platform", "status", "genre", "notes", "cover_url", "summary", "developer"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    # Default: giochi senza stato → Backlog
    df["status"] = df["status"].apply(lambda s: s if s in STATUSES else "Backlog")

    # Rimuovi righe completamente vuote o senza titolo
    df = df[df["title"].str.strip() != ""].reset_index(drop=True)

    return df


def add_game(df: pd.DataFrame, game_data: dict) -> pd.DataFrame:
    """Aggiungi un nuovo gioco alla libreria."""
    new_row = {col: game_data.get(col, "" if DEFAULT_COLUMNS.get(col) == str else pd.NA)
               for col in DEFAULT_COLUMNS.keys()}
    new_df = pd.DataFrame([new_row])
    return pd.concat([df, new_df], ignore_index=True)


def update_game(df: pd.DataFrame, index: int, game_data: dict) -> pd.DataFrame:
    """Aggiorna un gioco esistente."""
    for key, value in game_data.items():
        if key in df.columns:
            df.at[index, key] = value
    return df


def remove_game(df: pd.DataFrame, index: int) -> pd.DataFrame:
    """Rimuovi un gioco dalla libreria."""
    return df.drop(index=index).reset_index(drop=True)


def get_stats(df: pd.DataFrame) -> dict:
    """Calcola statistiche aggregate della libreria."""
    total = len(df)
    by_status = df["status"].value_counts().to_dict()
    by_platform = df["platform"].value_counts().to_dict()
    by_genre = df["genre"].value_counts().head(10).to_dict()

    rated = df[df["personal_rating"].notna() & (df["personal_rating"] > 0)]
    avg_rating = float(rated["personal_rating"].mean()) if len(rated) > 0 else 0

    total_hltb = 0
    if "hltb_main" in df.columns:
        total_hltb = df["hltb_main"].sum(skipna=True)

    return {
        "total": total,
        "by_status": by_status,
        "by_platform": by_platform,
        "by_genre": by_genre,
        "avg_rating": round(avg_rating, 1),
        "rated_count": len(rated),
        "total_hltb_hours": round(float(total_hltb), 0) if total_hltb else None,
        "backlog_count": by_status.get("Backlog", 0),
        "completed_count": by_status.get("Completed", 0),
        "playing_count": by_status.get("Playing", 0),
    }


def df_to_context(df: pd.DataFrame, max_games: int = 80) -> str:
    """Converte la libreria in testo leggibile per il contesto AI."""
    lines = []
    sample = df.head(max_games)
    for _, row in sample.iterrows():
        parts = [f"- {row['title']}"]
        if row.get("platform"): parts.append(f"({row['platform']})")
        if row.get("status"): parts.append(f"[{row['status']}]")
        if row.get("genre"): parts.append(f"Genre: {row['genre']}")
        if pd.notna(row.get("personal_rating")) and row.get("personal_rating") != "":
            parts.append(f"Voto: {row['personal_rating']}/10")
        if row.get("hltb_main") and pd.notna(row.get("hltb_main")):
            parts.append(f"~{row['hltb_main']:.0f}h")
        lines.append(" ".join(parts))
    return "\n".join(lines)
