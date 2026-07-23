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

# Variabile globale
CDC_DI_INTERESSE = []

# ==========================================
# 2. FUNZIONI DI UTILITA' E MENU
# ==========================================
def chiedi_cdc_utente():
    global CDC_DI_INTERESSE
    
    # 1. Controlla se siamo su GitHub Actions (leggendo la variabile)
    cdc_github = os.getenv("CDC_PREFERITE")
    
    if cdc_github is not None:
        if cdc_github.strip():
            cdc_inserite = [c.strip().upper() for c in cdc_github.split(",")]
            CDC_DI_INTERESSE = [re.sub(r'[^A-Z0-9]', '', c) for c in cdc_inserite if c]
            print(f"🤖 [Cloud Mode] Ricerca CDC impostata: {', '.join(CDC_DI_INTERESSE)}")
        else:
            CDC_DI_INTERESSE = []
            print("🤖 [Cloud Mode] Nessuna CDC specifica. Modalità 'Solo Database'.")
        return

    # 2. ALTRIMENTI SIAMO SUL TUO PC
    print("\n" + "="*50)
    print("🎓 SISTEMA MONITORAGGIO INTERPELLI - UST MODENA")
    print("="*50)
    input_utente = input("\n👉 Le tue CDC (es. A041, A026) o premi INVIO per tutte: ")
    
    if not input_utente.strip():
        CDC_DI_INTERESSE = []
        return

    cdc_inserite = [c.strip().upper() for c in input_utente.split(",")]
    CDC_DI_INTERESSE = [re.sub(r'[^A-Z0-9]', '', c) for c in cdc_inserite if c]

def invia_notifica_telegram(titolo, cdc_trovate, link_interpello, scadenza="Non specificata"):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return

    cdc_str = ", ".join(cdc_trovate) if cdc_trovate else "Sconosciuta"
    messaggio = (
        f"🚨 <b>NUOVO INTERPELLO RILEVATO!</b>\n\n"
        f"📚 <b>CDC:</b> {cdc_str}\n"
        f"📝 <b>Titolo:</b> {titolo}\n"
        f"🔗 <a href='{link_interpello}'>Clicca qui per aprire l'avviso</a>"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": messaggio, "parse_mode": "HTML"}
    
    try:
        requests.post(url, data=payload)
        print(f"  ✅ Notifica Telegram inviata!")
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
    pattern = r'\b[A-Za-z][\-\s]*\d{2,3}\b'
    trovati = re.findall(pattern, testo)
    cdc_pulite = set(re.sub(r'[^A-Za-z0-9]', '', c).upper() for c in trovati)
    return list(cdc_pulite)

# ==========================================
# 3. MOTORE PRINCIPALE (SCRAPER)
# ==========================================
def esegui_scraper():
    chiedi_cdc_utente()
    
    print("🚀 Avvio scraper UST Modena con Paginazione...")
    
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
                print(f"❌ Errore caricamento pagina: HTTP {risposta.status_code}")
                break
        except Exception as e:
            print(f"❌ Errore di rete: {e}")
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
            
            # Notifica Telegram
            if CDC_DI_INTERESSE and any(cdc in CDC_DI_INTERESSE for cdc in cdc_presenti):
                invia_notifica_telegram(titolo, cdc_presenti, url_avviso)
                
            time.sleep(0.5) 

        # Interruzione intelligente
        if nuovi_nella_pagina == 0 and len(storico) > 0:
            print("🛑 Tutti gli avvisi di questa pagina sono già nel database. Interrompo la paginazione.")
            break

        # Cerca bottone "Articoli meno recenti"
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
            print("🏁 Ultima pagina raggiunta.")
            url_attuale = None

    if nuovi_interpelli_totali > 0:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(storico, f, indent=4, ensure_ascii=False)
        print(f"\n💾 Database aggiornato! Aggiunti {nuovi_interpelli_totali} nuovi interpelli.")
    else:
        print("\n💤 Nessun nuovo interpello trovato.")

if __name__ == "__main__":
    esegui_scraper()
