import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Valutazione Atleta", page_icon="⚽", layout="centered")

# --- CONNESSIONE A GOOGLE SHEETS ---
# IMPORTANTE: Incolla qui il tuo URL completo che finisce con /edit
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1iNO4MNQCXHo9hBzOcBPzKR3xu1kt_E_w1eyQYQiqngw/edit?gid=0#gid=0"

# Pulizia automatica dell'URL
if "?" in URL_FOGLIO:
    URL_FOGLIO = URL_FOGLIO.split("?")[0]
if not URL_FOGLIO.endswith("/edit"):
    URL_FOGLIO = URL_FOGLIO.rstrip("/") + "/edit"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- STILE CSS AVANZATO ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .domanda-testo {
        font-size: 28px;
        font-weight: bold;
        color: #1e293b;
        margin-bottom: 30px;
        text-align: center;
        line-height: 1.3;
    }
    
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        overflow-x: auto;
        padding-top: 20px !important; 
        padding-bottom: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATI E CONFIGURAZIONI ---
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
st.markdown("---")

current_step = st.session_state.step

if current_step == 0:
    st.subheader("Benvenuto! Inserisci i tuoi dati.")
    st.session_state.nome_atleta = st.text_input("Nome e Cognome", value=st.session_state.nome_atleta, placeholder="Es: Mario Rossi")
    st.session_state.data_sessione = st.date_input("Data della sessione", value=st.session_state.data_sessione)
    if st.button("INIZIA TEST", type="primary", use_container_width=True):
        if not st.session_state.nome_atleta.strip(): st.error("⚠️ Inserisci il tuo nome.")
        else: avanti(); st.rerun()

elif 1 <= current_step <= len(domande):
    idx = current_step - 1
    st.write(f"Domanda {current_step} / {len(domande)}")
    st.markdown(f"<p class='domanda-testo'>{domande[idx]}</p>", unsafe_allow_html=True)
    
    chiave = f"q{idx}"
    scelto = st.session_state.risposte.get(chiave)
    cols = st.columns(5)
    
    for i in range(5):
        val = i + 1
        is_sel = (scelto == val)
        op = "1.0" if (scelto is None or is_sel) else "0.4"
        sc = "scale(1.2)" if is_sel else "scale(1.0)"
        brd = "border: 4px solid #1e293b;" if is_sel else ""
        
        with cols[i]:
            st.markdown(f"""
            <div style='background-color:{colori_bollini[i]}; border-radius:50%; width:55px; height:55px; 
                        display:flex; align-items:center; justify-content:center; font-size:30px; 
                        margin: 10px auto; transition: all 0.2s; opacity: {op}; transform: {sc}; {brd}'>
                <span>{faccine[i]}</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"{val}", key=f"b_{current_step}_{i}", use_container_width=True):
                st.session_state.risposte[chiave] = val
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    c_ind, c_spa, c_ava = st.columns([1, 1, 1])
    with c_ind: 
        if st.button("⬅️ Indietro", use_container_width=True): indietro(); st.rerun()
    with c_ava:
        if scelto:
            if st.button("AVANTI ➡️" if current_step < len(domande) else "FINALE 🏁", type="primary", use_container_width=True):
                avanti(); st.rerun()

elif current_step > len(domande):
    st.success(f"✅ Grazie {st.session_state.nome_atleta}! I tuoi dati sono in fase di salvataggio...")
    
    if 'salvato' not in st.session_state:
        try:
            # Creazione riga dati
            nuovi_dati = pd.DataFrame([{
                "data": st.session_state.data_sessione.strftime("%d/%m/%Y"),
                "nome": st.session_state.nome_atleta,
                "q1": st.session_state.risposte["q0"],
                "q2": st.session_state.risposte["q1"],
                "q3": st.session_state.risposte["q2"],
                "q4": st.session_state.risposte["q3"],
                "q5": st.session_state.risposte["q4"],
                "media": round(sum([st.session_state.risposte[f"q{i}"] for i in range(5)])/5, 2)
            }])
            
            # Lettura forzata senza cache (ttl=0) per vedere sempre l'ultimo inserimento
            df_esistente = conn.read(spreadsheet=URL_FOGLIO, ttl=0)
            
            # Pulizia e unione dei dati (previene la cancellazione dei precedenti)
            df_esistente = df_esistente.dropna(how='all')
            df_finale = pd.concat([df_esistente, nuovi_dati], ignore_index=True)
            
            # Scrittura su Google Sheets
            conn.update(spreadsheet=URL_FOGLIO, data=df_finale)
            
            st.session_state.salvato = True
            st.balloons()
            st.info("Dati salvati correttamente su Google Sheets!")
        except Exception as e:
            st.error(f"Errore durante il salvataggio: {e}")

    if st.button("Registra un altro atleta", use_container_width=True):
        reset_form(); st.rerun()

# --- AREA STAFF ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
with st.expander("🛠️ Area Staff"):
    pw = st.text_input("Password", type="password")
    if pw == PASSWORD_STAFF:
        try:
            # Lettura in tempo reale anche per l'area staff
            df_staff = conn.read(spreadsheet=URL_FOGLIO, ttl=0)
            st.dataframe(df_staff, use_container_width=True)
        except Exception as e:
            st.warning(f"Impossibile caricare i dati. Dettaglio errore: {e}")