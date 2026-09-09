"""
Storico Partite: elenco partite, distinte, eventi (gol/assist/cartellini/infortuni) e filtri.
"""
from __future__ import annotations

import datetime as dt

import db
from helpers import ensure_db_ready, get_players, get_team, player_label, confirm_action, apply_team_theme
import streamlit as st

st.set_page_config(page_title="Storico Partite", page_icon="🏟️", layout="wide")
ensure_db_ready()
apply_team_theme(get_team())

st.title("🏟️ Storico Partite")

TIPI_EVENTO = ["Gol", "Assist", "Ammonizione", "Espulsione", "Infortunio"]

# ---------------------------------------------------------------------------
# Filtri storico
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
