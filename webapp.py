import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Valutazione Atleta", page_icon="⚽", layout="centered")

# --- CONNESSIONE ---
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1iNO4MNQCXHo9hBzOcBPzKR3xu1kt_E_w1eyQYQiqngw/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- STILE CSS (ONE-PAGE & VERTICAL RESPONSIVE) ---
st.markdown("""
    <style>
    /* Rimuove spazi inutili in alto */
    .block-container { padding-top: 1rem; }
    
    .domanda-testo {
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 25px;
        color: #1e293b;
    }

    /* Contenitore verticale per le opzioni */
    .opzione-verticale {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        width: 100%;
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        transition: transform 0.2s;
    }

    /* Il bollino colorato tondo */
    .bollino {
        border-radius: 50%;
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        margin-right: 20px;
        flex-shrink: 0;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    }

    /* Testo descrittivo accanto al bollino */
    .testo-opzione {
        font-size: 20px;
        font-weight: 600;
    }

    /* Nascondiamo il tasto reale di Streamlit e lo espandiamo sopra l'intera riga */
    div.stButton > button {
        width: 100% !important;
        height: 70px !important;
        background-color: transparent !important;
        color: transparent !important;
        border: none !important;
        position: absolute;
        z-index: 10;
        margin-top: -70px;
    }
    
    div.stButton {
        height: 70px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATI ---
domande = [
    "Come ti sei sentito oggi in campo?",
    "Come ti sei relazionato con i compagni?",
    "Come hai gestito il tuo sguardo oggi?",
    "Come ti sei relazionato con lo staff?",
    "Pensi di aver avuto un atteggiamento propositivo?"
]
opzioni = [
    {"label": "Molto male", "emoji": "😠", "colore": "#FF4B4B"},
    {"label": "Male", "emoji": "🙁", "colore": "#FFA500"},
    {"label": "Neutro", "emoji": "😐", "colore": "#FFD700"},
    {"label": "Bene", "emoji": "🙂", "colore": "#9ACD32"},
    {"label": "Ottimo", "emoji": "😁", "colore": "#4CAF50"}
]

if 'step' not in st.session_state: st.session_state.step = 0
if 'risposte' not in st.session_state: st.session_state.risposte = {}
if 'nome_atleta' not in st.session_state: st.session_state.nome_atleta = ""

st.title("⚽ Report Sessione")

# --- LOGICA ONE-PAGE ---

if st.session_state.step == 0:
    st.session_state.nome_atleta = st.text_input("Nome e Cognome", placeholder="Es: Mario Rossi")
    if st.button("INIZIA TEST", type="primary", use_container_width=True):
        if st.session_state.nome_atleta.strip():
            st.session_state.step = 1
            st.rerun()

elif 1 <= st.session_state.step <= len(domande):
    idx = st.session_state.step - 1
    st.write(f"Domanda {st.session_state.step} di {len(domande)}")
    st.markdown(f"<p class='domanda-testo'>{domande[idx]}</p>", unsafe_allow_html=True)
    
    # GENERAZIONE OPZIONI IN VERTICALE (NO COLONNE = NO SCROLL)
    for i, op in enumerate(opzioni):
        st.markdown(f"""
            <div class="opzione-verticale">
                <div class="bollino" style="background-color: {op['colore']};">{op['emoji']}</div>
                <div class="testo-opzione">{op['label']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Tasto trasparente sopra la riga
        if st.button(f"Scegli {op['label']}", key=f"btn_{idx}_{i}"):
            st.session_state.risposte[f"q{idx}"] = i + 1
            st.session_state.step += 1
            st.rerun()

    st.markdown("---")
    if st.button("⬅️ Indietro", use_container_width=True):
        st.session_state.step -= 1
        st.rerun()

elif st.session_state.step > len(domande):
    st.success(f"✅ Grazie {st.session_state.nome_atleta}!")
    
    if 'salvato' not in st.session_state:
        try:
            nuova_riga = pd.DataFrame([{
                "data": datetime.today().strftime("%d/%m/%Y"),
                "nome": st.session_state.nome_atleta,
                "q1": st.session_state.risposte["q0"],
                "q2": st.session_state.risposte["q1"],
                "q3": st.session_state.risposte["q2"],
                "q4": st.session_state.risposte["q3"],
                "q5": st.session_state.risposte["q4"],
                "media": round(sum(st.session_state.risposte.values())/5, 2)
            }])
            
            df_esistente = conn.read(spreadsheet=URL_FOGLIO, ttl=0)
            df_finale = pd.concat([df_esistente, nuova_riga], ignore_index=True).dropna(how='all')
            conn.update(spreadsheet=URL_FOGLIO, data=df_finale)
            st.session_state.salvato = True
            st.balloons()
        except Exception as e:
            st.error(f"Errore di salvataggio: {e}")

    if st.button("Invia un altro report", use_container_width=True):
        st.session_state.step = 0
        st.session_state.risposte = {}
        if 'salvato' in st.session_state: del st.session_state.salvato
        st.rerun()
