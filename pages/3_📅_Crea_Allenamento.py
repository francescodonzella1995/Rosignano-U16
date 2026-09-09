"""
Crea Allenamento: registro delle sedute svolte + statistiche/insight.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

import db
from helpers import ensure_db_ready, get_players, get_team, player_label, confirm_action, apply_team_theme
from pdf_export import build_training_pdf

st.set_page_config(page_title="Crea Allenamento", page_icon="📅", layout="wide")
ensure_db_ready()
apply_team_theme(get_team())

st.title("📅 Crea Allenamento")

GIORNI_IT = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

# ---------------------------------------------------------------------------
# 1) Registra nuovo allenamento
# ---------------------------------------------------------------------------
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

st.divider()

# ---------------------------------------------------------------------------
# 2) Storico allenamenti
# ---------------------------------------------------------------------------
st.header("Storico allenamenti")

trainings = db.query_all("SELECT * FROM trainings ORDER BY data DESC, ora DESC")

if not trainings:
    st.info("Nessun allenamento ancora registrato.")
else:
    for t in trainings:
        try:
            data_fmt = dt.date.fromisoformat(t["data"]).strftime("%d/%m/%Y")
        except Exception:
            data_fmt = t["data"]
        n_presenti = db.query_one(
            "SELECT COUNT(*) AS c FROM training_attendance WHERE training_id=? AND presente=1", [t["id"]]
        )["c"]
        n_assenti = db.query_one(
            "SELECT COUNT(*) AS c FROM training_attendance WHERE training_id=? AND presente=0", [t["id"]]
        )["c"]
        label = f"{data_fmt} {t['ora'] or ''} — {n_presenti} presenti, {n_assenti} assenti"
        with st.expander(label):
            st.write(f"**Durata:** {t['durata_minuti']} minuti" if t["durata_minuti"] else "**Durata:** non indicata")
            if t["note"]:
                st.write(f"**Note:** {t['note']}")

            assenti = db.query_all(
                """SELECT p.*, ta.motivo FROM training_attendance ta JOIN players p ON p.id = ta.player_id
                   WHERE ta.training_id = ? AND ta.presente = 0 ORDER BY p.cognome, p.nome""",
                [t["id"]],
            )
            if assenti:
                st.write("**Assenti:**")
                for a in assenti:
                    motivo_txt = f" — {a['motivo']}" if a.get("motivo") else " — motivo non indicato"
                    st.write(f"- {player_label(a)}{motivo_txt}")
            else:
                st.write("**Assenti:** nessuno")

            ex_used_full = db.query_all(
                """SELECT e.* FROM training_exercises te JOIN exercises e ON e.id = te.exercise_id
                   WHERE te.training_id = ? ORDER BY e.categoria, e.nome""",
                [t["id"]],
            )
            if ex_used_full:
                st.write("**Esercizi svolti:**")
                for e in ex_used_full:
                    st.write(f"- [{e['categoria']}] {e['nome']}")
            else:
                st.write("**Esercizi svolti:** nessuno registrato")

            st.markdown("---")
            pdf_key = f"_pdf_bytes_training_{t['id']}"
            if st.button("📄 Genera PDF allenamento", key=f"gen_pdf_{t['id']}"):
                team_pdf = get_team()
                assenti_per_pdf = [
                    {"nome_completo": player_label(a), "motivo": a.get("motivo")} for a in assenti
                ]
                st.session_state[pdf_key] = build_training_pdf(
                    team_pdf.get("nome_squadra") if team_pdf else None,
                    t,
                    assenti_per_pdf,
                    ex_used_full,
                )
            if st.session_state.get(pdf_key):
                st.download_button(
                    "⬇️ Scarica PDF",
                    data=st.session_state[pdf_key],
                    file_name=f"allenamento_{t['data']}.pdf",
                    mime="application/pdf",
                    key=f"download_pdf_{t['id']}",
                )

            confirm_action(
                key=f"delete_training_{t['id']}",
                button_label="🗑️ Elimina questo allenamento",
                warning_text=(
                    f"Stai per eliminare definitivamente l'allenamento del **{data_fmt}**, comprese le presenze/assenze "
                    "e gli esercizi svolti collegati. Questa azione non è reversibile. Confermi?"
                ),
                on_confirm=lambda tid=t["id"]: db.execute("DELETE FROM trainings WHERE id = ?", [tid]),
            )

st.divider()

# ---------------------------------------------------------------------------
# 3) Insight / statistiche
# ---------------------------------------------------------------------------
st.header("Statistiche")

if not trainings:
    st.info("Nessun dato ancora disponibile per le statistiche.")
else:
    periodo = st.radio(
        "Periodo",
        ["Settimana corrente", "Mese corrente", "Anno corrente", "Intervallo personalizzato"],
        horizontal=True,
    )

    today = dt.date.today()
    if periodo == "Settimana corrente":
        start = today - dt.timedelta(days=today.weekday())
        end = start + dt.timedelta(days=6)
    elif periodo == "Mese corrente":
        start = today.replace(day=1)
        next_month = (start.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        end = next_month - dt.timedelta(days=1)
    elif periodo == "Anno corrente":
        start = today.replace(month=1, day=1)
        end = today.replace(month=12, day=31)
    else:
        drange = st.date_input(
            "Seleziona intervallo", value=(today - dt.timedelta(days=30), today), format="DD/MM/YYYY"
        )
        if isinstance(drange, tuple) and len(drange) == 2:
            start, end = drange
        else:
            start, end = today - dt.timedelta(days=30), today

    st.caption(f"Periodo selezionato: {start.strftime('%d/%m/%Y')} — {end.strftime('%d/%m/%Y')}")

    trainings_periodo = [
        t for t in trainings if start.isoformat() <= t["data"] <= end.isoformat()
    ]

    st.metric("Allenamenti nel periodo", len(trainings_periodo))

    if trainings_periodo:
        ids = [t["id"] for t in trainings_periodo]
        placeholders = ",".join("?" for _ in ids)

        # Distribuzione per categoria (basata sugli utilizzi di esercizi nel periodo)
        cat_rows = db.query_all(
            f"""SELECT e.categoria AS categoria, COUNT(*) AS c
                FROM training_exercises te JOIN exercises e ON e.id = te.exercise_id
                WHERE te.training_id IN ({placeholders})
                GROUP BY e.categoria ORDER BY c DESC""",
            ids,
        )
        if cat_rows:
            df_cat = pd.DataFrame(cat_rows)
            df_cat["percentuale"] = (df_cat["c"] / df_cat["c"].sum() * 100).round(1)
            st.subheader("Distribuzione per categoria di esercizio")
            st.caption("Calcolata sul numero di volte che un esercizio di quella categoria è stato usato nel periodo.")
            st.bar_chart(df_cat.set_index("categoria")["c"])
            st.dataframe(
                df_cat.rename(columns={"categoria": "Categoria", "c": "Utilizzi", "percentuale": "% sul totale"}),
                width='stretch',
                hide_index=True,
            )
        else:
            st.info("Nessun esercizio registrato negli allenamenti del periodo.")

        # Esercizi più ripetuti
        top_ex = db.query_all(
            f"""SELECT e.nome AS nome, e.categoria AS categoria, COUNT(*) AS volte
                FROM training_exercises te JOIN exercises e ON e.id = te.exercise_id
                WHERE te.training_id IN ({placeholders})
                GROUP BY e.id ORDER BY volte DESC, e.nome LIMIT 15""",
            ids,
        )
        if top_ex:
            st.subheader("Esercizi più ripetuti nel periodo")
            st.dataframe(
                pd.DataFrame(top_ex).rename(columns={"nome": "Esercizio", "categoria": "Categoria", "volte": "Volte usato"}),
                width='stretch',
                hide_index=True,
            )

        # Distribuzione per giorno della settimana
        giorni_count = {g: 0 for g in GIORNI_IT}
        for t in trainings_periodo:
            wd = dt.date.fromisoformat(t["data"]).weekday()
            giorni_count[GIORNI_IT[wd]] += 1
        df_giorni = pd.DataFrame({"Giorno": GIORNI_IT, "Allenamenti": [giorni_count[g] for g in GIORNI_IT]})
        df_giorni["Giorno"] = pd.Categorical(df_giorni["Giorno"], categories=GIORNI_IT, ordered=True)
        df_giorni = df_giorni.sort_values("Giorno")
        st.subheader("Distribuzione per giorno della settimana")
        st.bar_chart(df_giorni.set_index("Giorno"))
    else:
        st.info("Nessun allenamento nel periodo selezionato.")
