import os
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ==========================================
# 1. CONFIGURAZIONE
# ==========================================
URL_UST = "https://mo.istruzioneer.gov.it/category/interpelli-personale-docente-2025-26/"
DATA_FILE = "interpelli.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Variabile globale che ora accetta sia CDC che nomi di scuole/parole chiave
PAROLE_CHIAVE = []

# ==========================================
# 2. FUNZIONI DI UTILITA' E MENU
# ==========================================
def carica_parole_chiave():
    global PAROLE_CHIAVE
    
    # Legge le parole da GitHub Actions (Variabile CDC_PREFERITE)
    parole_github = os.getenv("CDC_PREFERITE")
    
    if parole_github is not None:
        if parole_github.strip():
            # Separiamo per virgola e togliamo gli spazi in eccesso
            PAROLE_CHIAVE = [p.strip().upper() for p in parole_github.split(",") if p.strip()]
            print(f"🤖 [Cloud Mode] Ricerca Parole/CDC impostata: {', '.join(PAROLE_CHIAVE)}")
        else:
            PAROLE_CHIAVE = []
            print("🤖 [Cloud Mode] Nessuna parola specifica. Modalità 'Solo Database'.")
        return

    # SUL PC LOCALE
    print("\n" + "="*50)
    print("🎓 SISTEMA MONITORAGGIO INTERPELLI - UST MODENA")
    print("="*50)
    print("Puoi inserire CDC (es. A041) o nomi di scuole/città (es. BAGGI, CARPI).")
    input_utente = input("👉 Le tue chiavi separate da virgola (o INVIO per tutte): ")
    
    if not input_utente.strip():
        PAROLE_CHIAVE = []
        return

    PAROLE_CHIAVE = [p.strip().upper() for p in input_utente.split(",") if p.strip()]

def invia_notifica_telegram(titolo, motivi_match, link_interpello):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return

    motivo_str = ", ".join(motivi_match)
    messaggio = (
        f"🚨 <b>NUOVO INTERPELLO RILEVATO!</b>\n\n"
        f"🎯 <b>Match trovato per:</b> {motivo_str}\n"
        f"📝 <b>Titolo:</b> {titolo}\n\n"
        f"🔗 <a href='{link_interpello}'>Clicca qui per aprire l'avviso</a>"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": messaggio, "parse_mode": "HTML"}
    
    try:
        requests.post(url, data=payload)
        print(f"  ✅ Notifica Telegram inviata! (Match: {motivo_str})")
    except Exception as e:
        print(f"  ❌ Errore invio Telegram: {e}")

def estrai_dettagli_pagina(url_pagina):
    dettagli = {"pdf_links": [], "form_links": []}
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url_pagina, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.lower().endswith('.pdf') and href not in dettagli["pdf_links"]:
                dettagli["pdf_links"].append(href)
            elif ("docs.google.com/forms" in href or "forms.gle" in href) and href not in dettagli["form_links"]:
                dettagli["form_links"].append(href)
    except Exception as e:
        pass
    return dettagli

def estrai_cdc(testo):
    # Continua a estrarre matematicamente le CDC per popolare correttamente il database e la dashboard
    pattern = r'\b[A-Za-z][\-\s]*\d{2,3}\b'
    trovati = re.findall(pattern, testo)
    cdc_pulite = set(re.sub(r'[^A-Za-z0-9]', '', c).upper() for c in trovati)
    return list(cdc_pulite)

# ==========================================
# 3. MOTORE PRINCIPALE (SCRAPER)
# ==========================================
def esegui_scraper():
    carica_parole_chiave()
    
    print("🚀 Avvio scraper UST Modena con Ricerca Universale...")
    
    storico = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                storico = json.load(f)
                print(f"📂 Trovato storico: {len(storico)} interpelli già noti.")
            except:
                pass
    
    url_visti = {item["url"] for item in storico}
    nuovi_interpelli_totali = 0
    
    url_attuale = URL_UST
    numero_pagina = 1
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    while url_attuale:
        print(f"\n📄 Analizzo Pagina {numero_pagina}: {url_attuale}")
        
        try:
            risposta = requests.get(url_attuale, headers=headers, timeout=10)
            if risposta.status_code != 200:
                print(f"❌ Errore HTTP {risposta.status_code}")
                break
        except Exception as e:
            print(f"❌ Errore rete: {e}")
            break

        soup = BeautifulSoup(risposta.text, 'html.parser')
        articoli = soup.find_all('a', rel="bookmark")
        
        nuovi_nella_pagina = 0

        for art in articoli:
            titolo = art.get_text(strip=True)
            url_avviso = art['href']
            
            if url_avviso in url_visti:
                continue
                
            print(f"  🆕 Nuovo: {titolo}")
            nuovi_nella_pagina += 1
            nuovi_interpelli_totali += 1
            
            data_match = re.search(r'/(\d{4}/\d{2}/\d{2})/', url_avviso)
            data_pubblicazione = data_match.group(1).replace("/", "-") if data_match else datetime.today().strftime('%Y-%m-%d')
            
            cdc_presenti = estrai_cdc(titolo)
            dettagli = estrai_dettagli_pagina(url_avviso)
            
            nuovo_interpello = {
                "titolo": titolo,
                "url": url_avviso,
                "data": data_pubblicazione,
                "cdc": cdc_presenti,
                "pdf_links": dettagli["pdf_links"],
                "form_links": dettagli["form_links"],
                "data_rilevamento": datetime.now().isoformat()
            }
            
            storico.insert(0, nuovo_interpello)
            url_visti.add(url_avviso)
            
            # --- NUOVA LOGICA DI NOTIFICA UNIVERSALE ---
            motivi_match = []
            titolo_maiuscolo = titolo.upper()
            
            if PAROLE_CHIAVE:
                for parola in PAROLE_CHIAVE:
                    # Se è una CDC normale (es A041) guarda se il tool matematico l'ha trovata,
                    # altrimenti cerca brutalmente la parola nel testo (es BAGGI, CARPI).
                    if parola in cdc_presenti or parola in titolo_maiuscolo:
                        motivi_match.append(parola)
            
            # Se ha trovato almeno una corrispondenza, manda la notifica!
            if motivi_match:
                invia_notifica_telegram(titolo, motivi_match, url_avviso)
                
            time.sleep(0.5) 

        # Interruzione
        if nuovi_nella_pagina == 0 and len(storico) > 0:
            print("🛑 Tutti gli avvisi di questa pagina sono già nel database. Stop.")
            break

        # Prossima pagina
        bottone_next = None
        for a in soup.find_all('a', href=True):
            if 'articoli meno recenti' in a.get_text(strip=True).lower():
                bottone_next = a
                break
        
        if bottone_next:
            url_attuale = bottone_next['href']
            numero_pagina += 1
            time.sleep(1) 
        else:
            url_attuale = None

    if nuovi_interpelli_totali > 0:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(storico, f, indent=4, ensure_ascii=False)
        print(f"\n💾 Aggiornato! Aggiunti {nuovi_interpelli_totali} nuovi.")
    else:
        print("\n💤 Nessun nuovo interpello.")

if __name__ == "__main__":
    esegui_scraper()
