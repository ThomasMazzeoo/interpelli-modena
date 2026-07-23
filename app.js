// Variabili globali per memorizzare i dati
let tuttiInterpelli = [];

// Funzione principale che si avvia al caricamento della pagina
document.addEventListener('DOMContentLoaded', () => {
    caricaDati();

    // Aggiungi gli event listener per la ricerca e il filtro
    document.getElementById('searchInput').addEventListener('input', filtraDati);
    document.getElementById('cdcFilter').addEventListener('change', filtraDati);
});

// 1. CARICAMENTO DATI
async function caricaDati() {
    try {
        const response = await fetch('interpelli.json?' + new Date().getTime());
        
        if (!response.ok) throw new Error("Errore nel caricamento del file JSON");
        
        tuttiInterpelli = await response.json();
        
        popolaMenuCDC(tuttiInterpelli);
        filtraDati(); 
        
    } catch (error) {
        console.error(error);
        document.getElementById('interpelliContainer').innerHTML = `
            <div class="col-span-full bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
                <strong class="font-bold">Attenzione!</strong>
                <span class="block sm:inline"> Impossibile caricare i dati. Assicurati che lo scraper abbia generato il file 'interpelli.json'.</span>
            </div>`;
    }
}

// 2. POPOLAMENTO MENU A TENDINA CDC
function popolaMenuCDC(dati) {
    const select = document.getElementById('cdcFilter');
    const cdcUniche = new Set();

    dati.forEach(item => {
        if (item.cdc && Array.isArray(item.cdc)) {
            item.cdc.forEach(c => cdcUniche.add(c));
        }
    });

    Array.from(cdcUniche).sort().forEach(cdc => {
        const option = document.createElement('option');
        option.value = cdc;
        option.textContent = cdc;
        select.appendChild(option);
    });
}

// 3. LOGICA DI FILTRAGGIO E ORDINAMENTO
function filtraDati() {
    const testoSito = document.getElementById('searchInput').value.toLowerCase();
    const cdcScelta = document.getElementById('cdcFilter').value;

    let risultatiFiltrati = tuttiInterpelli.filter(item => {
        const matchTesto = item.titolo.toLowerCase().includes(testoSito);
        let matchCDC = true; 
        if (cdcScelta !== "ALL") {
            matchCDC = item.cdc && item.cdc.includes(cdcScelta);
        }
        return matchTesto && matchCDC;
    });

    // --- NUOVA LOGICA DI ORDINAMENTO (INFALLIBILE DAL PIU RECENTE) ---
    risultatiFiltrati.sort((a, b) => {
        // Usa la stringa testuale della data per l'ordinamento se è nel formato YYYY-MM-DD
        // Se le date sono stringhe ISO (es. "2026-06-15" e "2025-09-16"), il confronto testuale funziona perfettamente
        let dataA = a.data || "";
        let dataB = b.data || "";
        
        if (dataA > dataB) return -1; // Se A è più recente (più grande) di B, mettilo prima
        if (dataA < dataB) return 1;  // Se A è più vecchio di B, mettilo dopo
        
        // Se la data di pubblicazione è identica, usa la data di rilevamento dello scraper
        let rilA = a.data_rilevamento || "";
        let rilB = b.data_rilevamento || "";
        if (rilA > rilB) return -1;
        if (rilA < rilB) return 1;
        
        return 0;
    });

    renderizzaCard(risultatiFiltrati);
}

// 4. CREAZIONE VISIVA DELLE SCHEDE (CARDS)
function renderizzaCard(dati) {
    const container = document.getElementById('interpelliContainer');
    const counter = document.getElementById('risultatiCounter');
    
    container.innerHTML = '';
    counter.innerHTML = `Mostrando <strong>${dati.length}</strong> interpelli.`;

    if (dati.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-10 text-gray-500">
                <i class="fa-solid fa-folder-open text-4xl mb-3"></i>
                <p>Nessun interpello trovato con i filtri attuali.</p>
            </div>`;
        return;
    }

    const dataOdierna = new Date();

    dati.forEach(item => {
        // --- LOGICA "NUOVO" ---
        let isNuovo = false;
        if (item.data_rilevamento) {
            const dataRilevamento = new Date(item.data_rilevamento);
            const differenzaOre = (dataOdierna - dataRilevamento) / (1000 * 60 * 60);
            if (differenzaOre <= 48) {
                isNuovo = true;
            }
        }

        const badgeCDC = item.cdc && item.cdc.length > 0 
            ? item.cdc.map(c => `<span class="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10 mr-1">${c}</span>`).join('')
            : `<span class="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-xs font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10">Generico</span>`;

        let linksHTML = `<a href="${item.url}" target="_blank" class="text-blue-600 hover:text-blue-800 text-sm font-medium"><i class="fa-solid fa-globe"></i> Apri Pagina</a>`;
        
        if (item.pdf_links && item.pdf_links.length > 0) {
            linksHTML += `<br><a href="${item.pdf_links[0]}" target="_blank" class="text-red-600 hover:text-red-800 text-sm font-medium mt-1 inline-block"><i class="fa-solid fa-file-pdf"></i> Scarica PDF</a>`;
        }
        if (item.form_links && item.form_links.length > 0) {
            linksHTML += `<br><a href="${item.form_links[0]}" target="_blank" class="text-green-600 hover:text-green-800 text-sm font-medium mt-1 inline-block"><i class="fa-solid fa-list-check"></i> Compila Form</a>`;
        }

        // --- FORMATTAZIONE DATA ITALIANA SICURA ---
        let dataVisualizzata = item.data;
        if (item.data && item.data.includes('-')) {
            // Se la data è "2025-09-16", la dividiamo e la rigiriamo in "16/09/2025"
            const parti = item.data.split('-');
            if (parti.length === 3) {
                dataVisualizzata = `${parti[2]}/${parti[1]}/${parti[0]}`;
            }
        }

        const cardHTML = `
            <div class="interpello-card bg-white rounded-lg shadow-sm border border-gray-200 p-5 flex flex-col h-full ${isNuovo ? 'card-nuova' : ''}">
                ${isNuovo ? '<span class="badge-nuovo">NUOVO</span>' : ''}
                
                <div class="text-xs text-gray-500 mb-2 flex justify-between items-center">
                    <span><i class="fa-regular fa-calendar"></i> Pubblicato: <span class="font-bold text-gray-700">${dataVisualizzata}</span></span>
                </div>
                
                <h3 class="text-lg font-bold text-gray-900 mb-3 leading-tight">${item.titolo}</h3>
                
                <div class="mb-4">
                    ${badgeCDC}
                </div>
                
                <div class="mt-auto pt-4 border-t border-gray-100">
                    ${linksHTML}
                </div>
            </div>
        `;
        
        container.innerHTML += cardHTML;
    });
}
