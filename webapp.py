import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Valutazione Atleta", page_icon="⚽", layout="centered")

# --- CONNESSIONE A GOOGLE SHEETS ---
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1iNO4MNQCXHo9hBzOcBPzKR3xu1kt_E_w1eyQYQiqngw/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- STILE CSS AGGRESSIVO PER MOBILE (NO SCROLL) ---
st.markdown("""
    <style>
    /* Nasconde menu inutili per risparmiare spazio */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Testo domanda più compatto */
    .domanda-testo {
        font-size: 20px !important;
        font-weight: bold;
        text-align: center;
        margin-bottom: 15px;
    }
    
    /* Forza il contenitore orizzontale a non andare a capo e non scrollare */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        justify-content: center !important;
        gap: 2px !important;
    }

    /* Forza le colonne a dividersi lo spazio equamente */
    div[data-testid="column"] {
        width: 19% !important;
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }

    /* Stile del bollino colorato più piccolo (45px) per mobile */
    .bollino-fisico {
        border-radius: 50%;
        width: 45px;
        height: 45px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin: 0 auto;
        border: 2px solid white;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.2);
    }

    /* Rende il bottone di Streamlit invisibile e sovrapposto al bollino */
    div[data-testid="column"] button {
        background: transparent !important;
        color: transparent !important;
        border: none !important;
        height: 45px !important;
        width: 45px !important;
        position: absolute;
        z-index: 10;
        margin-top: -45px; /* Lo sposta sopra il bollino */
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATI ---
domande = [
    "Come ti sei sentito oggi in campo?",
    "Come ti sei relazionato con i compagni?",
    "Come hai gestito il tuo sguardo oggi?",
    "Come ti sei relazionato con lo staff?",
    "Penti di aver avuto un atteggiamento propositivo?"
]
colori = ["#FF4B4B", "#FFA500", "#FFD700", "#9ACD32", "#4CAF50"]
faccine = ["😠", "🙁", "😐", "🙂", "😁"]

if 'step' not in st.session_state: st.session_state.step = 0
if 'risposte' not in st.session_state: st.session_state.risposte = {}
if 'nome_atleta' not in st.session_state: st.session_state.nome_atleta = ""

# --- LOGICA ---
st.title("⚽ Report Sessione")

if st.session_state.step == 0:
    st.session_state.nome_atleta = st.text_input("Nome e Cognome", placeholder="Mario Rossi")
    if st.button("INIZIA TEST", type="primary", use_container_width=True):
        if st.session_state.nome_atleta.strip():
            st.session_state.step = 1
            st.rerun()

elif 1 <= st.session_state.step <= len(domande):
    idx = st.session_state.step - 1
    st.write(f"Domanda {st.session_state.step} / {len(domande)}")
    st.markdown(f"<p class='domanda-testo'>{domande[idx]}</p>", unsafe_allow_html=True)
    
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            # Disegno il bollino
            st.markdown(f'<div class="bollino-fisico" style="background-color: {colori[i]};">{faccine[i]}</div>', unsafe_allow_html=True)
            # Bottone invisibile sopra per catturare il click
            if st.button(f"_{i}", key=f"b_{idx}_{i}"):
                st.session_state.risposte[f"q{idx}"] = i + 1
                st.session_state.step += 1
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Indietro", use_container_width=True):
        st.session_state.step -= 1
        st.rerun()

elif st.session_state.step > len(domande):
    st.success(f"Grazie {st.session_state.nome_atleta}!")
    
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
            st.error(f"Errore: {e}")

    if st.button("Nuovo Inserimento", use_container_width=True):
        st.session_state.step = 0
        st.session_state.risposte = {}
        if 'salvato' in st.session_state: del st.session_state.salvato
        st.rerun()
