import json

# Basato sul PDF "Programma_Rosignano.pdf" (Under 16 - Programma Allenamento 2026-2027, 20 pagine).
# Una scheda per ciascuna delle 6 giornate + 2 schede di riferimento comuni (pre-attivazione e scheda forza),
# tutte in categoria "Pre-Preparazione".

SCHEDE = [
    dict(page=4, nome="Pre-Attivazione e Attivazione (comune a tutte le giornate)",
         obiettivo="Riscaldamento pre-allenamento comune a tutte le sedute",
         regole="Ogni allenamento prevede: 16/18' di pre-attivazione divisa in 3 parti (Core Stability; "
                "Mobilità articolare - anche/coxo-femorale, arti inferiori; Attivazione muscolare arti inferiori), "
                "poi Attivazione (5' corsa con aumento progressivo di velocità; 5' andature + allungo: andature sui 10m "
                "+ allungo 40/50m con decelerazione in 4/5m, ritorno alla partenza in 30''; esempio andature: skip, "
                "calciata, spostamento laterale, combinazioni). "
                "Esempio Core Stability: plank orizzontale su gomiti (da 4 a 2 appoggi), plank dx/sx + torsione, "
                "reverse plank (da 4 a 3 appoggi alzando 1 piede alternato) — 2 serie, 30'' esercizio, 10'' recupero tra gli esercizi. "
                "Esempio pre-attivazione muscolare arti inferiori: affondo frontale alternato, affondo laterale alternato, "
                "granchio con elastico alle caviglie, ponte ad 1 piede — 2 serie, 30'' esercizio, 10'' recupero."),
    dict(page=9, nome="Giovedì 20.08.26 - Metabolico",
         obiettivo="Metabolico (intermittente)",
         regole="Parte centrale: Intermittente, recupero 60/90'' tra i blocchi/serie. "
                "8' x 20-20'': 20'' veloci (100m) alternati a 20'' recupero attivo (25+25m). "
                "8' x 15-30'': 15'' veloci (75/80m) alternati a 30'' recupero attivo (stessa distanza). "
                "8' x 15-15'': 15'' veloci (80/85m) alternati a 15'' recupero passivo. "
                "6' x 10-20'': 10'' veloci (55m) alternati a 20'' recupero attivo (stessa distanza). "
                "Parte finale: 10' foam roller, 10' posture."),
    dict(page=11, nome="Venerdì 21.08.26 - Metabolico",
         obiettivo="Metabolico (intermittente a distanza)",
         regole="Parte centrale: Intermittente a distanza, recupero 60/90'' tra i blocchi/serie. "
                "6' x (20m-30m): percorri 20m veloci e torni alla partenza in corsa lenta, poi 30m, per un totale di 6'. "
                "6' x (15m-25m): percorri 15m veloci e torni alla partenza lento, poi 25m, per un totale di 6'. "
                "12 ripetizioni x 15-10'': 15'' veloci (80m) alternati a 10'' recupero passivo. "
                "10/12 ripetizioni x 15-25'': 15'' veloci (20+20m a navetta in 5+5'' + 40m sprint) alternati a 25'' recupero passivo. "
                "Parte finale: 10' foam roller, 10' posture."),
    dict(page=13, nome="Lunedì 24.08.26 - Forza/Neuromuscolare",
         obiettivo="Forza / Neuromuscolare (accelerazioni-decelerazioni-sprint + forza)",
         regole="Parte centrale: dopo l'attivazione, accelerazioni/decelerazioni/sprint, poi passare alla Scheda Forza. "
                "5 x 35m sprint senza frenata, recupero passivo variato: 30''-20''-10''-15''. "
                "6 x 25m sprint senza frenata, recupero passivo variato: 25''-15''-5''-15''. "
                "8 x 15m con frenata entro 2m, recupero passivo variato: 15''-10''-5''-5''-10''-15''-15''. "
                "Eseguire quindi la Scheda Forza. Parte finale: 10' foam roller, 10' posture."),
    dict(page=14, nome="Martedì 25.08.26 - Recupero",
         obiettivo="Allenamento di recupero con variazione di velocità",
         regole="Parte centrale: allenamento di recupero con corsa a variazione di velocità. "
                "6' x 45-15'': 15'' in allungo alternati a 45'' corsa a ritmo medio, recupero 60''. "
                "6' x 50-10'': 10'' in allungo alternati a 50'' corsa a ritmo medio, recupero 60''. "
                "6' x 40'' corsa a ritmo medio/lento - 15'' in allungo - 5'' sprint. "
                "Parte finale: 10' foam roller, 10' posture."),
    dict(page=15, nome="Giovedì 27.08.26 - Forza/Neuromuscolare",
         obiettivo="Forza / Neuromuscolare (accelerazioni-decelerazioni-cambi di direzione-sprint + forza)",
         regole="Parte centrale: dopo l'attivazione, accelerazioni, decelerazioni, cambi di senso e direzione e sprint, poi Scheda Forza. "
                "6 x 15+15m sprint a navetta (andata+ritorno), recupero passivo variato: 20''-15''-10''-15''. "
                "6 x 40m sprint senza frenata, recupero passivo variato: 35''-25''-15''-10''-15''. "
                "6 x 4 cambi di direzione a zig-zag sui 5m, recupero passivo variato: 15''-10''-5''-10''. "
                "6 x 25m sprint + decelero 4/5m + ri-accelero 20m, recupero passivo variato: 35''-25''-15''-10''-15''. "
                "Eseguire quindi la Scheda Forza. Parte finale: 10' foam roller, 10' posture."),
    dict(page=17, nome="Venerdì 28.08.26 - Metabolico",
         obiettivo="Metabolico (intermittente a distanza-tempo)",
         regole="Parte centrale: intermittente a distanza-tempo, recupero 60'' tra i blocchi. "
                "6' x (10m-20m): percorri 10m veloci e torni alla partenza lento, poi 20m, per un totale di 6'. "
                "10 ripetizioni x (10'' allungo + 5'' sprint - 20'' recupero): 50/55m in allungo + sprint sui 40m, alternati a 20'' recupero passivo. "
                "5' x 10-20'': 10'' veloci (25/27+25/27m a navetta) alternati a 20'' recupero passivo. "
                "5' x (10'' allungo + 5'' sprint - 20'' recupero): 50/55m in allungo + sprint sui 40m, alternati a 20'' recupero passivo. "
                "Parte finale: 10' foam roller, 10' posture."),
    dict(page=19, nome="Scheda Forza (riferimento)",
         obiettivo="Forza (lower body + upper body), da abbinare alle giornate di Forza/Neuromuscolare",
         regole="Da fare nei due giorni della settimana impostati, e se se ne sente il bisogno nei giorni di riposo. "
                "Lower body (con pesi a casa, cercare eventualmente tutorial): squat bulgaro 3x6 (entrambe le gambe); "
                "jump squat 3x10 senza peso; box jump (balzi su panca 40-45cm) 3x15; hip thrust 3x8; 4x40'' di burpees. "
                "Upper body: a seconda dei pesi disponibili (panca, rematore, trazioni, ecc.), altrimenti 4x10 flessioni + 4x25 crunch. "
                "Recupero: sempre 1' tra le serie, 2' tra un esercizio e l'altro."),
]

out = []
for i, s in enumerate(SCHEDE, start=1):
    out.append({
        "id": i,
        "categoria": "Pre-Preparazione",
        "nome": s["nome"],
        "immagine": f"pre_preparazione/slide_{s['page']:02d}.jpg",
        "num_giocatori": "Tutta la squadra",
        "obiettivo": s["obiettivo"],
        "dimensioni_campo": "",
        "num_colori_casacche": "",
        "regole": s["regole"],
        "fonte": "Programma Rosignano - Under 16 2026-2027",
    })

with open("data/pre_preparazione_seed.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("Totale schede Pre-Preparazione:", len(out))
