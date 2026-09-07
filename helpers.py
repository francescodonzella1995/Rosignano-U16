"""
Funzioni di utilità condivise da tutte le pagine dell'app Streamlit.
"""
from __future__ import annotations

import os

import streamlit as st

import db

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
SEED_FILES = [
    os.path.join(PROJECT_DIR, "data", "manuale_seed.json"),
    os.path.join(PROJECT_DIR, "data", "pre_preparazione_seed.json"),
]


@st.cache_resource(show_spinner=False)
def ensure_db_ready() -> int:
    """Crea lo schema (se non esiste) e carica gli esercizi di base (solo se il catalogo è vuoto).

    Usa st.cache_resource per essere eseguita una sola volta per processo,
    non ad ogni rerun di ogni pagina.
    """
    db.init_db()
    return db.seed_exercises_if_empty(SEED_FILES)


def asset_path(immagine_path: str | None) -> str | None:
    """Percorso assoluto di un'immagine esercizio dato il path relativo salvato in DB
    (es. 'manuale/slide_03.png' o 'pre_preparazione/slide_09.png')."""
    if not immagine_path:
        return None
    full = os.path.join(ASSETS_DIR, immagine_path)
    return full if os.path.exists(full) else None


def get_team() -> dict | None:
    return db.query_one("SELECT * FROM team WHERE id = 1")


def get_players(only_active: bool = True) -> list[dict]:
    if only_active:
        return db.query_all("SELECT * FROM players WHERE attivo = 1 ORDER BY cognome, nome")
    return db.query_all("SELECT * FROM players ORDER BY cognome, nome")


def player_label(p: dict) -> str:
    numero = f" #{p['numero_maglia']}" if p.get("numero_maglia") not in (None, "") else ""
    return f"{p['cognome']} {p['nome']}{numero}"


def confirm_action(key: str, button_label: str, warning_text: str, on_confirm, button_type: str = "secondary") -> None:
    """Pattern di conferma a due passaggi per azioni distruttive
    (eliminare, sovrascrivere, rinominare dati): primo click mostra un
    avviso con cosa cambierà, il secondo click esegue davvero l'azione.
    """
    pending_key = f"_confirm_pending_{key}"
    if st.session_state.get(pending_key):
        st.warning(warning_text)
        c1, c2 = st.columns(2)
        if c1.button("✅ Sì, conferma", key=f"_confirm_yes_{key}", type="primary"):
            on_confirm()
            st.session_state[pending_key] = False
            st.rerun()
        if c2.button("Annulla", key=f"_confirm_no_{key}"):
            st.session_state[pending_key] = False
            st.rerun()
    else:
        if st.button(button_label, key=f"_confirm_btn_{key}", type=button_type):
            st.session_state[pending_key] = True
            st.rerun()
