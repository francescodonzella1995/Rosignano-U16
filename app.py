"""
Home dell'app - Rosignano Tancredi Under 16.
"""
import streamlit as st

import db
from helpers import ensure_db_ready, get_team, get_players, apply_team_theme

st.set_page_config(page_title="Rosignano Tancredi U16", page_icon="⚽", layout="wide")

ensure_db_ready()

team = get_team()
apply_team_theme(team)
nome_squadra = team["nome_squadra"] if team and team.get("nome_squadra") else None

st.title(f"⚽ {nome_squadra or 'Gestione Squadra'}")
st.caption("App di gestione allenamenti, partite e rosa")

if not nome_squadra:
    st.warning(
        "Non hai ancora configurato la squadra. Vai alla pagina **Board Iniziale** "
        "dal menu a sinistra per impostare nome, colori e rosa giocatori."
    )

players = get_players()
n_esercizi = db.query_one("SELECT COUNT(*) AS c FROM exercises")["c"]
n_allenamenti = db.query_one("SELECT COUNT(*) AS c FROM trainings")["c"]
n_partite = db.query_one("SELECT COUNT(*) AS c FROM matches")["c"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Giocatori in rosa", len(players))
col2.metric("Esercizi nel Manuale", n_esercizi)
col3.metric("Allenamenti registrati", n_allenamenti)
col4.metric("Partite registrate", n_partite)

st.divider()

st.markdown(
    """
Usa il menu a sinistra per navigare tra le sezioni:

- **Board Iniziale**: nome squadra, colori, rosa giocatori
- **Eserciziario**: catalogo esercizi di allenamento
- **Board Allenamenti**: registro sedute svolte + statistiche
- **Board Partite**: storico partite
- **Board Rosa**: statistiche automatiche per giocatore
- **Backup**: esporta/importa i dati (copia di sicurezza)
"""
)

if team and (team.get("colore_primario") or team.get("colore_secondario")):
    st.divider()
    st.subheader("Colori sociali")
    c1, c2 = st.columns(2)
    if team.get("colore_primario"):
        with c1:
            st.color_picker("Colore primario", value=team["colore_primario"], disabled=True, key="home_primario")
    if team.get("colore_secondario"):
        with c2:
            st.color_picker("Colore secondario", value=team["colore_secondario"], disabled=True, key="home_secondario")

with st.sidebar:
    st.caption(f"Storage: {'Turso (cloud)' if db.is_using_turso() else 'SQLite locale (solo per test)'}")
