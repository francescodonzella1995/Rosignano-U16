"""
Board Partite: storico partite, distinta, eventi (gol/assist/cartellini/infortuni) e filtri.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

import db
from helpers import ensure_db_ready, get_players, get_team, player_label, confirm_action, apply_team_theme

st.set_page_config(page_title="Board Partite", page_icon="🏟️", layout="wide")
ensure_db_ready()
apply_team_theme(get_team())

st.title("🏟️ Board Partite")

TIPI_EVENTO = ["Gol", "Assist", "Ammonizione", "Espulsione", "Infortunio"]

# ---------------------------------------------------------------------------
# 1) Registra nuova partita
# ---------------------------------------------------------------------------
st.header("Registra nuova partita")

players = get_players(only_active=True)

with st.form("form_new_match"):
    c1, c2, c3 = st.columns(3)
    with c1:
        data_match = st.date_input("Data", value=dt.date.today(), format="DD/MM/YYYY")
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

    st.markdown("**Distinta**: seleziona i convocati, chi è titolare e i minuti di ingresso/uscita dei subentrati.")
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
            }
        )
        distinta_edited = st.data_editor(
            df_distinta,
            width="stretch",
            num_rows="fixed",
            disabled=["player_id", "Giocatore"],
            hide_index=True,
            column_order=["Giocatore", "Convocato", "Titolare", "Minuto ingresso", "Minuto uscita", "Ruolo in campo"],
            column_config={
                "Minuto ingresso": st.column_config.NumberColumn(min_value=0, max_value=200),
                "Minuto uscita": st.column_config.NumberColumn(min_value=0, max_value=200),
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
               (data, avversario, casa_trasferta, modulo, durata_minuti, gol_fatti, gol_subiti, eventi_salienti, note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                data_match.isoformat(), avversario.strip(), casa_trasferta, modulo.strip(),
                int(durata_minuti), int(gol_fatti), int(gol_subiti), eventi_salienti.strip(), note_match.strip(),
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
        st.success(f"Partita contro {avversario} registrata.")
        st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# 2) Filtri storico
# ---------------------------------------------------------------------------
st.header("Storico partite")

all_players_for_filter = get_players(only_active=False)

fc1, fc2, fc3 = st.columns(3)
with fc1:
    filtro_avversario = st.text_input("Cerca per avversario")
with fc2:
    filtro_presenza = st.selectbox(
        "Solo partite giocate da",
        [None] + all_players_for_filter,
        format_func=lambda p: "-- tutti --" if p is None else player_label(p),
        key="filtro_presenza",
    )
with fc3:
    filtro_marcatore = st.selectbox(
        "Solo partite in cui ha segnato",
        [None] + all_players_for_filter,
        format_func=lambda p: "-- tutti --" if p is None else player_label(p),
        key="filtro_marcatore",
    )

query = "SELECT DISTINCT m.* FROM matches m"
joins = []
where = []
params: list = []
if filtro_presenza:
    joins.append("JOIN match_lineup ml_p ON ml_p.match_id = m.id AND ml_p.player_id = ?")
    params.append(filtro_presenza["id"])
if filtro_marcatore:
    joins.append("JOIN match_events me_g ON me_g.match_id = m.id AND me_g.player_id = ? AND me_g.tipo = 'Gol'")
    params.append(filtro_marcatore["id"])
if filtro_avversario.strip():
    where.append("LOWER(m.avversario) LIKE ?")
    params.append(f"%{filtro_avversario.strip().lower()}%")

full_query = query + (" " + " ".join(joins) if joins else "")
if where:
    full_query += " WHERE " + " AND ".join(where)
full_query += " ORDER BY m.data DESC"

matches = db.query_all(full_query, params)
st.caption(f"{len(matches)} partite trovate.")

for m in matches:
    try:
        data_fmt = dt.date.fromisoformat(m["data"]).strftime("%d/%m/%Y")
    except Exception:
        data_fmt = m["data"]
    label = f"{data_fmt} — vs {m['avversario']} ({m['casa_trasferta'] or '?'}) — {m['gol_fatti']}-{m['gol_subiti']}"
    with st.expander(label):
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Modulo:** {m['modulo'] or 'non indicato'}")
            st.write(f"**Durata:** {m['durata_minuti']} minuti" if m["durata_minuti"] else "**Durata:** non indicata")
        with c2:
            st.write(f"**Risultato:** {m['gol_fatti']} - {m['gol_subiti']}")
        if m["eventi_salienti"]:
            st.write(f"**Eventi salienti:** {m['eventi_salienti']}")
        if m["note"]:
            st.write(f"**Note:** {m['note']}")

        lineup = db.query_all(
            """SELECT ml.*, p.nome, p.cognome, p.numero_maglia FROM match_lineup ml
               JOIN players p ON p.id = ml.player_id WHERE ml.match_id = ?
               ORDER BY ml.titolare DESC, p.cognome, p.nome""",
            [m["id"]],
        )
        titolari = [r for r in lineup if r["titolare"]]
        subentrati = [r for r in lineup if not r["titolare"] and r["minuto_ingresso"] is not None]
        panchina = [r for r in lineup if not r["titolare"] and r["minuto_ingresso"] is None]

        st.markdown("**Titolari:** " + (", ".join(
            f"{player_label(r)}" + (f" (esce {r['minuto_uscita']}')" if r["minuto_uscita"] else "")
            for r in titolari
        ) or "nessuno indicato"))
        st.markdown("**Subentrati:** " + (", ".join(
            f"{player_label(r)} (entra {r['minuto_ingresso']}')" for r in subentrati
        ) or "nessuno"))
        st.markdown("**In panchina (non entrati):** " + (", ".join(player_label(r) for r in panchina) or "nessuno"))

        st.markdown("---")
        st.markdown("**Eventi (gol, assist, cartellini, infortuni)**")
        eventi = db.query_all(
            """SELECT me.*, p.nome, p.cognome FROM match_events me
               LEFT JOIN players p ON p.id = me.player_id WHERE me.match_id = ?
               ORDER BY me.minuto""",
            [m["id"]],
        )
        if eventi:
            for ev in eventi:
                chi = f"{ev['nome']} {ev['cognome']}" if ev.get("nome") else "?"
                minuto_str = f"{ev['minuto']}' " if ev["minuto"] is not None else ""
                desc = f" — {ev['descrizione']}" if ev["descrizione"] else ""
                colev1, colev2 = st.columns([5, 1])
                with colev1:
                    st.write(f"- {minuto_str}**{ev['tipo']}**: {chi}{desc}")
                with colev2:
                    if st.button("Elimina", key=f"del_event_{ev['id']}"):
                        db.execute("DELETE FROM match_events WHERE id = ?", [ev["id"]])
                        st.rerun()
        else:
            st.caption("Nessun evento registrato per questa partita.")

        with st.form(f"form_add_event_{m['id']}", clear_on_submit=True):
            ec1, ec2, ec3, ec4 = st.columns([2, 2, 1, 3])
            with ec1:
                if lineup:
                    giocatori_match = [
                        {"id": r["player_id"], "nome": r["nome"], "cognome": r["cognome"], "numero_maglia": r["numero_maglia"]}
                        for r in lineup
                    ]
                else:
                    giocatori_match = all_players_for_filter
                ev_player = st.selectbox(
                    "Giocatore", giocatori_match, format_func=lambda p: player_label(p), key=f"ev_player_{m['id']}"
                )
            with ec2:
                ev_tipo = st.selectbox("Tipo evento", TIPI_EVENTO, key=f"ev_tipo_{m['id']}")
            with ec3:
                ev_minuto = st.number_input("Minuto", min_value=0, max_value=200, step=1, value=0, key=f"ev_minuto_{m['id']}")
            with ec4:
                ev_desc = st.text_input("Descrizione (facoltativa)", key=f"ev_desc_{m['id']}")
            add_event = st.form_submit_button("Aggiungi evento")
        if add_event:
            db.execute(
                "INSERT INTO match_events (match_id, player_id, tipo, minuto, descrizione) VALUES (?, ?, ?, ?, ?)",
                [m["id"], ev_player["id"] if ev_player else None, ev_tipo, int(ev_minuto), ev_desc.strip()],
            )
            st.rerun()

        confirm_action(
            key=f"delete_match_{m['id']}",
            button_label="🗑️ Elimina questa partita",
            warning_text=(
                f"Stai per eliminare definitivamente la partita del **{data_fmt}** contro **{m['avversario']}**, "
                f"con tutta la distinta ({len(lineup)} giocatori) e gli eventi collegati ({len(eventi)}). "
                "Questa azione non è reversibile. Confermi?"
            ),
            on_confirm=lambda mid=m["id"]: db.execute("DELETE FROM matches WHERE id = ?", [mid]),
        )

if not matches:
    st.info("Nessuna partita corrisponde ai filtri selezionati.")
