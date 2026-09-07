import json

# Ogni voce corrisponde a una slide del PDF "Esercizi_Esordienti.pdf" (60 pagine totali).
# page = numero di pagina del PDF (1-indexed) -> file assets/manuale/slide_{page:02d}.png
# Le pagine di copertina e di intestazione categoria (stemma) NON generano un esercizio.

ESERCIZI = [
    # ---------------- ATTIVAZIONI TECNICHE (pag. 3-14) ----------------
    dict(page=3, categoria="Attivazione Tecnica", nome="Rombo Base",
         num_giocatori="5", obiettivo="Controllo orientato; smarcamento; conduzione; passaggio piatto",
         dimensioni_campo="12mt lato",
         regole="Progressioni: Uno-due (1-2-1-2->3-2-3->4-3-4); Terzo uomo (1-2-1-3->2-4->3-5). "
                "Variante: 6 ragazzi 2 palloni. Variante 2: pentagono 6 ragazzi."),
    dict(page=4, categoria="Attivazione Tecnica", nome="Quadrato - Vertice Interno",
         num_giocatori="7", obiettivo="Controllo orientato; smarcamento; gioco su vertice; sponda",
         dimensioni_campo="25x15",
         regole="Spostamento: 1->2->3->4->5->6->7. Progressioni: uno-due nei passaggi da 1 a 3, da 3 a 2, da 5 a 6, da 6 a 7."),
    dict(page=5, categoria="Attivazione Tecnica", nome="Quadrato - Giocata Esterna",
         num_giocatori="6", obiettivo="Controllo orientato; smarcamento; gioco a muro; 2 palloni",
         dimensioni_campo="25x15",
         regole="Spostamento a tempo. Primo pallone: 1-2-3-1-6-5-4-6-1. Secondo pallone: 5-6-4-5-2-1-3-2-5."),
    dict(page=6, categoria="Attivazione Tecnica", nome="Gioco Sui Triangoli",
         num_giocatori="7", obiettivo="Gioco/muovo; gioco su vertice",
         dimensioni_campo="18mt lato",
         regole="Primo pallone: 1-2-3-1-4-5-2-4-6-3-5-6-7. Spostamento: 1->4->6->7, a tempo tra triangolo interno ed esterno (1 a giro resta fuori)."),
    dict(page=7, categoria="Attivazione Tecnica", nome="Gioco E Mi Muovo",
         num_giocatori="6", obiettivo="Gioco/muovo; gioco su vertice; spazio interno",
         dimensioni_campo="15mt lato",
         regole="Prima parte: 1-2-1-3-2-4, spostamento 1->2->3->4. Seconda parte: 4-2-4-5-2-6, spostamento 4->2->5->6. "
                "A fine giro: 1->5 / 2->3 / 3->4 / 4->2 / 5->6."),
    dict(page=8, categoria="Attivazione Tecnica", nome="Rettangolo - Play Mobile",
         num_giocatori="8", obiettivo="Gioco/muovo; play mobili; spazio interno; due palloni",
         dimensioni_campo="20x15mt",
         regole="Primo pallone: 1-2-3-2-4-8. Secondo pallone: 5-6-4-6-3-7. Spostamento: 1->2/2->3/3->7  e  5->6/6->4/4->8."),
    dict(page=9, categoria="Attivazione Tecnica", nome="Gioco e Mi Muovo (variante)",
         num_giocatori="5", obiettivo="Gioco/muovo; occupo spazio; attivo mente; cerco cono libero",
         dimensioni_campo="20x12mt",
         regole=""),
    dict(page=10, categoria="Attivazione Tecnica", nome="Uomo/Solo",
         num_giocatori="6", obiettivo="Gioco/muovo; parlare; gioco in catena; profondità",
         dimensioni_campo="20x15mt",
         regole='Esempio 1: 1-2-"solo!"-3-4-"uomo!"-3-2-gol. Esempio 2: 1-2-"solo!"-3-4-"solo!"-gol. '
                'Esempio 3: 1-2-"uomo!"-1-finché non solo poi prosegue. '
                'Spostamento: chi segna va dietro la porta, chi sta dietro porta inizia azione, chi ha fatto sponda (4) va sulla fascia libera. '
                'Se segna 4 va lui dietro porta e si scambia con chi sta dietro porta, fine.'),
    dict(page=11, categoria="Attivazione Tecnica", nome="Circuito Terzo Uomo",
         num_giocatori="10", obiettivo="Gioco/muovo; 3° uomo; palla avanti/dietro; 2 palloni",
         dimensioni_campo="20x15mt",
         regole="Primo pallone: 1-2-3-2-4-3-5. Secondo pallone: 6-7-8-7-9-8-10. Spostamento: 1->2->3->4->5 e 6->7->8->9->10."),
    dict(page=12, categoria="Attivazione Tecnica", nome="Lavoro su Doppio Play",
         num_giocatori="6", obiettivo="Gioco/muovo; movimenti 2 play; posture",
         dimensioni_campo="15x15mt",
         regole="6 e 5 trovano spazi per ricevere e fare sponda, 3 la può ripassare a 5 e 6 o può girare. Spostamento: a tempo entrano altri 2."),
    dict(page=13, categoria="Attivazione Tecnica", nome="Lavoro su Rombo",
         num_giocatori="5", obiettivo="Gioco/muovo; terzo uomo; posture",
         dimensioni_campo="20x20mt",
         regole="Rotazione: 1-2-1-3-4 (a destra: 1-2-1-3-2-4, volendo scambio 4-3-4 per ripartire). Spostamento: 1->2 / 2->3 / 3->4, 4 riparte."),
    dict(page=14, categoria="Attivazione Tecnica", nome="Seguire la Pressione",
         num_giocatori="10", obiettivo="Dietro la pressione; smarcamento; precisione passaggio",
         dimensioni_campo="20x30",
         regole="Pallone: 1-2-3-4-6-5-7-8. Spostamento: 1-2->3-4 / 3-4->5-6 / 5-6->7-8 / 7-8 fuori / 9-10->1-2."),

    # ---------------- ATTIVAZIONI LUDICHE (pag. 16-21) ----------------
    dict(page=16, categoria="Attivazione Ludica", nome="Tre Stazioni - Precisione (1)",
         num_giocatori="A squadre", obiettivo="Tecnica; divertimento",
         dimensioni_campo="Metà campo",
         regole="Rotazione 1-2/2-3/3-4. Stazione 1 (scambio per bocce, 2 tocchi al bocciatore). "
                "Stazione 2 (crossbar challenge: 1pt di testa o al volo su respinta, 2pt). "
                "Stazione 3 (slalom e scambio, palla alzata sponda e gol al volo)."),
    dict(page=17, categoria="Attivazione Ludica", nome="Tre Stazioni - Precisione (2)",
         num_giocatori="A squadre", obiettivo="Tecnica; divertimento; colpo di testa; dominio",
         dimensioni_campo="Metà campo",
         regole="Rotazione 1-2/2-3/3-4. Stazione ostacoli: colpo di testa per ridare palla a 2, 2 la rende e tiro al volo per gol nelle porte "
                "(spostamento: 3 recupera palla e va all'infila, 2 va al posto di 3, 1 va al posto di 2). "
                "Stazione palleggi al volo: palla rasoterra per cross, gol sopra nastro. "
                "Stazione palleggio di gruppo per fare canestro: tutti la devono toccare, se cade si riparte."),
    dict(page=18, categoria="Attivazione Ludica", nome="Partite a Tema con le Mani",
         num_giocatori="A squadre", obiettivo="Attivazione neurale; divertimento; colpo di testa; gioco di squadra",
         dimensioni_campo="20x25 (tempi 3x4)",
         regole="Serie 1: gioco e mi muovo. Serie 2: palla avanti palla indietro. Serie 3: gioco e mi sovrappongo. "
                "Serie 4: tocco avversario cambio possesso. Rotazione 1-2/2-3/3-4."),
    dict(page=19, categoria="Attivazione Ludica", nome="Sfida - Conduzione",
         num_giocatori="A squadre", obiettivo="Attivazione fisica; dominio palla",
         dimensioni_campo="Area",
         regole="Conduzione palla con cinesino in mano da mettere nel paletto nel fare il giro."),
    dict(page=20, categoria="Attivazione Ludica", nome="Colpi di Testa",
         num_giocatori="A squadre", obiettivo="Colpo di testa; divertimento; motoria in porta",
         dimensioni_campo="Area",
         regole="Rotazione 1-2/2-3/3-4. Parte 1 rosso in porta, 1 blu gira intorno e colpisce di testa su palla di mano di 2, poi va in porta. "
                "Parte 2 rosso gira e colpisce di testa su palla di mano di 3, poi va in porta, ecc. Rotazione: 1->porta / 2->1 / porta->fila."),
    dict(page=21, categoria="Attivazione Ludica", nome="Circuito Precisione",
         num_giocatori="A squadre, minimo 6", obiettivo="Dominio e tiro in porta; sfida; lancio lungo",
         dimensioni_campo="Metà campo",
         regole="Rotazione 1-2-3-4-5->6->1. 1 e 2 fanno 3 scambi volanti, slalom e spola, cross per 3 (1pt gol). "
                "3 prende palla, scambia con 4 e gol di precisione in cortina (1pt). 5 recupera palla e lancia: se nel quadrato di cinesini e stoppata, 1pt. "
                "Dopo il tiro di 3 partono i blu."),

    # ---------------- RONDOS/POSSESSI (pag. 23-40) ----------------
    dict(page=23, categoria="Rondo/Possesso", nome='Rondo "Guardiola"',
         num_giocatori="11", obiettivo="Controllo orientato; riaggressione; postura; 4 appoggi",
         dimensioni_campo="20x12",
         regole="4v4+3 jolly: su recupero i rossi devono uscire dal rettangolo, i blu riaggrediscono. "
                "Variante: porte sui lati lunghi, su recupero palla si può segnare dopo sponda dei jolly esterni."),
    dict(page=24, categoria="Rondo/Possesso", nome="Rondo per 6/7",
         num_giocatori="6/7", obiettivo="Controllo orientato; postura; 4 appoggi",
         dimensioni_campo="12x12",
         regole="Metodo di uscita 1 o 2. Variante: se in 6 manca il giocatore interno."),
    dict(page=25, categoria="Rondo/Possesso", nome="Rondo per 8/9",
         num_giocatori="8/9", obiettivo="Controllo orientato; postura; 4 appoggi; spaziature del 3+2",
         dimensioni_campo="12 lato",
         regole="Metodo di uscita 1, 2 o 3. Variante: se in 8 manca il giocatore interno."),
    dict(page=26, categoria="Rondo/Possesso", nome="Rondo per 10",
         num_giocatori="10", obiettivo="Controllo orientato; postura; 4 appoggi",
         dimensioni_campo="12 lato",
         regole="Metodo di uscita 1, 2 o 3."),
    dict(page=27, categoria="Rondo/Possesso", nome="Rondo per 10 Posizionale (a)",
         num_giocatori="10", obiettivo="Controllo orientato; postura; 4 appoggi",
         dimensioni_campo="20x15",
         regole="Jolly rimangono come sostegno e vertice."),
    dict(page=28, categoria="Rondo/Possesso", nome="Rondo per 10 Posizionale (b)",
         num_giocatori="10", obiettivo="Controllo orientato; postura; 4 appoggi; riaggressione",
         dimensioni_campo="16x16 (5x5 dentro)",
         regole="Quando i rossi recuperano giocano fuori sugli altri 4 rossi: 6 passaggi = 1 gol. Se i blu recuperano e segnano in una porta = 1 gol. "
                "Ogni 2-3 giri cambiano i 2 rossi dentro. Possono farlo in contemporanea 2 gruppi da 20 (uno 4-6 rossi, uno 4-6 blu)."),
    dict(page=29, categoria="Rondo/Possesso", nome="Possesso per Filtrante / Smarcamento ai Fianchi",
         num_giocatori="15", obiettivo="Riaggressione; gioco sotto pressione; 4 appoggi; ricerca uomo ai fianchi",
         dimensioni_campo="30x15",
         regole="Rossi fanno rondo 5v2 con i blu che entrano dalla zona di mezzo. Dopo 5 passaggi cercano i gialli con filtrante centrale, "
                "o con palla diagonale verso due gialli apertisi ai fianchi. Se passa, i gialli rientrano e fanno un altro 5v2 contro altri 2 blu. "
                "Se recuperata nel rondo, gol nelle portine (1pt). A tempo chi fa più gol vince (3' a gruppo). "
                "Variante: senza porte e non a tempo, su recupero palla i blu servono i gialli e sono i rossi a dover recuperare palla, 4 serie da 3'."),
    dict(page=30, categoria="Rondo/Possesso", nome="Rondo a Cerchio-Gara",
         num_giocatori="8", obiettivo="Gioco con sponde; 4 appoggi; trova spazio libero",
         dimensioni_campo="15mt diametro",
         regole="10 palle per i blu, 10 per i rossi; 2v2+4 jolly. Gol valido solo dopo 5 passaggi e assist sponda (no gol jolly). "
                "Dopo i 10 palloni, 10 palle per i verdi e 10 per i gialli."),
    dict(page=31, categoria="Rondo/Possesso", nome="Rondo a Esagono-Gara",
         num_giocatori="9", obiettivo="Intercetto; riaggressione; gioco per dentro",
         dimensioni_campo="12mt lato",
         regole="6v3 a 3 squadre (Gialli+Blu vs Rossi). Cambio a tempo. Gol su recupero palla. Si contano i gol."),
    dict(page=32, categoria="Rondo/Possesso", nome="Possesso e Riaggressione",
         num_giocatori="14", obiettivo="Possesso sotto pressione; riaggressione",
         dimensioni_campo="30x22",
         regole="Possesso 8v6: se i rossi fanno 5 passaggi = 1pt. Se i blu recuperano diventa possesso 6v4 (5 passaggi = 1pt). "
                "Se i rossi recuperano nuovamente, 5 passaggi = 1pt contro riaggressione."),
    dict(page=33, categoria="Rondo/Possesso", nome="Rondo Forza",
         num_giocatori="12+", obiettivo="Velocità; forza",
         dimensioni_campo="12 lato / 8 lato",
         regole="Rondo rossi centrali vs 2 blu. Su recupero palla ogni blu va in un rondo 4v1 (i rossi laterali si spostano), su recupero palla va al tiro. "
                "Sfida a coppie, si contano i gol di ogni coppia (min 3 giri a coppia poi cambio)."),
    dict(page=34, categoria="Rondo/Possesso", nome="Rondo Posizionale 3+2+3",
         num_giocatori="12", obiettivo="Possesso sotto pressione; riaggressione; posizionamento 3+2",
         dimensioni_campo="24x16",
         regole="Possesso 8v4 (rossi+gialli vs blu), posizionamenti 3-2-3 di chi è in possesso. "
                "Se chi è in possesso fa 10 passaggi = 1 gol. Se i blu recuperano con gol nella portina = 1 gol. Cambio a tempo, vince chi segna più gol."),
    dict(page=35, categoria="Rondo/Possesso", nome="Rondo Mobile 5v2",
         num_giocatori="12/16", obiettivo="Possesso sotto pressione; riaggressione; posizionamento 3+2",
         dimensioni_campo="30x15",
         regole="Rondo gialli + jolly interno + 2 jolly esterni vs 2 blu. Dopo 6 passaggi può arrivare ai rossi (blu ok intercetto), "
                "se arriva ai 2 blu entrano e stesso rondo. Ogni recupero = 1pt. Cambio a tempo, vince chi fa più recuperi (cambiano anche i jolly). "
                "Variante: senza jolly (o solo 2 portieri come jolly esterno), rondo 4v2."),
    dict(page=36, categoria="Rondo/Possesso", nome="Rondo Bidirezionale 8",
         num_giocatori="8/9", obiettivo="Riconosco sostegno e vertice; mantenimento possesso; trasmissione",
         dimensioni_campo="12x12",
         regole="Rondo 5v3 contando i jolly; se una squadra va da un jolly all'altro e ritorno fa 1pt. "
                "Variante: si può fare in 9 aggiungendo un jolly al centro (e ruotando anche le 3 squadre)."),
    dict(page=37, categoria="Rondo/Possesso", nome="Rondo Bidirezionale 11",
         num_giocatori="8/9", obiettivo="Lavoro su posture; ricerca uomo libero; posizionamento e trasmissione; ricerca 4 appoggi",
         dimensioni_campo="12x20",
         regole="Rondo 5+jolly vs 5 con i ruoli, sfruttare superiorità. 6 passaggi = 1pt. "
                "Variante: con portieri, dopo 6 passaggi possibile andare al tiro in una porta (dal lato degli attaccanti)."),
    dict(page=38, categoria="Rondo/Possesso", nome="Rondo Mobile con Smarcamento",
         num_giocatori="10", obiettivo="Avanzamento per superiorità; ricerca uomo libero",
         dimensioni_campo="27x15",
         regole="Rondo 5v3 usando il sostegno come jolly: dopo 3 passaggi ci si può smarcare oltre la metà, o filtrante o conduzione. "
                "Se i blu recuperano vanno subito dalla parte opposta e iniziano il rondo. 1 punto ogni volta che si va da un jolly all'altro. "
                "Variante: con portieri come jolly, dopo la filtrante e dopo 3 passaggi 1c1 di chi riceve vs l'avversario nel quadrato e tiro per gol."),
    dict(page=39, categoria="Rondo/Possesso", nome="Gioco Posizionale 3+2",
         num_giocatori="10", obiettivo="Riconoscere superiorità; ricerca uomo libero",
         dimensioni_campo="27x15",
         regole="Costruzione 3+2+2 che inizia in rondo 5v2 (dif + 2 med + 1 trq + 1 att vs 2); dopo 3 passaggi si può segnare nelle portine "
                "(n9 no, solo sponda). Le ali possono entrare per creare un 5v4 lasciando liberi i terzini; se il terzino riceve può segnare subito. "
                "Se i rossi recuperano vanno per il gol."),
    dict(page=40, categoria="Rondo/Possesso", nome="Possesso con Sponde Posizionale",
         num_giocatori="12+P / 15+P", obiettivo="Riconoscere superiorità; utilizzo sponde; riaggressione; transizioni",
         dimensioni_campo="30x30",
         regole="Possesso 4v4 con una sponda per lato + jolly per superiorità (8v4). Una sponda è il portiere. 10 passaggi = 1pt. "
                "Su recupero palla i rossi possono attaccare la porta. Dopo 3' cambio squadre jolly compresi. "
                "Variante: possesso 5v5 con una sponda per lato + jolly per superiorità (10v5)."),

    # ---------------- ESERCITAZIONI CENTRALI (pag. 42-59) ----------------
    dict(page=42, categoria="Esercitazione Centrale", nome="Esercizio per Conduzione",
         num_giocatori="14", obiettivo="Riconoscere superiorità; conduzione",
         dimensioni_campo="35x20",
         regole="1v1+J nel primo settore, conduzione per superiorità numerica e 5v4 nel 2° settore per arrivare nel 3° a meta -> ogni meta 1pt. "
                "Variante: aggiungere 5-10mt, porte e portieri, sempre 1v1+J+P (3v1) e si va a tiri. "
                "Variante 2: nei primi settori 3v2 (tot 16 ragazzi) senza jolly e 3v3 dentro."),
    dict(page=43, categoria="Esercitazione Centrale", nome="Esercizio per Conduzione / Diagonalità",
         num_giocatori="16", obiettivo="Giocata diagonale; conduzione; riconoscere superiorità",
         dimensioni_campo="40x20",
         regole="2v2+j: si passa nel settore con conduzione o giocata a muro per 3° uomo per fare 4v3, no lungolinea, obbligo diagonale. Meta = 1pt. "
                "Variante: con porte e portieri."),
    dict(page=44, categoria="Esercitazione Centrale", nome="Messa in Campo con Jolly e Risalita",
         num_giocatori="18", obiettivo="Messa in campo; conduzione; riconoscere superiorità",
         dimensioni_campo="55x40",
         regole="Squadre schierate uguali (5 son DC, 2 son DC, J è DC, ecc). Per risalire il campo conduzione o 3° uomo, punto con meta. "
                "Se viene recuperata palla nei primi 2 settori si riparte dal 1° settore."),
    dict(page=45, categoria="Esercitazione Centrale", nome="Possesso con Meta",
         num_giocatori="14->18", obiettivo="Ricerca profondità; riconoscere superiorità",
         dimensioni_campo="37x50 + 10 meta",
         regole="7v7+1/2 jolly, punto con filtrante in zona meta (6 serie da 3' con 1' recupero, tot 24'). Variante: 8v8+J / 8v8 / 6v6+2J. "
                "Jolly: se centrocampista, superiorità a centrocampo; se terzino, superiorità dietro + inferiorità in transizione."),
    dict(page=46, categoria="Esercitazione Centrale", nome="Possesso con Jolly Esterni",
         num_giocatori="14->18", obiettivo="Ricerca palla esterna; riconoscere superiorità",
         dimensioni_campo="37x50 + 10 meta",
         regole="Punto se si va da portiere a portiere e ritorno. Si passa zona con conduzione o filtrante. I jolly non possono condurre in zona 3. "
                "Variante: inserire le porte e partita. Jolly: se centrocampista superiorità a centrocampo; se terzino superiorità dietro + inferiorità in transizione."),
    dict(page=47, categoria="Esercitazione Centrale", nome="Esercitazione Filtranti",
         num_giocatori="9+2P", obiettivo="Filtrante; copertura linea; transizione",
         dimensioni_campo="32x25",
         regole="2v1, ricerco filtrante per punta: se passa, 2 centrocampisti si girano e 3v2; se non passa, transizione 3 centrocampisti + attaccante vs 2."),
    dict(page=48, categoria="Esercitazione Centrale", nome="Esercitazione Filtranti 2",
         num_giocatori="14+2P", obiettivo="Filtrante; copertura linea; transizione; controllo orientato/palla aperta",
         dimensioni_campo="40x25",
         regole="3 giocano per filtrante: se passa, controllo orientato e 4v3 per il gol; se non passa, 3v4 in transizione. "
                "Variante: i 4 superati possono rientrare. Alternativa: inserire punta davanti e attacco in 5v3."),
    dict(page=49, categoria="Esercitazione Centrale", nome="Costruzioni in Superiorità Numerica",
         num_giocatori="9+P", obiettivo="Riconoscere uomo libero; giocare sotto pressione; trovare palla aperta",
         dimensioni_campo="50x60",
         regole="5+P vs 4 (o 3 per iniziare) -> gol nelle portine per punto. I rossi, su recupero, fanno transizione per punto."),
    dict(page=50, categoria="Esercitazione Centrale", nome="Costruzioni in Superiorità Numerica con Trequartista",
         num_giocatori="12+P", obiettivo="Riconoscere uomo libero; giocare sotto pressione; trovare palla aperta; movimenti trequartista",
         dimensioni_campo="50x60",
         regole="5+P vs 4 (o 3 per iniziare) -> gol nelle portine per punto o trovando un trequartista nei box rossi. "
                "Il n.6 rosso può solo schermare i 2 trequartisti; i trequartisti possono uscire dai box, ma in quel caso il 6 può seguirli."),
    dict(page=51, categoria="Esercitazione Centrale", nome="Costruzione per Dentro",
         num_giocatori="9+P", obiettivo="Riconoscere uomo libero; giocare sotto pressione; trovare palla aperta; tenere palla dentro",
         dimensioni_campo="50x60",
         regole="5+P vs 4 (o 3 per iniziare) -> gol nelle portine per punto. Rossi: recupero e transizione per punto, via linee esterne per giocare dentro."),
    dict(page=52, categoria="Esercitazione Centrale", nome="Costruzione Simil-Gara",
         num_giocatori="14+2P", obiettivo="Riconoscere uomo libero; giocare sotto pressione; trovare palla aperta; tenere palla dentro",
         dimensioni_campo="50x60",
         regole="7+J vs 6 in costruzione: se i rossi recuperano diventa un 7v7. Jolly centrocampista per superiorità dentro, oppure libero dove vuole (es. trequartista)."),
    dict(page=53, categoria="Esercitazione Centrale", nome="Sviluppi Offensivi",
         num_giocatori="12+P (10+P)", obiettivo="Trovare spazi tra le linee; soluzioni attacco linea; palla aperta/chiusa; preventive",
         dimensioni_campo="50x60",
         regole="Rondo 4v2: dopo 5 passaggi i blu possono attaccare 5v3. Se i rossi recuperano, gol nelle porte. "
                "Variante: 2c2 e non 3c3 per forzare fuorilinea e tagli. Rotazione a 16/17: cambio 2/3 attaccanti e 2 difensori ogni 2 turni."),
    dict(page=54, categoria="Esercitazione Centrale", nome="Sviluppi Offensivi per 1c1 Esterno",
         num_giocatori="12+P", obiettivo="Forzare 1c1 esterni; soluzioni su cross; palla aperta/chiusa; preventive",
         dimensioni_campo="50x60",
         regole="Rondo 4v2: dopo 5 passaggi i blu trovano le ali sull'esterno, il rosso può entrare dopo l'1c1 e riempimento area. "
                "Rotazione a 16/17: cambio 2/3 attaccanti e 2 difensori ogni 2 turni."),
    dict(page=55, categoria="Esercitazione Centrale", nome="Sviluppi Catena Laterale",
         num_giocatori="13/14+P", obiettivo="Forzare 1c1 esterni; soluzioni su cross; palla aperta/chiusa; preventive",
         dimensioni_campo="50x60",
         regole="Rondo 5v2 (o 5v3): dopo 5 passaggi ricerca palla esterna e il terzino sovrappone sull'1c1. Rotazione a 16/17: cambio 2/3 attaccanti."),
    dict(page=56, categoria="Esercitazione Centrale", nome="Sviluppi per Zona Rifinitura",
         num_giocatori="13+P (14+2P)", obiettivo="Ricerca uomo tra le linee; controllo orientato/postura; palla aperta/chiusa; tagli",
         dimensioni_campo="50x60",
         regole="Rondo 4v2: dopo 5 passaggi ricerca filtrante e 4v3 in attacco. Variante: rondo 4v3 + portiere per trovare imbucata fin da subito per i trequartisti. "
                "Rotazione a 16/17: cambio 2/3 attaccanti."),
    dict(page=57, categoria="Esercitazione Centrale", nome="Costruzioni per Gioco su Vertice",
         num_giocatori="15+2P", obiettivo="Ricerca uomo libero; ricerca vertice per sponda",
         dimensioni_campo="50x60",
         regole="Costruzione in +1 (+portiere) o anche +2 all'inizio. Ricerca vertice per sponda e tiro. Rotazione a 16/17: cambio centrocampista attaccante."),
    dict(page=58, categoria="Esercitazione Centrale", nome="Sviluppo Palla Aperta/Chiusa",
         num_giocatori="8+P", obiettivo="Palla aperta/chiusa; smarcamento e attacco alla porta",
         dimensioni_campo="32x40",
         regole="Il 5 scambia con il jolly. Se dice solo jolly si gira e gioca 4v3. Se dice uomo, il jolly la rende a 5 e lo attacca: diventa 4v4."),
    dict(page=59, categoria="Esercitazione Centrale", nome="Esercitazione Difesa",
         num_giocatori="8+P", obiettivo="Analitico e coperture porta; copertura su palla laterale",
         dimensioni_campo="32x40",
         regole="Prima passaggio analitico. Poi conduzione e palla chiusa/aperta. Coperture su ricezione di schiena. "
                "Difesa della porta su palla laterale. 3v5 in fase difensiva."),
    dict(page=60, categoria="Esercitazione Centrale", nome="Schieramento (da completare)",
         num_giocatori="", obiettivo="", dimensioni_campo="",
         regole="Slide senza titolo/testo nel PDF originale: schieramento 11 vs 11 nei pressi dell'area. Compilare i dettagli mancanti."),
]

out = []
for i, e in enumerate(ESERCIZI, start=1):
    out.append({
        "id": i,
        "categoria": e["categoria"],
        "nome": e["nome"],
        "immagine": f"manuale/slide_{e['page']:02d}.jpg",
        "num_giocatori": e["num_giocatori"],
        "obiettivo": e["obiettivo"],
        "dimensioni_campo": e["dimensioni_campo"],
        "num_colori_casacche": "",
        "regole": e["regole"],
        "fonte": "Keynote: Esercizi Esordienti",
    })

with open("data/manuale_seed.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("Totale esercizi Manuale:", len(out))
