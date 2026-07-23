# 🎓 Monitoraggio Interpelli UST Modena

Questo progetto è un sistema 100% gratuito e automatizzato per il monitoraggio degli interpelli (supplenze scolastiche) pubblicati sul sito dell'Ufficio Scolastico Territoriale di Modena.

## 🚀 Funzionalità
- **Scraping Automatico:** Controlla il sito ogni ora dal lunedì al venerdì (7:00 - 19:00).
- **Notifiche Telegram:** Invia un avviso in tempo reale se viene pubblicato un interpello per le tue Classi di Concorso (CDC) preferite.
- **Dashboard Web:** Un'interfaccia interattiva ospitata su GitHub Pages per filtrare e visualizzare tutti gli avvisi dell'anno scolastico, evidenziando quelli più recenti.
- **Smart Paginator:** Gestione intelligente delle pagine storiche per non sovraccaricare il server.

---

## 🛠️ MANUALE DI GESTIONE (Per l'amministratore)

Poiché gli interpelli sono attivi solo in determinati periodi dell'anno, questo sistema è progettato per essere facilmente messo in pausa e aggiornato per gli anni scolastici successivi senza dover mai toccare il codice.

### ⏸️ 1. Come mettere in PAUSA il sistema (es. durante l'estate)
Per non consumare minuti gratuiti di GitHub Actions quando non ci sono nomine, puoi "spegnere" il bot:
1. Vai sulla pagina principale di questo repository.
2. Clicca in alto sulla scheda **Actions**.
3. Nel menu a sinistra, clicca su **Interpelli Scraper Automazione**.
4. Sulla destra, clicca sul pulsante con i **tre puntini (`...`)**.
5. Seleziona **Disable workflow**.

*(Per riattivarlo a Settembre, ripeti la procedura e clicca su **Enable workflow**).*

### 🔄 2. Come aggiornare il Link per il nuovo Anno Scolastico (es. 2026/2027)
Quando l'UST cambierà la pagina web ufficiale per il nuovo anno, il bot si adatterà automaticamente. Devi solo aggiornare la variabile:
1. Clicca in alto sulla scheda ⚙️ **Settings**.
2. Nel menu a sinistra scorri verso il basso, apri **Secrets and variables** e clicca su **Actions**.
3. Clicca sulla scheda **Variables** (NON Secrets).
4. Trova la variabile `URL_UST_MODENA` e clicca sull'icona della **matita** (Edit).
5. Incolla il nuovo link ufficiale e salva.

*Nota: Se vuoi fare "tabula rasa" del database per il nuovo anno, ricordati anche di eliminare (o svuotare) il file `interpelli.json` dal repository, così il bot ricomincerà a contare da zero.*

### 📚 3. Come modificare le tue Classi di Concorso (CDC)
Se decidi di voler ricevere notifiche Telegram per nuove CDC:
1. Vai su ⚙️ **Settings** > **Secrets and variables** > **Actions** > scheda **Variables**.
2. Modifica la variabile `CDC_PREFERITE`.
3. Inserisci le tue CDC separate da virgola (es. `A041, A026, A027`).
4. Salva. Al prossimo giro, il bot cercherà le nuove classi.

---

## ⚙️ Infrastruttura Tecnica
- **Motore:** GitHub Actions (Cron Jobs)
- **Logica:** Python 3 (Requests, BeautifulSoup, Regex)
- **Database:** JSON flat-file (`interpelli.json`) aggiornato tramite Auto-Commit.
- **Notifiche:** API di Telegram (BotFather)
- **Frontend:** HTML5, JS Vanilla, Tailwind CSS ospitato su GitHub Pages.

Creato con automazione intelligente per farti risparmiare tempo. Buon anno scolastico! 🍎
