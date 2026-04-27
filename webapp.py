import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Valutazione Atleta", page_icon="⚽", layout="centered")

# --- CONNESSIONE ---
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1iNO4MNQCXHo9hBzOcBPzKR3xu1kt_E_w1eyQYQiqngw/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- STILE CSS (MOBILE VERTICALE) ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    
    .domanda-testo {
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 25px;
        color: #1e293b;
    }

    .opzione-verticale {
        display: flex;
        align-items: center;
        width: 100%;
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        background-color: #f8fafc;
    }

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

    .testo-opzione {
        font-size: 20px;
        font-weight: 600;
        color: #1e293b;
    }

    /* Tasto trasparente per le opzioni delle domande */
    .stButton > button[key^="btn_"] {
        width: 100% !important;
        height: 70px !important;
        background-color: transparent !important;
        color: transparent !important;
        border: none !important;
        position: absolute;
        z-index: 10;
        margin-top: -70px;
    }

    /* Stile per i tasti normali (Inizia, Indietro) */
    .stButton > button {
        border-radius: 10px;
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

# --- STEP 0: SCHERMATA INIZIALE ---
if st.session_state.step == 0:
    st.session_state.nome_atleta = st.text_input("Nome e Cognome", placeholder="Es: Mario Rossi")
    # IL TASTO START ORA È QUI
    if st.button("INIZIA TEST", type="primary", use_container_width=True):
        if st.session_state.nome_atleta.strip():
            st.session_state.step = 1
            st.rerun()
        else:
            st.error("Inserisci il tuo nome per iniziare")

# --- STEP 1-5: DOMANDE ---
elif 1 <= st.session_state.step <= len(domande):
    idx = st.session_state.step - 1
    st.write(f"Domanda {st.session_state.step} di {len(domande)}")
    st.markdown(f"<p class='domanda-testo'>{domande[idx]}</p>", unsafe_allow_html=True)
    
    for i, op in enumerate(opzioni):
        st.markdown(f"""
            <div class="opzione-verticale">
                <div class="bollino" style="background-color: {op['colore']};">{op['emoji']}</div>
                <div class="testo-opzione">{op['label']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Scegli {op['label']}", key=f"btn_{idx}_{i}"):
            st.session_state.risposte[f"q{idx}"] = i + 1
            st.session_state.step += 1
            st.rerun()

    st.markdown("---")
    if st.button("⬅️ Indietro", use_container_width=True):
        st.session_state.step -= 1
        st.rerun()

# --- STEP FINALE: SALVATAGGIO ---
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
