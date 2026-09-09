"""
Funzioni di utilità condivise da tutte le pagine dell'app Streamlit.
"""
from __future__ import annotations

import base64
import os

import streamlit as st

import db

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
SEED_FILES = [
    os.path.join(PROJECT_DIR, "data", "manuale_seed.json"),
    os.path.join(PROJECT_DIR, "data", "pre_preparazione_seed.json"),
]

# Tipologie di partita e di evento, condivise tra Inserisci Dati e Storico Partite.
TIPI_PARTITA = ["Campionato", "Amichevole", "Torneo"]
TIPI_EVENTO = ["Gol", "Assist", "Ammonizione", "Espulsione", "Infortunio"]


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


def exercise_image_source(ex: dict):
    """Restituisce l'immagine di un esercizio pronta per st.image():

    - se è stata caricata/sostituita manualmente, i byte sono salvati nel
      database (colonna immagine_dati) e vengono decodificati qui, così
      l'immagine resta disponibile anche dopo un redeploy dell'app;
    - altrimenti, se l'esercizio usa un'immagine di base inclusa nel
      progetto, viene usato il file su disco (immagine_path);
    - restituisce None se non c'è nessuna immagine.
    """
    dati = ex.get("immagine_dati") if isinstance(ex, dict) else None
    if dati:
        try:
            return base64.b64decode(dati)
        except Exception:
            return None
    return asset_path(ex.get("immagine_path"))


def encode_uploaded_image(uploaded_file) -> tuple[str, str]:
    """Codifica un file immagine caricato con st.file_uploader in base64,
    pronto per essere salvato nella colonna immagine_dati del database.

    Restituisce (dati_base64, mime_type).
    """
    raw = uploaded_file.getvalue()
    mime = uploaded_file.type or "image/jpeg"
    return base64.b64encode(raw).decode("ascii"), mime


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(v))):02x}" for v in rgb)


def darken_hex(hex_color: str, factor: float = 0.82) -> str:
    """Restituisce lo stesso colore reso più scuro (factor < 1 = più scuro).
    Se il colore non è un esadecimale valido, lo restituisce invariato."""
    try:
        r, g, b = _hex_to_rgb(hex_color)
    except Exception:
        return hex_color
    return _rgb_to_hex((r * factor, g * factor, b * factor))


def _contrast_text_color(hex_color: str) -> str:
    """Sceglie testo bianco o nero a seconda di quanto è chiaro/scuro il colore di sfondo,
    per mantenere il testo leggibile qualunque colore sociale venga scelto."""
    try:
        r, g, b = _hex_to_rgb(hex_color)
    except Exception:
        return "#000000"
    luminanza = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#000000" if luminanza > 0.55 else "#ffffff"


def apply_team_theme(team: dict | None) -> None:
    """Applica i colori sociali della squadra (impostati in Board Iniziale) come
    tema dell'app:
    - sfondo della parte centrale = colore primario
    - sfondo della barra laterale = colore secondario
    - caselle di testo: sfondo colore primario più scuro, bordo colore secondario
    Il colore del testo viene scelto automaticamente (bianco o nero) in base
    alla luminosità dello sfondo, per restare sempre leggibile.
    Non fa nulla se i colori non sono ancora stati impostati.
    """
    if not team:
        return
    primario = (team.get("colore_primario") or "").strip()
    secondario = (team.get("colore_secondario") or "").strip()
    if not primario and not secondario:
        return
    primario = primario or "#0e1117"
    secondario = secondario or "#262730"
    try:
        sfondo_caselle = darken_hex(primario, 0.82)
        testo_centrale = _contrast_text_color(primario)
        testo_laterale = _contrast_text_color(secondario)
        testo_caselle = _contrast_text_color(sfondo_caselle)
    except Exception:
        return
    st.markdown(
        f"""
        <style>
        [data-testid="stMain"] {{
            background-color: {primario};
        }}
        [data-testid="stMain"],
        [data-testid="stMain"] p,
        [data-testid="stMain"] span,
        [data-testid="stMain"] label {{
            color: {testo_centrale};
        }}
        [data-testid="stSidebar"] {{
            background-color: {secondario};
        }}
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label {{
            color: {testo_laterale};
        }}
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stNumberInput"] input {{
            background-color: {sfondo_caselle};
            border: 1px solid {secondario};
            color: {testo_caselle};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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
