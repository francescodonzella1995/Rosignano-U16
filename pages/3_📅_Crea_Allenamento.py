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
            edit_key = f"_edit_mode_training_{t['id']}"
            if st.button(
                "✖️ Annulla modifica" if st.session_state.get(edit_key) else "✏️ Modifica giocatori ed esercizi",
                key=f"toggle_edit_{t['id']}",
            ):
                st.session_state[edit_key] = not st.session_state.get(edit_key, False)
                st.rerun()

            if st.session_state.get(edit_key):
                st.markdown("**Modifica presenze**")
                current_att = {
                    r["player_id"]: r
                    for r in db.query_all(
                        "SELECT player_id, presente, motivo FROM training_attendance WHERE training_id=?",
                        [t["id"]],
                    )
                }
                edit_active_players = get_players(only_active=True)
                edit_active_ids = {p["id"] for p in edit_active_players}
                edit_extra_ids = set(current_att.keys()) - edit_active_ids
                edit_extra_players = []
                if edit_extra_ids:
                    ph_extra = ",".join("?" for _ in edit_extra_ids)
                    edit_extra_players = db.query_all(
                        f"SELECT * FROM players WHERE id IN ({ph_extra})", list(edit_extra_ids)
                    )
                edit_players_list = edit_active_players + edit_extra_players
                if edit_extra_players:
                    st.caption(
                        "Alcuni giocatori qui sotto non sono più nella rosa attiva, ma erano presenti/assenti "
                        "in questo allenamento: puoi comunque modificarne lo stato."
                    )

                edit_presenze: dict[int, bool] = {}
                edit_motivi: dict[int, str] = {}
                if not edit_players_list:
                    st.info("Nessun giocatore disponibile.")
                else:
                    n_cols_edit = 3
                    cols_edit = st.columns(n_cols_edit)
                    for i, p in enumerate(edit_players_list):
                        default_presente = current_att.get(p["id"], {}).get("presente", 1) == 1
                        with cols_edit[i % n_cols_edit]:
                            edit_presenze[p["id"]] = st.checkbox(
                                player_label(p),
                                value=default_presente,
                                key=f"edit_presente_{t['id']}_{p['id']}",
                            )
                            if not edit_presenze[p["id"]]:
                                default_motivo = current_att.get(p["id"], {}).get("motivo") or ""
                                edit_motivi[p["id"]] = st.text_input(
                                    f"Motivo assenza di {player_label(p)}",
                                    value=default_motivo,
                                    key=f"edit_motivo_{t['id']}_{p['id']}",
                                    placeholder="es. infortunio, scuola, permesso...",
                                    label_visibility="collapsed",
                                )

                st.markdown("**Modifica esercizi svolti**")
                current_ex_ids = {
                    r["exercise_id"]
                    for r in db.query_all(
                        "SELECT exercise_id FROM training_exercises WHERE training_id=?", [t["id"]]
                    )
                }
                categorie_edit = sorted(
                    {e["categoria"] for e in db.query_all("SELECT DISTINCT categoria FROM exercises")}
                )
                edit_filtro_cat = st.multiselect(
                    "Filtra esercizi per categoria",
                    categorie_edit,
                    default=[],
                    key=f"edit_filtro_cat_{t['id']}",
                )
                edit_ex_query = "SELECT id, categoria, nome FROM exercises"
                edit_ex_params: list = []
                if edit_filtro_cat:
                    ph_cat = ",".join("?" for _ in edit_filtro_cat)
                    edit_ex_query += f" WHERE categoria IN ({ph_cat})"
                    edit_ex_params.extend(edit_filtro_cat)
                edit_ex_query += " ORDER BY categoria, nome"
                edit_ex_disponibili = db.query_all(edit_ex_query, edit_ex_params)
                edit_ex_options = {f"[{e['categoria']}] {e['nome']}": e["id"] for e in edit_ex_disponibili}
                # assicura che gli esercizi già selezionati restino visibili anche se il filtro li esclude
                for ex_id in current_ex_ids:
                    if ex_id not in edit_ex_options.values():
                        ex_row = db.query_one("SELECT id, categoria, nome FROM exercises WHERE id=?", [ex_id])
                        if ex_row:
                            edit_ex_options[f"[{ex_row['categoria']}] {ex_row['nome']}"] = ex_row["id"]
                label_by_id = {v: k for k, v in edit_ex_options.items()}
                default_labels = [label_by_id[eid] for eid in current_ex_ids if eid in label_by_id]
                edit_esercizi_scelti = st.multiselect(
                    "Esercizi svolti",
                    list(edit_ex_options.keys()),
                    default=default_labels,
                    key=f"edit_esercizi_{t['id']}",
                )

                if st.button("💾 Salva modifiche allenamento", key=f"save_edit_{t['id']}", type="primary"):
                    db.execute("DELETE FROM training_attendance WHERE training_id=?", [t["id"]])
                    for pid, presente in edit_presenze.items():
                        motivo_pid = (edit_motivi.get(pid, "") or "").strip() if not presente else ""
                        db.execute(
                            "INSERT INTO training_attendance (training_id, player_id, presente, motivo) "
                            "VALUES (?, ?, ?, ?)",
                            [t["id"], pid, 1 if presente else 0, motivo_pid],
                        )
                    db.execute("DELETE FROM training_exercises WHERE training_id=?", [t["id"]])
                    for label in edit_esercizi_scelti:
                        ex_id = edit_ex_options[label]
                        db.execute(
                            "INSERT INTO training_exercises (training_id, exercise_id) VALUES (?, ?)",
                            [t["id"], ex_id],
                        )
                    st.session_state[edit_key] = False
                    st.success("Modifiche salvate.")
                    st.rerun()

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
