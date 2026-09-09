"""
Storico Partite: elenco partite, distinte, eventi (gol/assist/cartellini/infortuni) e filtri.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import db
from helpers import (
    ensure_db_ready, get_players, get_team, player_label, confirm_action, apply_team_theme,
    TIPI_PARTITA, TIPI_EVENTO,
)
import streamlit as st

st.set_page_config(page_title="Storico Partite", page_icon="🏟️", layout="wide")
ensure_db_ready()
apply_team_theme(get_team())

st.title("🏟️ Storico Partite")

# ---------------------------------------------------------------------------
# Filtri storico
# ---------------------------------------------------------------------------
st.header("Storico partite")

all_players_for_filter = get_players(only_active=False)

fc1, fc2, fc3, fc4 = st.columns(4)
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
with fc4:
    filtro_tipo = st.selectbox(
        "Tipo partita",
        [None] + TIPI_PARTITA,
        format_func=lambda t: "-- tutti --" if t is None else t,
        key="filtro_tipo_partita",
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
if filtro_tipo:
    where.append("m.tipo_partita = ?")
    params.append(filtro_tipo)

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
    tipo_label = f" [{m['tipo_partita']}]" if m.get("tipo_partita") else ""
    label = f"{data_fmt} — vs {m['avversario']} ({m['casa_trasferta'] or '?'}){tipo_label} — {m['gol_fatti']}-{m['gol_subiti']}"
    with st.expander(label):
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Tipo:** {m.get('tipo_partita') or 'non indicato'}")
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

        st.markdown("---")
        edit_key_m = f"_edit_mode_match_{m['id']}"
        if st.button(
            "✖️ Annulla modifica" if st.session_state.get(edit_key_m) else "✏️ Modifica partita",
            key=f"toggle_edit_match_{m['id']}",
        ):
            st.session_state[edit_key_m] = not st.session_state.get(edit_key_m, False)
            st.rerun()

        if st.session_state.get(edit_key_m):
            st.markdown("**Modifica dati partita**")
            try:
                default_data_m = dt.date.fromisoformat(m["data"])
            except Exception:
                default_data_m = dt.date.today()
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                edit_data_m = st.date_input(
                    "Data", value=default_data_m, format="DD/MM/YYYY", key=f"edit_data_{m['id']}"
                )
                edit_tipo_m = st.selectbox(
                    "Tipo partita",
                    TIPI_PARTITA,
                    index=TIPI_PARTITA.index(m["tipo_partita"]) if m.get("tipo_partita") in TIPI_PARTITA else 0,
                    key=f"edit_tipo_{m['id']}",
                )
            with ec2:
                edit_avversario_m = st.text_input(
                    "Avversario", value=m["avversario"], key=f"edit_avversario_{m['id']}"
                )
                edit_ct_m = st.selectbox(
                    "Casa / Trasferta",
                    ["Casa", "Trasferta"],
                    index=1 if m.get("casa_trasferta") == "Trasferta" else 0,
                    key=f"edit_ct_{m['id']}",
                )
            with ec3:
                edit_modulo_m = st.text_input("Modulo (es. 1-4-3-3)", value=m.get("modulo") or "", key=f"edit_modulo_{m['id']}")
                edit_durata_m = st.number_input(
                    "Durata (minuti)", min_value=0, max_value=200, step=5,
                    value=int(m.get("durata_minuti") or 0), key=f"edit_durata_{m['id']}",
                )
            egc1, egc2 = st.columns(2)
            with egc1:
                edit_gf_m = st.number_input(
                    "Gol fatti", min_value=0, step=1, value=int(m.get("gol_fatti") or 0), key=f"edit_gf_{m['id']}"
                )
            with egc2:
                edit_gs_m = st.number_input(
                    "Gol subiti", min_value=0, step=1, value=int(m.get("gol_subiti") or 0), key=f"edit_gs_{m['id']}"
                )

            st.markdown("**Modifica distinta** (aggiungi o togli giocatori convocati, titolarità e minuti)")
            edit_active_players_m = get_players(only_active=True)
            edit_active_ids_m = {p["id"] for p in edit_active_players_m}
            current_lineup_ids_m = {r["player_id"] for r in lineup}
            edit_extra_ids_m = current_lineup_ids_m - edit_active_ids_m
            edit_extra_players_m = []
            if edit_extra_ids_m:
                ph_m = ",".join("?" for _ in edit_extra_ids_m)
                edit_extra_players_m = db.query_all(
                    f"SELECT * FROM players WHERE id IN ({ph_m})", list(edit_extra_ids_m)
                )
            edit_players_list_m = edit_active_players_m + edit_extra_players_m
            if edit_extra_players_m:
                st.caption(
                    "Alcuni giocatori qui sotto non sono più nella rosa attiva, ma erano convocati per questa "
                    "partita: puoi comunque modificarne lo stato."
                )
            lineup_by_pid = {r["player_id"]: r for r in lineup}
            if not edit_players_list_m:
                st.info("Nessun giocatore disponibile.")
                edit_distinta_m = None
            else:
                df_edit_distinta = pd.DataFrame(
                    {
                        "player_id": [p["id"] for p in edit_players_list_m],
                        "Giocatore": [player_label(p) for p in edit_players_list_m],
                        "Convocato": [p["id"] in lineup_by_pid for p in edit_players_list_m],
                        "Titolare": [bool(lineup_by_pid.get(p["id"], {}).get("titolare", 0)) for p in edit_players_list_m],
                        "Minuto ingresso": [lineup_by_pid.get(p["id"], {}).get("minuto_ingresso") for p in edit_players_list_m],
                        "Minuto uscita": [lineup_by_pid.get(p["id"], {}).get("minuto_uscita") for p in edit_players_list_m],
                        "Ruolo in campo": [lineup_by_pid.get(p["id"], {}).get("ruolo_in_campo") or "" for p in edit_players_list_m],
                    }
                )
                edit_distinta_m = st.data_editor(
                    df_edit_distinta,
                    width="stretch",
                    num_rows="fixed",
                    disabled=["player_id", "Giocatore"],
                    hide_index=True,
                    column_order=["Giocatore", "Convocato", "Titolare", "Minuto ingresso", "Minuto uscita", "Ruolo in campo"],
                    column_config={
                        "Minuto ingresso": st.column_config.NumberColumn(min_value=0, max_value=200),
                        "Minuto uscita": st.column_config.NumberColumn(min_value=0, max_value=200),
                    },
                    key=f"edit_distinta_editor_{m['id']}",
                )

            st.caption(
                "Per modificare o aggiungere gol, assist, cartellini o infortuni usa la sezione "
                "\"Eventi\" qui sopra: qui puoi cambiare solo i dati generali e i convocati."
            )

            if st.button("💾 Salva modifiche partita", key=f"save_edit_match_{m['id']}", type="primary"):
                db.execute(
                    """UPDATE matches SET data=?, avversario=?, casa_trasferta=?, modulo=?, durata_minuti=?,
                       gol_fatti=?, gol_subiti=?, tipo_partita=? WHERE id=?""",
                    [
                        edit_data_m.isoformat(), edit_avversario_m.strip(), edit_ct_m, edit_modulo_m.strip(),
                        int(edit_durata_m), int(edit_gf_m), int(edit_gs_m), edit_tipo_m, m["id"],
                    ],
                )
                if edit_distinta_m is not None:
                    db.execute("DELETE FROM match_lineup WHERE match_id=?", [m["id"]])
                    for _, row in edit_distinta_m.iterrows():
                        if not row["Convocato"]:
                            continue
                        minuto_ingresso = row["Minuto ingresso"]
                        minuto_uscita = row["Minuto uscita"]
                        db.execute(
                            """INSERT INTO match_lineup
                               (match_id, player_id, titolare, minuto_ingresso, minuto_uscita, ruolo_in_campo)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            [
                                m["id"],
                                int(row["player_id"]),
                                1 if row["Titolare"] else 0,
                                int(minuto_ingresso) if pd.notna(minuto_ingresso) else None,
                                int(minuto_uscita) if pd.notna(minuto_uscita) else None,
                                row["Ruolo in campo"],
                            ],
                        )
                st.session_state[edit_key_m] = False
                st.success("Modifiche salvate.")
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
