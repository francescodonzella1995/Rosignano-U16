"""
Board Rosa: statistiche automatiche per giocatore (presenze, minuti, gol, assist,
cartellini, presenze/assenze allenamento, infortuni) + note libere.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

import db
from helpers import ensure_db_ready, get_players, get_team, player_label, confirm_action, apply_team_theme

st.set_page_config(page_title="Board Rosa", page_icon="📊", layout="wide")
ensure_db_ready()
apply_team_theme(get_team())

st.title("📊 Board Rosa")


def compute_player_stats(player_id: int) -> dict:
    lineup_rows = db.query_all(
        """SELECT ml.titolare, ml.minuto_ingresso, ml.minuto_uscita, m.durata_minuti
           FROM match_lineup ml JOIN matches m ON m.id = ml.match_id
           WHERE ml.player_id = ?""",
        [player_id],
    )
    presenze = 0
    titolarita = 0
    minuti_totali = 0
    for r in lineup_rows:
        giocato = False
        if r["titolare"]:
            titolarita += 1
            giocato = True
            fine = r["minuto_uscita"] if r["minuto_uscita"] is not None else r["durata_minuti"]
            if fine:
                minuti_totali += fine
        elif r["minuto_ingresso"] is not None:
            giocato = True
            fine = r["minuto_uscita"] if r["minuto_uscita"] is not None else r["durata_minuti"]
            if fine and fine > r["minuto_ingresso"]:
                minuti_totali += fine - r["minuto_ingresso"]
        if giocato:
            presenze += 1

    eventi = db.query_all(
        "SELECT tipo, COUNT(*) AS c FROM match_events WHERE player_id = ? GROUP BY tipo", [player_id]
    )
    conteggio_eventi = {e["tipo"]: e["c"] for e in eventi}

    all_train = db.query_one(
        "SELECT COUNT(*) AS c FROM training_attendance WHERE player_id = ? AND presente = 1", [player_id]
    )["c"]
    all_assenti = db.query_one(
        "SELECT COUNT(*) AS c FROM training_attendance WHERE player_id = ? AND presente = 0", [player_id]
    )["c"]
    tot_train = all_train + all_assenti
    perc_train = round(all_train / tot_train * 100, 1) if tot_train > 0 else None

    return {
        "presenze": presenze,
        "titolarita": titolarita,
        "minuti_totali": minuti_totali,
        "gol": conteggio_eventi.get("Gol", 0),
        "assist": conteggio_eventi.get("Assist", 0),
        "ammonizioni": conteggio_eventi.get("Ammonizione", 0),
        "espulsioni": conteggio_eventi.get("Espulsione", 0),
        "infortuni_in_partita": conteggio_eventi.get("Infortunio", 0),
        "allenamenti_presenti": all_train,
        "allenamenti_assenti": all_assenti,
        "perc_presenza_allenamenti": perc_train,
    }


TIPO_EVENTO_TO_CAMPO = {
    "Gol": "gol",
    "Assist": "assist",
    "Ammonizione": "ammonizioni",
    "Espulsione": "espulsioni",
    "Infortunio": "infortuni_in_partita",
}


def compute_all_stats(player_ids: list[int]) -> dict[int, dict]:
    """Come compute_player_stats, ma per più giocatori insieme con un numero
    fisso di query (3 in totale) invece di ripeterle per ognuno.

    Con una rosa numerosa, calcolare le statistiche un giocatore alla volta
    significa fare 4 query al database per ciascuno: su un database remoto
    come Turso, ogni query è un giro di rete, quindi la pagina impiega
    diversi secondi a comparire (sembrando "vuota" nel frattempo). Qui invece
    si scaricano tutte le righe una sola volta e si smistano in Python.
    """
    stats: dict[int, dict] = {
        pid: {
            "presenze": 0, "titolarita": 0, "minuti_totali": 0,
            "gol": 0, "assist": 0, "ammonizioni": 0, "espulsioni": 0, "infortuni_in_partita": 0,
            "allenamenti_presenti": 0, "allenamenti_assenti": 0, "perc_presenza_allenamenti": None,
        }
        for pid in player_ids
    }
    if not player_ids:
        return stats

    lineup_rows = db.query_all(
        """SELECT ml.player_id, ml.titolare, ml.minuto_ingresso, ml.minuto_uscita, m.durata_minuti
           FROM match_lineup ml JOIN matches m ON m.id = ml.match_id"""
    )
    for r in lineup_rows:
        s = stats.get(r["player_id"])
        if s is None:
            continue
        giocato = False
        if r["titolare"]:
            s["titolarita"] += 1
            giocato = True
            fine = r["minuto_uscita"] if r["minuto_uscita"] is not None else r["durata_minuti"]
            if fine:
                s["minuti_totali"] += fine
        elif r["minuto_ingresso"] is not None:
            giocato = True
            fine = r["minuto_uscita"] if r["minuto_uscita"] is not None else r["durata_minuti"]
            if fine and fine > r["minuto_ingresso"]:
                s["minuti_totali"] += fine - r["minuto_ingresso"]
        if giocato:
            s["presenze"] += 1

    eventi_rows = db.query_all(
        "SELECT player_id, tipo, COUNT(*) AS c FROM match_events WHERE player_id IS NOT NULL GROUP BY player_id, tipo"
    )
    for r in eventi_rows:
        s = stats.get(r["player_id"])
        campo = TIPO_EVENTO_TO_CAMPO.get(r["tipo"])
        if s is not None and campo is not None:
            s[campo] = r["c"]

    att_rows = db.query_all(
        "SELECT player_id, presente, COUNT(*) AS c FROM training_attendance GROUP BY player_id, presente"
    )
    for r in att_rows:
        s = stats.get(r["player_id"])
        if s is None:
            continue
        if r["presente"]:
            s["allenamenti_presenti"] = r["c"]
        else:
            s["allenamenti_assenti"] = r["c"]

    for s in stats.values():
        tot = s["allenamenti_presenti"] + s["allenamenti_assenti"]
        s["perc_presenza_allenamenti"] = round(s["allenamenti_presenti"] / tot * 100, 1) if tot > 0 else None

    return stats


# ---------------------------------------------------------------------------
# 1) Panoramica rosa
# ---------------------------------------------------------------------------
st.header("Panoramica rosa")

mostra_inattivi_rosa = st.checkbox("Includi giocatori disattivati", value=False, key="rosa_mostra_inattivi")
players = get_players(only_active=not mostra_inattivi_rosa)

if not players:
    st.info("Nessun giocatore in rosa. Vai alla Board Iniziale per aggiungerli.")
else:
    with st.spinner("Calcolo statistiche della rosa..."):
        all_stats = compute_all_stats([p["id"] for p in players])
        rows = []
        for p in players:
            s = all_stats[p["id"]]
            rows.append(
                {
                    "Giocatore": player_label(p),
                    "Ruolo": p.get("ruolo") or "",
                    "Presenze partite": s["presenze"],
                    "Titolarità": s["titolarita"],
                    "Minuti giocati": s["minuti_totali"],
                    "Gol": s["gol"],
                    "Assist": s["assist"],
                    "Ammonizioni": s["ammonizioni"],
                    "Espulsioni": s["espulsioni"],
                    "All. presenti": s["allenamenti_presenti"],
                    "All. assenti": s["allenamenti_assenti"],
                    "% presenza all.": s["perc_presenza_allenamenti"],
                }
            )
        df_overview = pd.DataFrame(rows)
    st.dataframe(df_overview, width="stretch", hide_index=True)

st.divider()

# ---------------------------------------------------------------------------
# 2) Dettaglio giocatore
# ---------------------------------------------------------------------------
st.header("Dettaglio giocatore")

all_players_full = get_players(only_active=False)
if not all_players_full:
    st.stop()

sel = st.selectbox(
    "Seleziona giocatore",
    all_players_full,
    format_func=lambda p: f"{player_label(p)} {'(disattivato)' if not p['attivo'] else ''}",
    key="rosa_player_select",
)

if sel:
    stats = compute_player_stats(sel["id"])
    st.subheader(player_label(sel))
    info_cols = st.columns(4)
    info_cols[0].write(f"**Ruolo:** {sel.get('ruolo') or 'non indicato'}")
    info_cols[1].write(f"**Numero:** {sel.get('numero_maglia') or 'non indicato'}")
    info_cols[2].write(f"**Data di nascita:** {sel.get('data_nascita') or 'non indicata'}")
    info_cols[3].write(f"**Stato:** {'Attivo' if sel['attivo'] else 'Disattivato'}")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Presenze partite", stats["presenze"])
    m2.metric("Titolarità", stats["titolarita"])
    m3.metric("Minuti giocati", stats["minuti_totali"])
    m4.metric(
        "% presenza allenamenti",
        f"{stats['perc_presenza_allenamenti']}%" if stats["perc_presenza_allenamenti"] is not None else "n/d",
    )

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("Gol", stats["gol"])
    m6.metric("Assist", stats["assist"])
    m7.metric("Ammonizioni", stats["ammonizioni"])
    m8.metric("Espulsioni", stats["espulsioni"])

    st.caption(
        f"Allenamenti: {stats['allenamenti_presenti']} presenze, {stats['allenamenti_assenti']} assenze"
        + (f" — infortuni segnalati durante le partite: {stats['infortuni_in_partita']}" if stats["infortuni_in_partita"] else "")
    )

    st.markdown("---")

    # ---------------- Infortuni ----------------
    st.subheader("Infortuni")
    infortuni = db.query_all(
        "SELECT * FROM injuries WHERE player_id = ? ORDER BY data_inizio DESC", [sel["id"]]
    )
    if infortuni:
        for inf in infortuni:
            colinf1, colinf2 = st.columns([5, 1])
            with colinf1:
                periodo = f"dal {inf['data_inizio']}"
                if inf["data_fine_prevista"]:
                    periodo += f" al {inf['data_fine_prevista']} (previsto)"
                st.write(f"- **{periodo}**: {inf['descrizione'] or 'nessuna descrizione'}"
                         + (f" — {inf['note']}" if inf["note"] else ""))
            with colinf2:
                if st.button("Elimina", key=f"del_inf_{inf['id']}"):
                    db.execute("DELETE FROM injuries WHERE id = ?", [inf["id"]])
                    st.rerun()
    else:
        st.caption("Nessun infortunio registrato.")

    with st.form(f"form_add_injury_{sel['id']}", clear_on_submit=True):
        ic1, ic2, ic3 = st.columns(3)
        with ic1:
            inf_inizio = st.date_input("Data inizio infortunio", value=dt.date.today(), format="DD/MM/YYYY")
        with ic2:
            ha_fine_prevista = st.checkbox("Ha una data di fine prevista")
            inf_fine = st.date_input("Data fine prevista", value=dt.date.today(), format="DD/MM/YYYY", disabled=not ha_fine_prevista)
        with ic3:
            inf_desc = st.text_input("Descrizione")
        inf_note = st.text_area("Note", height=60)
        add_inf = st.form_submit_button("Aggiungi infortunio")
    if add_inf:
        db.execute(
            "INSERT INTO injuries (player_id, data_inizio, data_fine_prevista, descrizione, note) VALUES (?, ?, ?, ?, ?)",
            [sel["id"], inf_inizio.isoformat(), inf_fine.isoformat() if ha_fine_prevista else None, inf_desc.strip(), inf_note.strip()],
        )
        st.success("Infortunio registrato.")
        st.rerun()

    st.markdown("---")

    # ---------------- Note libere ----------------
    st.subheader("Note")
    note = db.query_all("SELECT * FROM player_notes WHERE player_id = ? ORDER BY data DESC", [sel["id"]])
    if note:
        for n in note:
            coln1, coln2 = st.columns([5, 1])
            with coln1:
                st.write(f"- **{n['data']}**: {n['testo']}")
            with coln2:
                if st.button("Elimina", key=f"del_note_{n['id']}"):
                    db.execute("DELETE FROM player_notes WHERE id = ?", [n["id"]])
                    st.rerun()
    else:
        st.caption("Nessuna nota registrata.")

    with st.form(f"form_add_note_{sel['id']}", clear_on_submit=True):
        nota_data = st.date_input("Data nota", value=dt.date.today(), format="DD/MM/YYYY", key=f"nota_data_{sel['id']}")
        nota_testo = st.text_area("Nota", height=80, key=f"nota_testo_{sel['id']}")
        add_nota = st.form_submit_button("Aggiungi nota")
    if add_nota:
        if nota_testo.strip():
            db.execute(
                "INSERT INTO player_notes (player_id, data, testo) VALUES (?, ?, ?)",
                [sel["id"], nota_data.isoformat(), nota_testo.strip()],
            )
            st.success("Nota aggiunta.")
            st.rerun()
        else:
            st.error("Scrivi qualcosa nella nota prima di salvare.")
