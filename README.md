# App Gestione Rosignano Tancredi - Under 16

App Streamlit per catalogare allenamenti, esercizi, partite e statistiche della rosa.

## Struttura del progetto

```
project/
├── app.py                          # Home dell'app
├── db.py                           # Accesso al database (Turso o SQLite locale)
├── helpers.py                      # Funzioni condivise dalle pagine
├── requirements.txt                # Librerie Python richieste
├── pages/
│   ├── 1_🏠_Board_Iniziale.py           # Squadra, colori, rosa (import Excel + manuale)
│   ├── 2_📘_Eserciziario.py             # Catalogo esercizi di allenamento
│   ├── 3_📝_Inserisci_Dati.py           # Registra un nuovo allenamento o una nuova partita
│   ├── 4_📅_Storico_Allenamenti.py      # Sedute svolte, modifica, export PDF + statistiche
│   ├── 5_🏟️_Storico_Partite.py          # Storico partite, distinte, eventi/marcatori
│   ├── 6_📊_Board_Rosa.py               # Statistiche automatiche per giocatore
│   └── 7_💾_Backup.py                   # Esporta/importa una copia di sicurezza dei dati
├── assets/
│   ├── manuale/                    # Immagini degli esercizi (dal Keynote esportato in PDF)
│   └── pre_preparazione/           # Immagini delle schede di pre-preparazione
├── data/
│   ├── manuale_seed.json           # Dati iniziali del Manuale (55 esercizi)
│   └── pre_preparazione_seed.json  # Dati iniziali Pre-Preparazione (8 schede)
└── .streamlit/
    └── secrets.toml.example        # Modello per le credenziali Turso
```

Al primo avvio l'app crea automaticamente lo schema del database e carica gli
esercizi di base (Manuale + Pre-Preparazione) **solo se il catalogo esercizi è
vuoto** — non sovrascrive mai dati che hai già inserito.

## Come funziona il database

L'app usa **Turso** (database cloud gratuito, compatibile con SQLite) per
salvare i dati in modo permanente. Questo è necessario perché Streamlit
Community Cloud non garantisce che i file salvati localmente sopravvivano ai
redeploy dell'app.

Se le credenziali Turso non sono configurate, l'app usa automaticamente un
file SQLite locale (`data/app.db`) come ripiego: comodo per provare l'app in
locale sul tuo computer, ma **da non usare per l'uso reale su Streamlit
Cloud**, perché quei dati andrebbero persi ad ogni redeploy.

In aggiunta a Turso, la pagina **Backup** permette di scaricare in qualsiasi
momento un file `.json` con una copia completa di tutti i dati, e di
ripristinarlo in caso di necessità. È una rete di sicurezza indipendente da
Turso: usala periodicamente (es. dopo ogni allenamento o partita importante).

## 1. Caricare il progetto su GitHub

Se non l'hai già fatto, crea un nuovo repository:

1. Vai su [github.com/new](https://github.com/new), scegli un nome (es.
   `rosignano-u16-app`), lascialo **privato** se preferisci, e crea il
   repository (senza aggiungere README/licenza, per evitare conflitti).
2. Nel terminale, dentro alla cartella del progetto:

   ```bash
   git init
   git add .
   git commit -m "Prima versione app gestione squadra"
   git branch -M main
   git remote add origin https://github.com/<tuo-utente>/rosignano-u16-app.git
   git push -u origin main
   ```

Il file `.gitignore` è già configurato per escludere il database locale e i
file di credenziali (`secrets.toml`), quindi non finiranno mai su GitHub per
sbaglio.

## 2. Creare il database Turso (se non l'hai già fatto)

1. Registrati su [turso.tech](https://turso.tech) (puoi usare l'account
   Google/Gmail).
2. Crea un database (es. chiamato `rosignano-u16`), scegliendo una regione
   AWS a tua scelta (per un'app come questa, con pochi utenti, la scelta
   della regione ha un impatto trascurabile sulle prestazioni — "EU West
   (Ireland)" va benissimo per l'Italia).
3. Apri la pagina del database creato: nella sezione **Connect** troverai il
   **Database URL** (del tipo `libsql://nome-database-tuoaccount.turso.io`) e
   un pulsante **Create Token** per generare l'**Auth Token**.
4. Conserva questi due valori: ti serviranno al passo successivo.

⚠️ **L'Auth Token è una credenziale segreta**: non condividerlo, non
incollarlo in chat o in messaggi, e non salvarlo mai nel codice o su GitHub.
Va inserito solo nei Secrets di Streamlit Cloud (vedi sotto) o, per uso
locale, nel tuo file personale `.streamlit/secrets.toml` (già escluso da
Git).

## 3. Deploy su Streamlit Community Cloud

1. Vai su [share.streamlit.io](https://share.streamlit.io) e accedi con il
   tuo account GitHub.
2. Clicca su **"New app"**, seleziona il repository appena creato, il branch
   `main` e il file principale `app.py`.
3. Prima di avviare il deploy (o subito dopo, dalle impostazioni dell'app),
   apri la sezione **"Secrets"** e incolla:

   ```toml
   TURSO_DATABASE_URL = "libsql://il-tuo-database-xxxx.turso.io"
   TURSO_AUTH_TOKEN = "il-tuo-token-segreto"
   ```

   (sostituendo con i valori reali ottenuti da Turso al passo 2).
4. Salva e avvia il deploy. Dopo un paio di minuti l'app sarà online con un
   link che puoi condividere con chi vuoi (es. dirigenti, altri allenatori).

Da questo momento, ogni volta che fai `git push` di modifiche al codice,
Streamlit Cloud aggiorna automaticamente l'app online.

## 3bis. Aggiornare l'app dopo una modifica al codice

Ogni volta che il codice del progetto viene modificato (es. da Claude, dopo
una richiesta di miglioria), per far arrivare la modifica sull'app online
servono questi passaggi, dalla cartella del progetto sul tuo computer:

```bash
git add .
git commit -m "Descrizione modifica"
git push
```

- `git add .` prepara tutti i file modificati.
- `git commit -m "Descrizione modifica"` crea un "pacchetto" con le modifiche:
  la scritta tra virgolette è solo una breve nota per te stesso (e per la
  cronologia del progetto) su cosa è cambiato — es.
  `git commit -m "Rinominato Board Manuale in Eserciziario, aggiunto tema colori"`.
  Non è un comando magico: puoi scrivere qualunque frase descrittiva, anche
  breve, non influisce sul funzionamento dell'app.
- `git push` invia le modifiche a GitHub. Da lì, Streamlit Cloud se ne accorge
  da solo e aggiorna l'app online in automatico, di solito in meno di un
  minuto, senza altre azioni da parte tua.

## 4. Uso in locale (facoltativo, per provare o modificare l'app)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Senza un file `.streamlit/secrets.toml`, l'app userà il database SQLite
locale di fallback (`data/app.db`) — utile per fare prove senza toccare i
dati reali su Turso. Se invece vuoi lavorare in locale sugli stessi dati
online, copia `.streamlit/secrets.toml.example` in
`.streamlit/secrets.toml` e inserisci le tue credenziali Turso reali.

## 5. Backup dei dati

Nella pagina **Backup** dell'app:

- **Esporta backup**: genera e scarica un file `.json` con tutti i dati
  attuali (squadra, rosa, manuale esercizi, allenamenti, partite,
  statistiche). Fallo periodicamente e conserva i file in un posto sicuro
  (es. Google Drive, email a te stesso, ecc.).
- **Importa / Ripristina da backup**: carica un file `.json` generato in
  precedenza per ripristinare i dati. L'app mostra sempre un'anteprima di
  cosa verrà eliminato e cosa verrà ripristinato, e chiede una conferma
  esplicita prima di procedere, perché **questa operazione sostituisce
  completamente i dati attuali**.

## Colori squadra e tema dell'app

I colori impostati in **Board Iniziale** (colore primario e colore secondario)
vengono usati automaticamente come tema grafico di tutta l'app: il colore
primario è lo sfondo della parte centrale, il secondario è lo sfondo della
barra laterale, e le caselle di testo hanno uno sfondo primario più scuro con
bordo del colore secondario. Il colore del testo (bianco o nero) viene scelto
automaticamente per restare sempre leggibile. Se i colori non sono ancora
stati impostati, l'app usa il tema grafico predefinito di Streamlit.

## Eserciziario: nome, immagine e video degli esercizi

Da ogni scheda esercizio, nel form di modifica, puoi ora: cambiare il nome
dell'esercizio, sostituire l'immagine (carica un nuovo file: quella vecchia
viene sostituita) e aggiungere un link a un video (es. YouTube, Google Drive,
WeTransfer). Il video è gestito come link esterno e non come file caricato:
i video pesano molto di più delle immagini, e caricarli direttamente
nell'app rischierebbe di rallentarla o di superare i limiti del database —
un link esterno resta invece leggero e affidabile. Le immagini caricate
manualmente (sia in "Aggiungi nuovo esercizio" sia sostituendo un'immagine
esistente) vengono salvate direttamente nel database (Turso), non sul disco
del server, cosa necessaria perché su Streamlit Cloud i file salvati su disco
possono andare persi ad ogni redeploy.

## Inserisci Dati, Storico Allenamenti e Storico Partite

La registrazione di un nuovo allenamento o di una nuova partita avviene ora
in un'unica board, **Inserisci Dati**: un pulsante a scelta multipla in alto
permette di passare dall'uno all'altro, con sotto esattamente gli stessi
campi di prima. Lo storico e le statistiche sono invece divisi in due board
dedicate: **Storico Allenamenti** (elenco sedute, modifica presenze ed
esercizi, export PDF e statistiche) e **Storico Partite** (elenco partite,
filtri, distinte ed eventi).

## Storico Allenamenti: motivo assenze e PDF riepilogativo

Quando registri un nuovo allenamento e deselezioni un giocatore come assente,
compare subito un campo per indicarne il motivo (facoltativo). Il motivo
resta salvato insieme alla presenza/assenza e viene mostrato sia nello
storico sia nel PDF.

Per ogni allenamento nello storico è disponibile un pulsante "Genera PDF
allenamento": crea un documento con una prima pagina di riepilogo (data, ora,
durata, assenti con motivazione, elenco degli esercizi svolti) seguita da una
pagina per ciascun esercizio con la sua immagine, così puoi stamparlo o
condividerlo facilmente.

## Note sui dati iniziali del Manuale

Gli esercizi caricati automaticamente al primo avvio (55 nel Manuale + 8
schede di Pre-Preparazione) sono stati trascritti dai PDF forniti
("Esercizi Esordienti" e "Programma Rosignano"). Alcuni campi sono stati
lasciati vuoti quando l'informazione non era presente nella slide originale
(es. numero di colori casacche, dimensioni campo per alcune schede di
pre-preparazione) — puoi completarli liberamente dalla Board Manuale.
