"""
Inserisci Dati: registrazione di un nuovo allenamento oppure di una nuova partita,
a seconda della scelta fatta con il selettore qui sotto.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

import db
from helpers import ensure_db_ready, get_players, get_team, player_label, apply_team_theme, TIPI_PARTITA

st.set_page_config(page_title="Inserisci Dati", page_icon="📝", layout="wide")
ensure_db_ready()
apply_team_theme(get_team())

st.title("📝 Inserisci Dati")

tipo_inserimento = st.radio(
    "Cosa vuoi registrare?", ["Allenamento", "Partita"], horizontal=True, key="inserisci_dati_tipo"
)
st.divider()

# =============================================================================
# ALLENAMENTO
# =============================================================================
if tipo_inserimento == "Allenamento":
    st.header("Registra nuovo allenamento")

    players = get_players(only_active=True)

    # NB: questa sezione non usa st.form perché il campo "motivo assenza" deve
    # comparire subito, appena si deseleziona un giocatore — con un form i
    # widget non si aggiornano finché non si preme il pulsante di invio finale.
    c1, c2, c3 = st.columns(3)
    with c1:
        data_all = st.date_input("Data", value=dt.date.today(), format="DD/MM/YYYY", key="new_training_data")
    with c2:
        ora_all = st.time_input("Ora", value=dt.time(18, 0), key="new_training_ora")
    with c3:
        durata_all = st.number_input(
            "Durata (minuti)", min_value=0, max_value=300, step=5, value=0, key="new_training_durata"
        )

    st.markdown("**Presenze** (tutti selezionati come presenti di default, deseleziona gli assenti e indica il motivo)")
    presenze: dict[int, bool] = {}
    motivi: dict[int, str] = {}
    if not players:
        st.info("Nessun giocatore in rosa. Vai alla Board Iniziale per aggiungerli.")
    else:
        n_cols = 3
        cols = st.columns(n_cols)
        for i, p in enumerate(players):
            with cols[i % n_cols]:
                presenze[p["id"]] = st.checkbox(player_label(p), value=True, key=f"presente_{p['id']}")
                if not presenze[p["id"]]:
                    motivi[p["id"]] = st.text_input(
                        f"Motivo assenza di {player_label(p)}",
                        key=f"motivo_{p['id']}",
                        placeholder="es. infortunio, scuola, permesso...",
                        label_visibility="collapsed",
                    )

    st.markdown("**Esercizi svolti**")
    categorie_disponibili = sorted({e["categoria"] for e in db.query_all("SELECT DISTINCT categoria FROM exercises")})
    filtro_cat = st.multiselect(
        "Filtra esercizi per categoria", categorie_disponibili, default=[], key="new_training_filtro_cat"
    )

    ex_query = "SELECT id, categoria, nome FROM exercises"
    ex_params: list = []
    if filtro_cat:
        placeholders = ",".join("?" for _ in filtro_cat)
        ex_query += f" WHERE categoria IN ({placeholders})"
        ex_params.extend(filtro_cat)
    ex_query += " ORDER BY categoria, nome"
    esercizi_disponibili = db.query_all(ex_query, ex_params)
    ex_options = {f"[{e['categoria']}] {e['nome']}": e["id"] for e in esercizi_disponibili}
    esercizi_scelti_label = st.multiselect(
        "Seleziona esercizi svolti", list(ex_options.keys()), key="new_training_esercizi"
    )

    note_all = st.text_area("Note (facoltativo)", height=70, key="new_training_note")

    submitted_training = st.button("Salva allenamento", type="primary", key="submit_new_training")

    if submitted_training:
        if not players:
            st.error("Non ci sono giocatori in rosa: aggiungili prima nella Board Iniziale.")
        else:
            new_id = db.insert_and_get_id(
                "INSERT INTO trainings (data, ora, durata_minuti, note) VALUES (?, ?, ?, ?)",
                [data_all.isoformat(), ora_all.strftime("%H:%M"), int(durata_all), note_all.strip()],
            )
            for pid, presente in presenze.items():
                motivo_pid = (motivi.get(pid, "") or "").strip() if not presente else ""
                db.execute(
                    "INSERT INTO training_attendance (training_id, player_id, presente, motivo) VALUES (?, ?, ?, ?)",
                    [new_id, pid, 1 if presente else 0, motivo_pid],
                )
            for label in esercizi_scelti_label:
                ex_id = ex_options[label]
                db.execute(
                    "INSERT INTO training_exercises (training_id, exercise_id) VALUES (?, ?)",
                    [new_id, ex_id],
                )
            st.success(f"Allenamento del {data_all.strftime('%d/%m/%Y')} registrato.")
            st.rerun()

# =============================================================================
# PARTITA
# =============================================================================
else:
    st.header("Registra nuova partita")

    players = get_players(only_active=True)

    with st.form("form_new_match"):
        c1, c2, c3 = st.columns(3)
        with c1:
            data_match = st.date_input("Data", value=dt.date.today(), format="DD/MM/YYYY")
            tipo_match = st.selectbox("Tipo partita", TIPI_PARTITA)
            avversario = st.text_input("Avversario")
        with c2:
            casa_trasferta = st.selectbox("Casa / Trasferta", ["Casa", "Trasferta"])
            modulo = st.text_input("Modulo (es. 1-4-3-3)")
        with c3:
            durata_minuti = st.number_input("Durata (minuti)", min_value=0, max_value=200, step=5, value=0)
            gc1, gc2 = st.columns(2)
            with gc1:
                gol_fatti = st.number_input("Gol fatti", min_value=0, step=1, value=0)
            with gc2:
                gol_subiti = st.number_input("Gol subiti", min_value=0, step=1, value=0)

        st.markdown(
            "**Distinta**: seleziona i convocati, chi è titolare, i minuti di ingresso/uscita dei subentrati "
            "e, se vuoi, gol/assist/cartellini segnati durante la partita."
        )
        if not players:
            st.info("Nessun giocatore in rosa. Vai alla Board Iniziale per aggiungerli.")
            distinta_edited = None
        else:
            df_distinta = pd.DataFrame(
                {
                    "player_id": [p["id"] for p in players],
                    "Giocatore": [player_label(p) for p in players],
                    "Convocato": [True for _ in players],
                    "Titolare": [False for _ in players],
                    "Minuto ingresso": [None for _ in players],
                    "Minuto uscita": [None for _ in players],
                    "Ruolo in campo": ["" for _ in players],
                    "Gol": [0 for _ in players],
                    "Assist": [0 for _ in players],
                    "Ammonito": [False for _ in players],
                    "Espulso": [False for _ in players],
                }
            )
            distinta_edited = st.data_editor(
                df_distinta,
                width="stretch",
                num_rows="fixed",
                disabled=["player_id", "Giocatore"],
                hide_index=True,
                column_order=[
                    "Giocatore", "Convocato", "Titolare", "Minuto ingresso", "Minuto uscita", "Ruolo in campo",
                    "Gol", "Assist", "Ammonito", "Espulso",
                ],
                column_config={
                    "Minuto ingresso": st.column_config.NumberColumn(min_value=0, max_value=200),
                    "Minuto uscita": st.column_config.NumberColumn(min_value=0, max_value=200),
                    "Gol": st.column_config.NumberColumn(min_value=0, max_value=20, step=1),
                    "Assist": st.column_config.NumberColumn(min_value=0, max_value=20, step=1),
                },
                key="distinta_editor",
            )

        eventi_salienti = st.text_area("Eventi salienti (testo libero, facoltativo)", height=70)
        note_match = st.text_area("Note (facoltativo)", height=70)

        submitted_match = st.form_submit_button("Salva partita", type="primary")

    if submitted_match:
        if not avversario.strip():
            st.error("Inserisci il nome dell'avversario.")
        else:
            new_match_id = db.insert_and_get_id(
                """INSERT INTO matches
                   (data, avversario, casa_trasferta, modulo, durata_minuti, gol_fatti, gol_subiti, eventi_salienti, note, tipo_partita)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    data_match.isoformat(), avversario.strip(), casa_trasferta, modulo.strip(),
                    int(durata_minuti), int(gol_fatti), int(gol_subiti), eventi_salienti.strip(), note_match.strip(),
                    tipo_match,
                ],
            )
            if distinta_edited is not None:
                for _, row in distinta_edited.iterrows():
                    if not row["Convocato"]:
                        continue
                    minuto_ingresso = row["Minuto ingresso"]
                    minuto_uscita = row["Minuto uscita"]
                    db.execute(
                        """INSERT INTO match_lineup
                           (match_id, player_id, titolare, minuto_ingresso, minuto_uscita, ruolo_in_campo)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        [
                            new_match_id,
                            int(row["player_id"]),
                            1 if row["Titolare"] else 0,
                            int(minuto_ingresso) if pd.notna(minuto_ingresso) else None,
                            int(minuto_uscita) if pd.notna(minuto_uscita) else None,
                            row["Ruolo in campo"],
                        ],
                    )
                    pid = int(row["player_id"])
                    n_gol = int(row.get("Gol", 0) or 0)
                    n_assist = int(row.get("Assist", 0) or 0)
                    for _ in range(n_gol):
                        db.execute(
                            "INSERT INTO match_events (match_id, player_id, tipo, minuto, descrizione) VALUES (?, ?, ?, ?, ?)",
                            [new_match_id, pid, "Gol", None, ""],
                        )
                    for _ in range(n_assist):
                        db.execute(
                            "INSERT INTO match_events (match_id, player_id, tipo, minuto, descrizione) VALUES (?, ?, ?, ?, ?)",
                            [new_match_id, pid, "Assist", None, ""],
                        )
                    if row.get("Ammonito"):
                        db.execute(
                            "INSERT INTO match_events (match_id, player_id, tipo, minuto, descrizione) VALUES (?, ?, ?, ?, ?)",
                            [new_match_id, pid, "Ammonizione", None, ""],
                        )
                    if row.get("Espulso"):
                        db.execute(
                            "INSERT INTO match_events (match_id, player_id, tipo, minuto, descrizione) VALUES (?, ?, ?, ?, ?)",
                            [new_match_id, pid, "Espulsione", None, ""],
                        )
            st.success(f"Partita contro {avversario} registrata.")
            st.rerun()
