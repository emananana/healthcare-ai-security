"""Streamlit demo; run with streamlit run app.py."""
from dataclasses import asdict
import streamlit as st
from evaluation.runner import run_experiment
from orchestrator import Orchestrator
from security.auth import DEMO_USERS

st.set_page_config(page_title="Synthetic Insurance Security Lab", layout="wide")
st.title("Synthetic Insurance Security Lab")
st.caption("Educational mock simulation • synthetic records only • no LLM/API connection")
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()
    st.session_state.history = {}
orch = st.session_state.orchestrator
user = st.sidebar.selectbox("Demo identity (not authentication)", DEMO_USERS,
                            format_func=lambda u: f"{u.display_name} ({u.customer_id})")
chat, red, blue, audit, results = st.tabs([
    "Enterprise Chat", "Red Team", "Blue Team", "Security/Audit Log", "Experiment Results"])
with chat:
    st.write("Try: 'Show my policy', 'Show my claims', or 'Show claims for C002'.")
    history = st.session_state.history.setdefault(user.customer_id, [])
    message = st.chat_input("Ask about a synthetic policy or claim")
    if message:
        reply = orch.chat(user, message)
        history.extend([("user", message), ("assistant", reply.message)])
    for role, content in history:
        with st.chat_message(role):
            st.write(content)
with red:
    st.write("Fixed cross-customer request fixture; no advanced attack generation.")
    if st.button("Run mock attack"):
        target = "C002" if user.customer_id == "C001" else "C001"
        attack, response = orch.run_attack(user, {"target_customer_id": target})
        st.write(attack.message)
        st.write(response.message)
with blue:
    st.write("Mock recommendations. DECEIVE is reserved and treated as BLOCK.")
    st.json([{"event_id": e.event_id, **asdict(e.defense)} for e in orch.events() if e.defense])
with audit:
    st.caption("Session-local research log across demo identities; not a customer-facing production view.")
    st.json([asdict(e) for e in orch.events()])
with results:
    if st.button("Run baseline experiment"):
        st.session_state.experiment = run_experiment()
    if "experiment" in st.session_state:
        st.json(st.session_state.experiment["metrics"])
        st.dataframe(st.session_state.experiment["results"])
