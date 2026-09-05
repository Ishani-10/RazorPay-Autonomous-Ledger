import streamlit as st
import pandas as pd
import os
import sys

# Ensure the parent directory is in the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.generator import generate_synthetic_data
from core.engine import run_reconciliation

# ---------------------------------------------------------
# UI CONFIGURATION & STYLING (Dark, No-Nonsense, Sharp)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Autonomous Ledger | Razorpay",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ICPC / HFT Dark Theme CSS
# Sharp corners, monospaced fonts for data, pure black/dark grey backgrounds
dark_theme_css = """
<style>
    /* Global Backgrounds */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Inter', sans-serif;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Courier New', Courier, monospace;
        font-weight: bold;
        letter-spacing: -0.5px;
        text-transform: uppercase;
    }
    
    /* Metrics Box styling (Sharp corners, dark borders) */
    div[data-testid="metric-container"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 0px !important; /* SHARP CORNERS */
        padding: 15px;
        box-shadow: none;
    }
    
    /* Dataframes / Tables */
    .stDataFrame {
        font-family: 'Courier New', Courier, monospace;
        border-radius: 0px !important;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #21262d;
        color: #ffffff;
        border: 1px solid #f0f6fc;
        border-radius: 0px !important; /* SHARP CORNERS */
        font-family: 'Courier New', Courier, monospace;
        font-weight: bold;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #f0f6fc;
        color: #000000;
        border-color: #f0f6fc;
    }

    /* Badges / Tags */
    .badge-success { background-color: #238636; color: white; padding: 2px 6px; font-size: 12px; font-weight: bold; border: 1px solid #2ea043; }
    .badge-warning { background-color: #9e6a03; color: white; padding: 2px 6px; font-size: 12px; font-weight: bold; border: 1px solid #d29922; }
    .badge-danger  { background-color: #da3633; color: white; padding: 2px 6px; font-size: 12px; font-weight: bold; border: 1px solid #f85149; }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(dark_theme_css, unsafe_allow_html=True)

# ---------------------------------------------------------
# APPLICATION LOGIC
# ---------------------------------------------------------
st.title("SYS.LEDGER // AUTONOMOUS RECONCILIATION")
st.markdown("`TRACK 04 : AI FINANCE CONTROLLER` | `STATUS: ONLINE`")
st.markdown("---")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# State Management
if 'reconciliation_run' not in st.session_state:
    st.session_state.reconciliation_run = False
if 'results' not in st.session_state:
    st.session_state.results = []

col1, col2 = st.columns([1, 4])

with col1:
    st.markdown("### COMMAND CONTROLS")
    if st.button("1. GENERATE SYNTHETIC BATCH", use_container_width=True):
        with st.spinner("Injecting messy dataset..."):
            generate_synthetic_data(DATA_DIR)
        st.success("Batch Generated: 50 Records")
        
    if st.button("2. EXECUTE LEDGER PIPELINE", use_container_width=True):
        if not os.path.exists(os.path.join(DATA_DIR, "bank.csv")):
            st.error("Generate data first.")
        else:
            with st.spinner("Piping data through Layer 1 (Deterministic) and Layer 2 (AI)..."):
                st.session_state.results = run_reconciliation(DATA_DIR)
                st.session_state.reconciliation_run = True

with col2:
    if st.session_state.reconciliation_run:
        results = st.session_state.results
        
        # Calculate Metrics
        total = len(results)
        deterministic = sum(1 for r in results if r.match_type == "DETERMINISTIC")
        ai_resolved = sum(1 for r in results if r.match_type == "AI_RESOLVED")
        exceptions = sum(1 for r in results if r.match_type == "EXCEPTION")
        
        st.markdown("### EXECUTION METRICS")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(label="TOTAL PROCESSED", value=total)
        m2.metric(label="L1: DETERMINISTIC EXACT", value=deterministic)
        m3.metric(label="L2: AI RESOLVED", value=ai_resolved)
        m4.metric(label="L3: EXCEPTIONS CAUGHT", value=exceptions, delta="-Requires Review", delta_color="inverse")
        
        st.markdown("---")
        
        import sqlite3
        # Tabs for detailed views
        t1, t2, t3, t4 = st.tabs(["[ L3: HONEST EXCEPTION QUEUE ]", "[ L2: AI AUDIT TRAIL ]", "[ L1: DETERMINISTIC LOG ]", "[ SYSTEM: SQLITE DB ]"])
        
        with t4:
            st.markdown("#### RAW DATABASE STATE (`ledger.db`)")
            st.markdown("Unlike memory-based scripts, this system commits state changes to an ACID-compliant SQLite relational database.")
            st.markdown("🛡️ **Idempotency Active:** If you click *Execute Ledger* again, the database will ignore duplicate webhook events instead of double-processing them.")
            
            db_path = os.path.join(DATA_DIR, "ledger.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                df_db = pd.read_sql_query("SELECT bank_transaction_id, status, deposit_amount, order_id, match_type FROM ledger", conn)
                
                # Apply color styling based on status
                def color_status(val):
                    if val == 'RECONCILED':
                        return 'color: #238636; font-weight: bold;'
                    elif val == 'EXCEPTION':
                        return 'color: #da3633; font-weight: bold;'
                    return 'color: #d29922; font-weight: bold;'
                
                st.dataframe(df_db.style.applymap(color_status, subset=['status']), use_container_width=True)
                conn.close()
            else:
                st.write("Database not initialized yet.")
                
        with t1:
            st.markdown("#### EXCEPTIONS (BLOCKED BY MATH GUARDRAIL)")
            st.markdown("These transactions failed the Layer 3 verification. The AI was overridden due to financial discrepancy.")
            exc_data = [r for r in results if r.match_type == "EXCEPTION"]
            if exc_data:
                for e in exc_data:
                    st.markdown(f"""
                    <div style="border: 1px solid #f85149; padding: 10px; margin-bottom: 10px; background-color: #211414;">
                        <span class="badge-danger">EXCEPTION FLAG</span> 
                        <strong>BANK TXN:</strong> `{e.bank_transaction_id}` | 
                        <strong>EXPECTED:</strong> ₹{e.settled_amount} | 
                        <strong>ACTUAL DEPOSIT:</strong> ₹{e.bank_deposit_amount}
                        <br><br>
                        <span style="color:#ff7b72;">[REASONING LOG]:</span> {e.reasoning}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("No exceptions found in this batch.")
                
        with t2:
            st.markdown("#### AI RESOLUTION AUDIT (FUZZY MATCHES)")
            st.markdown("These transactions had missing IDs or garbage text. Layer 2 AI deduced the match by reverse-engineering fees.")
            st.markdown("🔒 *Note: All Personally Identifiable Information (PII) like names was dynamically masked before transmission to OpenAI.*")
            ai_data = [r for r in results if r.match_type == "AI_RESOLVED"]
            if ai_data:
                for a in ai_data:
                    st.markdown(f"""
                    <div style="border: 1px solid #d29922; padding: 10px; margin-bottom: 10px; background-color: #1a150c;">
                        <span class="badge-warning">AI RESOLVED</span> 
                        <strong>BANK TXN:</strong> `{a.bank_transaction_id}` -> 
                        <strong>LINKED ORDER:</strong> `{a.order_id}`
                        <br><br>
                        <span style="color:#d29922;">[AI REASONING]:</span> {a.reasoning}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("No AI resolutions required.")

        with t3:
            st.markdown("#### DETERMINISTIC EXACT MATCHES (NO AI)")
            st.markdown("These matched perfectly via standard string and float comparison. Zero LLM tokens wasted.")
            det_data = [r for r in results if r.match_type == "DETERMINISTIC"]
            
            if det_data:
                # Convert to dataframe for a clean table view
                df = pd.DataFrame([{
                    "BANK_TXN": d.bank_transaction_id,
                    "ORDER_ID": d.order_id,
                    "PAYMENT_ID": d.payment_id,
                    "AMOUNT": f"₹{d.bank_deposit_amount}"
                } for d in det_data])
                
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.write("No deterministic matches found.")

    else:
        st.info("System idle. Awaiting command.")
