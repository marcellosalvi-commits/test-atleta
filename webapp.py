import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Valutazione Atleta", page_icon="⚽", layout="centered")

# --- CONNESSIONE A GOOGLE SHEETS ---
# Sostituisci questo URL con quello del tuo foglio, assicurandoti che includa la parte 'gid=0'
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1iNO4MNQCXHo9hBzOcBPzKR3xu1kt_E_w1eyQYQiqngw/edit#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- STILE CSS PER TELEFONO ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .domanda-testo {
        font-size: 22px;
        font-weight: bold;
        color: #1e293b;
        margin-bottom: 20px;
        text-align: center;
        line-height: 1.2;
    }
    
    /* Layout orizzontale per i bollini su mobile */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        justify-content: center !important;
        gap: 5px !important;
    }

    /* Riduzione bottoni per non farli uscire dallo schermo */
    div[data-testid="column"] button {
        padding: 0px !important;
        width: 100% !important;
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
colori_bollini = ["#FF4B4B", "#FFA500", "#FFD700", "#9ACD32", "#4CAF50"]
faccine = ["😠", "🙁", "😐", "🙂", "😁"]
PASSWORD_STAFF = "mister123"

# --- STATO SESSIONE ---
if 'step' not in st.session_state: st.session_state.step = 0
if 'risposte' not in st.session_state: st.session_state.risposte = {}
if 'nome_atleta' not in st.session_state: st.session_state.nome_atleta = ""
if 'data_sessione' not in st.session_state: st.session_state.data_sessione = datetime.today()

def avanti(): st.session_state.step += 1
def indietro(): 
    if st.session_state.step > 0: st.session_state.step -= 1
def reset_form():
    st.session_state.step = 0
    st.session_state.risposte = {}
    st.session_state.nome_atleta = ""
    if 'salvato' in st.session_state: del st.session_state.salvato

# --- INTERFACCIA ---
st.title("⚽ Report Sessione Atleta")

if st.session_state.step == 0:
    st.subheader("Benvenuto! Inserisci i tuoi dati.")
    st.session_state.nome_atleta = st.text_input("Nome e Cognome", value=st.session_state.nome_atleta)
    st.session_state.data_sessione = st.date_input("Data", value=st.session_state.data_sessione)
    if st.button("INIZIA TEST", type="primary", use_container_width=True):
        if not st.session_state.nome_atleta.strip(): st.error("⚠️ Inserisci il nome.")
        else: avanti(); st.rerun()

elif 1 <= st.session_state.step <= len(domande):
    idx = st.session_state.step - 1
    st.write(f"Domanda {st.session_state.step} / {len(domande)}")
    st.markdown(f"<p class='domanda-testo'>{domande[idx]}</p>", unsafe_allow_html=True)
    
    chiave = f"q{idx}"
    scelto = st.session_state.risposte.get(chiave)
    cols = st.columns(5)
    
    for i in range(5):
        val = i + 1
        is_sel = (scelto == val)
        op = "1.0" if (scelto is None or is_sel) else "0.4"
        sc = "scale(1.1)" if is_sel else "scale(1.0)"
        brd = "border: 2px solid #000;" if is_sel else ""
        
        with cols[i]:
            st.markdown(f"""
            <div style='background-color:{colori_bollini[i]}; border-radius:50%; width:45px; height:45px; 
                        display:flex; align-items:center; justify-content:center; font-size:25px; 
                        margin: 0 auto; opacity: {op}; transform: {sc}; {brd}'>
                <span>{faccine[i]}</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"{val}", key=f"b_{st.session_state.step}_{i}", use_container_width=True):
                st.session_state.risposte[chiave] = val
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("⬅️ Indietro", use_container_width=True): indietro(); st.rerun()
    with c2:
        if scelto:
            if st.button("AVANTI ➡️" if st.session_state.step < len(domande) else "FINALE 🏁", type="primary", use_container_width=True):
                avanti(); st.rerun()

elif st.session_state.step > len(domande):
    st.success(f"✅ Grazie {st.session_state.nome_atleta}!")
    
    if 'salvato' not in st.session_state:
        try:
            # Creazione riga
            nuova_riga = pd.DataFrame([{
                "data": st.session_state.data_sessione.strftime("%d/%m/%Y"),
                "nome": st.session_state.nome_atleta,
                "q1": st.session_state.risposte["q0"],
                "q2": st.session_state.risposte["q1"],
                "q3": st.session_state.risposte["q2"],
                "q4": st.session_state.risposte["q3"],
                "q5": st.session_state.risposte["q4"],
                "media": round(sum(st.session_state.risposte.values())/5, 2)
            }])
            
            # LETTURA E AGGIORNAMENTO
            df_vecchio = conn.read(spreadsheet=URL_FOGLIO, ttl=0)
            df_finale = pd.concat([df_vecchio, nuova_riga], ignore_index=True).dropna(how='all')
            
            # UPDATE
            conn.update(spreadsheet=URL_FOGLIO, data=df_finale)
            st.session_state.salvato = True
            st.balloons()
        except Exception as e:
            st.error(f"Errore durante il salvataggio: {e}")

    if st.button("Registra un altro atleta", use_container_width=True):
        reset_form(); st.rerun()

# --- AREA STAFF ---
with st.expander("🛠️ Area Staff"):
    pw = st.text_input("Password", type="password")
    if pw == PASSWORD_STAFF:
        df_staff = conn.read(spreadsheet=URL_FOGLIO, ttl=0)
        st.dataframe(df_staff)
