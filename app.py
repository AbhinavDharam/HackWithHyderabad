"""
RecallOps: Incident Command Center
Enterprise Operational Incident Response Engine with Real-Time Telemetry & Hindsight Persistent Memory
"""
import os
import streamlit as st
import json
import time
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from recallops.config import HINDSIGHT_BANK_ID, HINDSIGHT_BASE_URL, GROQ_MODEL
from recallops.models.incident import Incident, ActionAttempt, ActionOutcome, Severity, IncidentMetric, IncidentTrigger
from recallops.memory.hindsight_adapter import HindsightAdapter
from recallops.incidents.incident_manager import IncidentManager
from recallops.agent.sre_agent import SREAgent
from recallops.llm.llm_client import LLMClient

# Page Configuration
st.set_page_config(
    page_title="RecallOps — Enterprise Incident Command",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# High-End Enterprise SRE Theme (Datadog / Rootly / Linear Aesthetic)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .stApp {
        background-color: #070b14;
        color: #f1f5f9;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 3.5rem;
        max-width: 1420px;
    }

    /* Enterprise Navigation Header */
    .cmd-header {
        background: linear-gradient(180deg, #0e1626 0%, #0a0f1d 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 14px 20px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
    }
    .cmd-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .cmd-title {
        font-size: 20px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #ffffff;
    }
    .cmd-tag {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        padding: 2px 8px;
        border-radius: 4px;
        background: rgba(56, 189, 248, 0.12);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .cmd-meta {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .live-pulse {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        font-weight: 700;
        color: #f87171;
        background: rgba(239, 68, 68, 0.12);
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 3px 10px;
        border-radius: 20px;
        letter-spacing: 0.3px;
    }
    .live-pulse-green {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        font-weight: 700;
        color: #34d399;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 3px 10px;
        border-radius: 20px;
        letter-spacing: 0.3px;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #ef4444;
        box-shadow: 0 0 8px #ef4444;
    }
    .pulse-dot-green {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981;
    }
    .meta-pill {
        font-size: 12px;
        font-weight: 500;
        color: #94a3b8;
        background: #0f172a;
        border: 1px solid #1e293b;
        padding: 3px 10px;
        border-radius: 6px;
    }

    /* Workflow Stage Progress Tracker */
    .stepper-bar {
        display: flex;
        align-items: center;
        background-color: #0b1120;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 8px 16px;
        margin-bottom: 24px;
        gap: 8px;
        overflow-x: auto;
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        font-weight: 600;
        color: #64748b;
        padding: 4px 10px;
        border-radius: 6px;
        white-space: nowrap;
    }
    .step-item.active {
        color: #38bdf8;
        background: rgba(14, 165, 233, 0.1);
        border: 1px solid rgba(14, 165, 233, 0.25);
    }
    .step-badge {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        font-weight: 700;
    }
    .step-item.active .step-badge {
        background-color: #0284c7;
        color: #ffffff;
    }
    .step-arrow {
        color: #334155;
        font-size: 11px;
    }

    /* Section Cards & Headers */
    .section-container {
        background-color: #0c1222;
        border: 1px solid #1b263b;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 24px;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
    }
    .section-header-wrap {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #1a2538;
        padding-bottom: 12px;
        margin-bottom: 16px;
    }
    .section-title {
        font-size: 17px;
        font-weight: 700;
        letter-spacing: -0.3px;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .section-index {
        width: 24px;
        height: 24px;
        border-radius: 6px;
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
        color: #ffffff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 800;
    }
    .section-subtitle {
        font-size: 13px;
        color: #94a3b8;
        font-weight: 400;
    }

    /* Incident Overview Hero */
    .incident-hero {
        background: linear-gradient(180deg, #111a2f 0%, #0d1424 100%);
        border: 1px solid #1f2e4a;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 16px;
    }
    .hero-topline {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
    }
    .sev-pill {
        font-size: 11px;
        font-weight: 800;
        padding: 3px 10px;
        border-radius: 4px;
        letter-spacing: 0.6px;
        text-transform: uppercase;
    }
    .sev-critical {
        background: rgba(239, 68, 68, 0.18);
        color: #f87171;
        border: 1px solid #dc2626;
    }
    .sev-mitigated {
        background: rgba(16, 185, 129, 0.18);
        color: #34d399;
        border: 1px solid #059669;
    }
    .service-pill {
        font-size: 11px;
        font-weight: 600;
        background: rgba(139, 92, 246, 0.15);
        color: #c084fc;
        border: 1px solid #7c3aed;
        padding: 3px 9px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
    }
    .status-pill {
        font-size: 11px;
        font-weight: 700;
        background: rgba(244, 63, 94, 0.12);
        color: #fda4af;
        border: 1px solid #f43f5e;
        padding: 3px 9px;
        border-radius: 4px;
        text-transform: uppercase;
    }
    .status-pill-green {
        font-size: 11px;
        font-weight: 700;
        background: rgba(16, 185, 129, 0.12);
        color: #a7f3d0;
        border: 1px solid #10b981;
        padding: 3px 9px;
        border-radius: 4px;
        text-transform: uppercase;
    }
    .hero-heading {
        font-size: 21px;
        font-weight: 800;
        color: #ffffff;
        margin: 6px 0;
        letter-spacing: -0.4px;
    }
    .hero-desc {
        font-size: 13.5px;
        color: #94a3b8;
        line-height: 1.5;
        margin: 0;
    }

    /* Metric KPI Cards with Progress Meters */
    .metric-card {
        background: #0d1424;
        border: 1px solid #1a2742;
        border-radius: 8px;
        padding: 14px 16px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }
    .metric-name {
        font-size: 11px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }
    .metric-val {
        font-size: 26px;
        font-weight: 800;
        color: #ffffff;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.5px;
    }
    .metric-sub {
        font-size: 12px;
        font-weight: 600;
        margin-top: 2px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .delta-red { color: #f87171; }
    .delta-amber { color: #fbbf24; }
    .delta-green { color: #34d399; }
    .metric-bar-bg {
        width: 100%;
        height: 4px;
        background: #1e293b;
        border-radius: 2px;
        margin-top: 10px;
        overflow: hidden;
    }
    .metric-bar-fill {
        height: 100%;
        border-radius: 2px;
    }

    /* Architecture / Blast Radius Strip */
    .topology-strip {
        background: #090e1a;
        border: 1px solid #1a263e;
        border-radius: 6px;
        padding: 10px 14px;
        margin-top: 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 12.5px;
        color: #cbd5e1;
    }
    .topo-node {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #131c30;
        border: 1px solid #233454;
        padding: 4px 10px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11.5px;
    }
    .topo-arrow {
        color: #475569;
        font-size: 13px;
        font-weight: 700;
    }

    /* Precedent Card (Step 2) */
    .precedent-card {
        background: linear-gradient(180deg, #0e172a 0%, #0a0f1d 100%);
        border: 1px solid #1e2e4a;
        border-left: 4px solid #0284c7;
        border-radius: 8px;
        padding: 18px 20px;
        margin-bottom: 14px;
    }
    .precedent-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .precedent-title {
        font-size: 16px;
        font-weight: 700;
        color: #ffffff;
    }
    .match-tag {
        background: rgba(14, 165, 233, 0.15);
        color: #38bdf8;
        border: 1px solid #0284c7;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.6px;
        padding: 3px 10px;
        border-radius: 4px;
        text-transform: uppercase;
    }
    .evidence-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin: 14px 0 6px 0;
    }
    .evidence-cell {
        background: #090e1a;
        border: 1px solid #182338;
        border-radius: 6px;
        padding: 10px 12px;
    }
    .evidence-label {
        font-size: 10.5px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .evidence-val {
        font-size: 12.5px;
        color: #e2e8f0;
        font-weight: 500;
    }

    /* Learnings Panels (Step 3) */
    .card-anti-pattern {
        background: linear-gradient(180deg, rgba(225, 29, 72, 0.08) 0%, rgba(225, 29, 72, 0.02) 100%);
        border: 1px solid rgba(225, 29, 72, 0.25);
        border-left: 4px solid #e11d48;
        border-radius: 8px;
        padding: 16px;
        height: 100%;
    }
    .card-verified {
        background: linear-gradient(180deg, rgba(16, 185, 129, 0.08) 0%, rgba(16, 185, 129, 0.02) 100%);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-left: 4px solid #10b981;
        border-radius: 8px;
        padding: 16px;
        height: 100%;
    }
    .action-row {
        background: #090e1a;
        border: 1px solid #182338;
        border-radius: 6px;
        padding: 10px 12px;
        margin-bottom: 10px;
    }
    .action-row-title {
        font-size: 13.5px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .action-row-desc {
        font-size: 12.5px;
        line-height: 1.45;
    }

    /* Reasoning Layer Trace (Step 4) */
    .reasoning-box {
        background: #090e1a;
        border: 1px solid #182338;
        border-radius: 6px;
        padding: 12px 14px;
        margin-bottom: 8px;
    }
    .reasoning-pill {
        display: inline-block;
        font-size: 10.5px;
        font-weight: 800;
        letter-spacing: 0.5px;
        padding: 2px 7px;
        border-radius: 3px;
        margin-right: 8px;
        text-transform: uppercase;
        font-family: 'JetBrains Mono', monospace;
    }
    .pill-observed { background: #1e293b; color: #f1f5f9; border: 1px solid #334155; }
    .pill-history { background: rgba(14, 165, 233, 0.2); color: #38bdf8; border: 1px solid #0284c7; }
    .pill-inference { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #d97706; }
    .pill-rec { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #059669; }

    /* Diagnostic Terminal */
    .terminal-window {
        background: #050811;
        border: 1px solid #1b263b;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 12px;
    }
    .terminal-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #151e30;
        padding-bottom: 6px;
        margin-bottom: 8px;
        font-size: 11px;
        color: #64748b;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Retention Payload (Step 5) */
    .retention-summary {
        background: #0a0f1d;
        border: 1px solid #1a2742;
        border-left: 4px solid #10b981;
        border-radius: 8px;
        padding: 16px 18px;
        height: 100%;
    }
    .retention-item {
        margin-bottom: 10px;
        font-size: 13px;
        line-height: 1.5;
        color: #cbd5e1;
    }

    /* Live Log Console */
    .log-stream-box {
        background: #050811;
        border: 1px solid #151e30;
        border-radius: 6px;
        padding: 10px 14px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11.5px;
        color: #94a3b8;
        max-height: 160px;
        overflow-y: auto;
        line-height: 1.6;
    }
    .log-line {
        display: block;
        margin-bottom: 2px;
    }
    .log-crit { color: #f87171; }
    .log-warn { color: #fbbf24; }
    .log-info { color: #38bdf8; }
    .log-success { color: #34d399; }

    /* Streamlit Form & Controls Overrides */
    div[role="radiogroup"] {
        display: flex !important;
        background-color: #0b1120 !important;
        border: 1px solid #1e293b !important;
        border-radius: 6px !important;
        padding: 3px !important;
        gap: 4px !important;
    }
    div[role="radiogroup"] > label {
        background-color: transparent !important;
        border-radius: 4px !important;
        padding: 4px 12px !important;
        margin: 0 !important;
        cursor: pointer !important;
        color: #94a3b8 !important;
        font-size: 12.5px !important;
        font-weight: 600 !important;
    }
    div[role="radiogroup"] > label:hover {
        color: #ffffff !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
    }

    /* Primary CTA Buttons */
    div.stButton > button, div.stFormSubmitButton > button {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        letter-spacing: 0.3px !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 6px !important;
        padding: 12px 24px !important;
        box-shadow: 0 4px 16px rgba(2, 132, 199, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #0369a1 0%, #1d4ed8 100%) !important;
        box-shadow: 0 6px 22px rgba(2, 132, 199, 0.45) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }
    
    pre, code {
        font-family: 'JetBrains Mono', monospace !important;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Adapters & Services
@st.cache_resource
def get_adapters():
    mem_adapter = HindsightAdapter()
    inc_manager = IncidentManager(memory_adapter=mem_adapter)
    llm = LLMClient()
    agent = SREAgent(memory_adapter=mem_adapter, llm_client=llm)
    return mem_adapter, inc_manager, agent, llm

mem_adapter, inc_manager, agent, llm = get_adapters()

# Session State for Real-Time Simulation
if "ran_diagnostic" not in st.session_state:
    st.session_state["ran_diagnostic"] = False
if "remediation_executed" not in st.session_state:
    st.session_state["remediation_executed"] = False

# Enterprise Navigation Sidebar
with st.sidebar:
    st.image("assets/logo.png", width=180)
    st.markdown("""
    <div style="font-size:12px; color:#64748b; font-weight:600; text-transform:uppercase; letter-spacing:0.8px; margin-top:2px;">
        Operational Incident Memory
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Active Incident Switcher
    all_incidents = inc_manager.get_all()
    inc_options = {f"[{i.incident_id}] {i.title}": i.incident_id for i in all_incidents}
    
    default_idx = 0
    for idx, (label, iid) in enumerate(inc_options.items()):
        if iid == "INC-105":
            default_idx = idx
            break

    st.markdown("<span style='font-size:12px; font-weight:700; color:#94a3b8; text-transform:uppercase;'>Incident Catalog</span>", unsafe_allow_html=True)
    selected_label = st.selectbox("Select Active Outage:", list(inc_options.keys()), index=default_idx, label_visibility="collapsed")
    selected_id = inc_options[selected_label]
    current_incident = inc_manager.get_by_id(selected_id)

    # Reset live simulation state if incident changes
    if "current_incident_id" not in st.session_state or st.session_state["current_incident_id"] != selected_id:
        st.session_state["current_incident_id"] = selected_id
        st.session_state["ran_diagnostic"] = False
        st.session_state["remediation_executed"] = False

    st.markdown("---")

    # Real-Time Controls
    st.markdown("<span style='font-size:12px; font-weight:700; color:#94a3b8; text-transform:uppercase;'>Real-Time Simulation</span>", unsafe_allow_html=True)
    if st.session_state["remediation_executed"]:
        st.success("Remediation Active: Latency Normalized")
        if st.button("↺ Reset Outage State (Re-run Demo)", use_container_width=True):
            st.session_state["ran_diagnostic"] = False
            st.session_state["remediation_executed"] = False
            st.rerun()
    else:
        st.caption("Status: Critical Outage in Progress")

    st.markdown("---")

    # Institutional Memory Bank Health
    stats = mem_adapter.get_stats()
    st.markdown("<span style='font-size:12px; font-weight:700; color:#94a3b8; text-transform:uppercase;'>Hindsight Memory Bank</span>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:#0b1120; border:1px solid #1e293b; border-radius:6px; padding:12px; margin-top:6px;">
        <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:6px;">
            <span style="color:#94a3b8;">Indexed Memories:</span>
            <span style="color:#f8fafc; font-weight:700; font-family:'JetBrains Mono';">{stats['total_memories']} records</span>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:6px;">
            <span style="color:#94a3b8;">Learned Outcomes:</span>
            <span style="color:#38bdf8; font-weight:700; font-family:'JetBrains Mono';">{stats['action_experiences']} actions</span>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:8px;">
            <span style="color:#94a3b8;">Runbook Rules:</span>
            <span style="color:#34d399; font-weight:700; font-family:'JetBrains Mono';">{stats['lessons_and_antipatterns']} rules</span>
        </div>
        <div style="font-size:11px; color:#10b981; display:flex; align-items:center; gap:6px;">
            <span style="width:6px; height:6px; background:#10b981; border-radius:50%;"></span>
            Hindsight Vault Online (recallops-vault)
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    with st.expander("API Keys & Hindsight Integration", expanded=False):
        has_groq = bool(llm.groq_client)
        has_hs_cloud = bool(mem_adapter.client)
        
        st.markdown(f"**Groq LLM:** {'🟢 Connected (Live)' if has_groq else '🟡 Fallback Engine'}")
        input_groq = st.text_input("Groq API Key:", value=os.getenv("GROQ_API_KEY", ""), type="password", placeholder="gsk_...", help="From https://console.groq.com")
        if input_groq and input_groq != os.getenv("GROQ_API_KEY", ""):
            os.environ["GROQ_API_KEY"] = input_groq
            st.cache_resource.clear()
            st.rerun()

        st.markdown(f"**Hindsight Memory:** {'🟢 Cloud Connected' if has_hs_cloud else '🟢 Local Vault (18 records)'}")
        input_hs = st.text_input("Hindsight API Key:", value=os.getenv("HINDSIGHT_API_KEY", ""), type="password", placeholder="hs_...", help="From https://ui.hindsight.vectorize.io (Promo: MEMHACK99)")
        if input_hs and input_hs != os.getenv("HINDSIGHT_API_KEY", ""):
            os.environ["HINDSIGHT_API_KEY"] = input_hs
            st.cache_resource.clear()
            st.rerun()
            
        st.caption(f"Bank ID: `{stats['bank_id']}` | Model: `{GROQ_MODEL}`")
        if st.button("Reset Baseline Memory", use_container_width=True):
            from seed_memory import seed_memory_bank
            seed_memory_bank()
            st.rerun()


if not current_incident:
    st.error("Incident not found.")
    st.stop()

# State-dependent values
is_recovered = st.session_state["remediation_executed"]

# =========================================================================
# GLOBAL ENTERPRISE SRE COMMAND BAR
# =========================================================================
status_beacon_html = f"""
<span class="live-pulse-green">
    <span class="pulse-dot-green"></span>
    MITIGATED / RECOVERED
</span>
""" if is_recovered else f"""
<span class="live-pulse">
    <span class="pulse-dot"></span>
    LIVE OUTAGE IN PROGRESS
</span>
"""

st.markdown(f"""
<div class="cmd-header">
    <div class="cmd-brand">
        <span class="cmd-title">RecallOps</span>
        <span class="cmd-tag">Enterprise SRE</span>
        <span style="color:#475569; font-size:14px;">/</span>
        <span class="meta-pill" style="font-family:'JetBrains Mono'; font-weight:600; color:#38bdf8;">
            prod-aws-eu-west-1 &bull; {current_incident.affected_service}
        </span>
    </div>
    <div class="cmd-meta">
        {status_beacon_html}
        <span class="meta-pill" style="font-family:'JetBrains Mono'; font-weight:700; color:#ffffff;">
            {current_incident.incident_id}
        </span>
        <span class="meta-pill" style="color:#cbd5e1;">
            {"19m Total Recovery Duration" if is_recovered else "Triggered 18m ago (Active)"}
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# 5-Stage Visual Workflow Stepper
st.markdown("""
<div class="stepper-bar">
    <div class="step-item active">
        <span class="step-badge">1</span> What's Happening?
    </div>
    <span class="step-arrow">&rarr;</span>
    <div class="step-item active">
        <span class="step-badge">2</span> Have We Seen This?
    </div>
    <span class="step-arrow">&rarr;</span>
    <div class="step-item active">
        <span class="step-badge">3</span> Team Learnings
    </div>
    <span class="step-arrow">&rarr;</span>
    <div class="step-item active">
        <span class="step-badge">4</span> What to Investigate
    </div>
    <span class="step-arrow">&rarr;</span>
    <div class="step-item active">
        <span class="step-badge">5</span> Ingest to Memory
    </div>
</div>
""", unsafe_allow_html=True)


# =========================================================================
# 1. WHAT'S HAPPENING? (INCIDENT TELEMETRY & SYSTEM TOPOLOGY)
# =========================================================================
st.markdown("""
<div class="section-container">
    <div class="section-header-wrap">
        <div>
            <div class="section-title">
                <span class="section-index">1</span>
                What's happening?
            </div>
            <div class="section-subtitle">Real-time incident classification, live telemetry stream, and topology blast radius.</div>
        </div>
    </div>
""", unsafe_allow_html=True)

sev_val = current_incident.severity.value if hasattr(current_incident.severity, 'value') else current_incident.severity
sev_class = "sev-mitigated" if is_recovered else ("sev-critical" if "SEV-1" in sev_val else "sev-warning")
status_label = "RECOVERED" if is_recovered else current_incident.status
status_class = "status-pill-green" if is_recovered else "status-pill"

st.markdown(f"""
<div class="incident-hero">
    <div class="hero-topline">
        <span class="sev-pill {sev_class}">{sev_val}</span>
        <span class="{status_class}">{status_label}</span>
        <span class="service-pill">{current_incident.affected_service}</span>
    </div>
    <div class="hero-heading">[{current_incident.incident_id}] {current_incident.title}</div>
    <p class="hero-desc">
        {"Production performance has been restored to normal baseline following targeted PID lock termination." if is_recovered else f"Production service <b>{current_incident.affected_service}</b> is suffering critical p99 degradation and elevated 504 gateway drops following recent deployment activities. Customer transactions are timing out at payment checkout."}
    </p>
</div>
""", unsafe_allow_html=True)

# 4 High-Density Metric Cards
c_m1, c_m2, c_m3, c_m4 = st.columns(4)

with c_m1:
    if is_recovered:
        st.markdown("""
        <div class="metric-card">
            <div>
                <div class="metric-header">
                    <span class="metric-name">P99 API Latency</span>
                    <span style="font-size:11px; color:#34d399; font-weight:700;">NORMALIZED</span>
                </div>
                <div class="metric-val" style="color:#34d399;">210 ms</div>
                <div class="metric-sub delta-green">
                    <span>&check; Baseline restored (Threshold: 500ms)</span>
                </div>
            </div>
            <div class="metric-bar-bg">
                <div class="metric-bar-fill" style="width: 22%; background: #10b981;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <div>
                <div class="metric-header">
                    <span class="metric-name">P99 API Latency</span>
                    <span style="font-size:11px; color:#f87171; font-weight:700;">CRITICAL</span>
                </div>
                <div class="metric-val">4.92s</div>
                <div class="metric-sub delta-red">
                    <span>&uarr; 4,710ms vs baseline (210ms)</span>
                </div>
            </div>
            <div class="metric-bar-bg">
                <div class="metric-bar-fill" style="width: 96%; background: #ef4444;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with c_m2:
    if is_recovered:
        st.markdown("""
        <div class="metric-card">
            <div>
                <div class="metric-header">
                    <span class="metric-name">504 Error Rate</span>
                    <span style="font-size:11px; color:#34d399; font-weight:700;">ZERO DROPS</span>
                </div>
                <div class="metric-val" style="color:#34d399;">0.01%</div>
                <div class="metric-sub delta-green">
                    <span>&check; Healthy ingress (Baseline: 0.05%)</span>
                </div>
            </div>
            <div class="metric-bar-bg">
                <div class="metric-bar-fill" style="width: 2%; background: #10b981;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <div>
                <div class="metric-header">
                    <span class="metric-name">504 Error Rate</span>
                    <span style="font-size:11px; color:#f87171; font-weight:700;">HIGH SPIKE</span>
                </div>
                <div class="metric-val">14.2%</div>
                <div class="metric-sub delta-red">
                    <span>&uarr; +14.15% vs baseline (0.05%)</span>
                </div>
            </div>
            <div class="metric-bar-bg">
                <div class="metric-bar-fill" style="width: 78%; background: #f43f5e;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with c_m3:
    if is_recovered:
        st.markdown("""
        <div class="metric-card">
            <div>
                <div class="metric-header">
                    <span class="metric-name">DB Pool Saturation</span>
                    <span style="font-size:11px; color:#34d399; font-weight:700;">HEALTHY</span>
                </div>
                <div class="metric-val" style="color:#34d399;">22%</div>
                <div class="metric-sub delta-green">
                    <span>&check; 11 / 50 active client pools</span>
                </div>
            </div>
            <div class="metric-bar-bg">
                <div class="metric-bar-fill" style="width: 22%; background: #10b981;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <div>
                <div class="metric-header">
                    <span class="metric-name">DB Pool Saturation</span>
                    <span style="font-size:11px; color:#fbbf24; font-weight:700;">STARVATION</span>
                </div>
                <div class="metric-val">88%</div>
                <div class="metric-sub delta-amber">
                    <span>&uarr; 44 / 50 active client pools</span>
                </div>
            </div>
            <div class="metric-bar-bg">
                <div class="metric-bar-fill" style="width: 88%; background: #f59e0b;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with c_m4:
    st.markdown("""
    <div class="metric-card">
        <div>
            <div class="metric-header">
                <span class="metric-name">Deployment Trigger</span>
                <span style="font-size:11px; color:#38bdf8; font-weight:700;">RELEASE</span>
            </div>
            <div class="metric-val" style="font-size:22px; color:#38bdf8;">v2.4.5</div>
            <div class="metric-sub" style="color:#94a3b8;">
                <span>Deployed 18m prior to alert (commit: 8f2a9c1)</span>
            </div>
        </div>
        <div class="metric-bar-bg">
            <div class="metric-bar-fill" style="width: 100%; background: #0284c7;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Architecture Blast Radius Strip
node_status_style = "border-color:#10b981; color:#a7f3d0;" if is_recovered else "border-color:#f43f5e; color:#fca5a5;"
node_status_text = "checkout-service [4 PODS / HEALTHY]" if is_recovered else "checkout-service [4 PODS / DEGRADED]"
pool_status_style = "border-color:#10b981; color:#a7f3d0;" if is_recovered else "border-color:#f59e0b; color:#fde68a;"
pool_status_text = "pgbouncer-pool [22% / HEALTHY]" if is_recovered else "pgbouncer-pool [88% SATURATED]"

st.markdown(f"""
<div class="topology-strip">
    <span style="font-weight:700; color:#94a3b8; font-size:11px; text-transform:uppercase;">Topology Blast Radius:</span>
    <span class="topo-node">api-gateway (eu-west-1)</span>
    <span class="topo-arrow">&xrarr;</span>
    <span class="topo-node" style="{node_status_style}">{node_status_text}</span>
    <span class="topo-arrow">&xrarr;</span>
    <span class="topo-node" style="{pool_status_style}">{pool_status_text}</span>
    <span class="topo-arrow">&xrarr;</span>
    <span class="topo-node">postgres-primary (db.r6g.2xlarge)</span>
</div>
""", unsafe_allow_html=True)

# Real-Time Telemetry Time-Series Charts
st.write("")
st.markdown("<span style='font-size:12px; font-weight:700; color:#94a3b8; text-transform:uppercase;'>Real-Time Telemetry Curve (30-Minute Window):</span>", unsafe_allow_html=True)

time_points = [f"T-{30-i}m" for i in range(30)]
np.random.seed(42)

if not is_recovered:
    lat_data = [int(210 + np.random.randint(-15, 20)) for _ in range(12)] + [int(4920 + np.random.randint(-70, 90)) for _ in range(18)]
    pool_data = [int(22 + np.random.randint(-2, 3)) for _ in range(12)] + [int(88 + np.random.randint(-3, 4)) for _ in range(18)]
else:
    lat_data = [int(210 + np.random.randint(-15, 20)) for _ in range(12)] + [int(4920 + np.random.randint(-70, 90)) for _ in range(14)] + [1850, 640, 240, 210]
    pool_data = [int(22 + np.random.randint(-2, 3)) for _ in range(12)] + [int(88 + np.random.randint(-3, 4)) for _ in range(14)] + [58, 34, 24, 22]

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    df_lat = pd.DataFrame({"P99 Latency (ms)": lat_data}, index=time_points)
    st.line_chart(df_lat, height=190, use_container_width=True)
    st.caption("P99 API Latency Curve (Critical Threshold: 500ms)")

with chart_col2:
    df_pool = pd.DataFrame({"DB Pool Saturation (%)": pool_data}, index=time_points)
    st.line_chart(df_pool, height=190, use_container_width=True)
    st.caption("Database Connection Pool Utilization (Warning Ceiling: 75%)")

# Live Operational Event Feed
with st.expander("Live Operational Event Stream & Telemetry Log", expanded=False):
    log_rows = [
        "<span class='log-line log-info'>[18:36:02.100] [DEPLOYMENT] Automated Canary deployment complete: release v2.4.5 rolled out to checkout-service pods.</span>",
        "<span class='log-line log-warn'>[18:36:12.402] [PGBOUNCER] Warning: Connection pool active count breached 80% (41/50).</span>",
        "<span class='log-line log-crit'>[18:36:14.881] [CHECKOUT-POD-3] Connection pool acquire timeout after 5000ms: PgBouncer pool ceiling reached.</span>",
        "<span class='log-line log-crit'>[18:36:18.120] [GATEWAY] HTTP 504 Gateway Timeout on POST /api/v2/checkout/pay (4,921ms).</span>",
        "<span class='log-line log-info'>[18:36:20.450] [RECALLOPS-AGENT] Incident detected: P99 latency breached SLA. Initiating Hindsight vector retrieval.</span>"
    ]
    if is_recovered:
        log_rows.append("<span class='log-line log-success'>[18:36:44.200] [REMEDIATION] Terminated blocking query PID 48219 via pg_terminate_backend.</span>")
        log_rows.append("<span class='log-line log-success'>[18:36:46.800] [PGBOUNCER] Active connection pool queue cleared: 44 -> 18 active connections.</span>")
        log_rows.append("<span class='log-line log-success'>[18:36:48.110] [GATEWAY] Ingress latency restored: HTTP 200 OK across all pods (p99: 210ms).</span>")
    
    st.markdown(f"""
    <div class="log-stream-box">
        {"".join(log_rows)}
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)


# =========================================================================
# 2. HAVE WE SEEN THIS BEFORE? (HISTORICAL RECALL)
# =========================================================================
st.markdown("""
<div class="section-container">
""", unsafe_allow_html=True)

col_s2_left, col_s2_right = st.columns([3, 1])

with col_s2_left:
    st.markdown("""
    <div class="section-title">
        <span class="section-index">2</span>
        Have we seen this before?
    </div>
    <div class="section-subtitle">Institutional experience retrieved from Hindsight memory bank matching active outage signals.</div>
    """, unsafe_allow_html=True)

with col_s2_right:
    memory_mode = st.radio(
        "Team Memory:",
        ["WITH TEAM MEMORY", "WITHOUT MEMORY"],
        format_func=lambda x: "ON (Team Memory)" if x == "WITH TEAM MEMORY" else "OFF (Generic AI)",
        horizontal=True,
        help="Compare RecallOps institutional memory vs standard generic unassisted AI."
    )

is_memory_enabled = (memory_mode == "WITH TEAM MEMORY")

# Run Agent Reasoning
historical_pool = inc_manager.get_historical_pool()
agent_mode_internal = "WITH_HINDSIGHT_MEMORY" if is_memory_enabled else "WITHOUT_MEMORY"

report = agent.investigate(
    incident=current_incident,
    mode=agent_mode_internal,
    historical_pool=historical_pool
)

if is_memory_enabled:
    st.markdown("""
    <div class="precedent-card">
        <div class="precedent-top">
            <div>
                <span style="font-size:12px; font-weight:700; color:#38bdf8; text-transform:uppercase; letter-spacing:0.8px;">Historical Precedent Confirmed</span>
                <div class="precedent-title">INC-101: Checkout API / Post-release latency surge / Database connection pool exhaustion</div>
            </div>
            <span class="match-tag">STRONG HISTORICAL MATCH</span>
        </div>
        <div style="font-size:13px; color:#cbd5e1; margin-bottom:8px;">
            RecallOps matched active telemetry against <b>18 institutional memories</b> in 9.2ms. Found identical precedent from <b>August 14</b>:
        </div>
        <div class="evidence-grid">
            <div class="evidence-cell">
                <div class="evidence-label">Affected Component</div>
                <div class="evidence-val">&check; <b>checkout-service</b> (100% match)</div>
            </div>
            <div class="evidence-cell">
                <div class="evidence-label">Failure Signature</div>
                <div class="evidence-val">&check; <b>p99 &gt; 4,500ms + 504 drops</b></div>
            </div>
            <div class="evidence-cell">
                <div class="evidence-label">Trigger Vector</div>
                <div class="evidence-val">&check; <b>&lt; 20m post-deployment</b></div>
            </div>
            <div class="evidence-cell">
                <div class="evidence-label">Resource Pattern</div>
                <div class="evidence-val">&check; <b>DB pool exhaustion (88% vs 100%)</b></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Historical Incident Precedents in Catalog"):
        st.markdown("- **INC-101:** `checkout-service` &mdash; Database connection pool lock exhaustion (Recovered in 24m)")
        st.markdown("- **INC-102:** `inventory-service` &mdash; Redis Cache Stampede under flash traffic (Recovered in 39m)")
        st.markdown("- **INC-104:** `payment-service` &mdash; Webhook Ingestion Thread Starvation (Recovered in 45m)")

else:
    st.markdown("""
    <div class="precedent-card" style="border-left: 4px solid #64748b;">
        <div class="precedent-top">
            <div>
                <span style="font-size:12px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.8px;">Unassisted Generic AI Mode</span>
                <div class="precedent-title">No Institutional Memory Accessed</div>
            </div>
            <span class="meta-pill">COLD START</span>
        </div>
        <p style="font-size:13.5px; color:#94a3b8; margin: 8px 0 0 0;">
            Operating without access to team memory or historical incident catalogs. The assistant must reason from first-principles heuristics alone and cannot warn against past team mistakes.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)


# =========================================================================
# 3. WHAT DID THE TEAM LEARN? (ANTI-PATTERNS VS VERIFIED MITIGATION)
# =========================================================================
st.markdown("""
<div class="section-container">
    <div class="section-header-wrap">
        <div>
            <div class="section-title">
                <span class="section-index">3</span>
                What did the team learn?
            </div>
            <div class="section-subtitle">Real historical experience from INC-101: costly anti-patterns to avoid vs proven recovery playbooks.</div>
        </div>
    </div>
""", unsafe_allow_html=True)

if is_memory_enabled:
    c_lrn1, c_lrn2 = st.columns(2)

    with c_lrn1:
        st.markdown("""
        <div class="card-anti-pattern">
            <div style="font-size:13px; font-weight:800; color:#f87171; text-transform:uppercase; letter-spacing:0.6px; margin-bottom:12px;">
                &cross; What Engineers Tried That FAILED (Anti-Patterns)
            </div>
            <div class="action-row">
                <div class="action-row-title" style="color:#f87171;">Anti-Pattern 1: Scaled pod deployment replicas from 4 to 12</div>
                <div class="action-row-desc" style="color:#fecdd3;">
                    <b>Impact:</b> Severe Failure &mdash; Each new pod opened 25 client pool connections, crashing PgBouncer, resetting active sockets, and worsening p99 latency to <b>8.2s</b>.
                </div>
            </div>
            <div class="action-row">
                <div class="action-row-title" style="color:#f87171;">Anti-Pattern 2: Increased API gateway timeout from 5s to 15s</div>
                <div class="action-row-desc" style="color:#fecdd3;">
                    <b>Impact:</b> Failed &mdash; Client requests accumulated in gateway queues, causing upstream worker thread pool starvation and memory exhaustion.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_lrn2:
        st.markdown("""
        <div class="card-verified">
            <div style="font-size:13px; font-weight:800; color:#34d399; text-transform:uppercase; letter-spacing:0.6px; margin-bottom:12px;">
                &check; What ACTUALLY Worked & Confirmed Root Cause
            </div>
            <div class="action-row">
                <div class="action-row-title" style="color:#34d399;">Verified Action 1: Terminated blocking lock query PID</div>
                <div class="action-row-desc" style="color:#a7f3d0;">
                    <b>Outcome:</b> Immediate Recovery &mdash; The active connection queue drained from 100 to 28; p99 latency returned to <b>210ms in 90 seconds</b>.
                </div>
            </div>
            <div class="action-row">
                <div class="action-row-title" style="color:#34d399;">Verified Action 2: Capped per-pod client pool limit to 8</div>
                <div class="action-row-desc" style="color:#a7f3d0;">
                    <b>Outcome:</b> Permanently prevented pod scale-out from exhausting shared database connection pools.
                </div>
            </div>
            <div class="action-row" style="background:#0b1322; border-color:#2a3d60;">
                <div class="action-row-title" style="color:#ffffff;">Root Cause Identified in INC-101:</div>
                <div class="action-row-desc" style="color:#cbd5e1;">
                    The release introduced an unindexed query with exclusive row locks on checkout tables, holding connections open under concurrent user transactions.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.info("Historical learning is unavailable because Team Memory is OFF. Generic AI has no access to past anti-patterns or previous root causes.")

st.markdown("</div>", unsafe_allow_html=True)


# =========================================================================
# 4. WHAT SHOULD I INVESTIGATE NOW? (SAFE DIAGNOSTIC WORKBENCH)
# =========================================================================
st.markdown("""
<div class="section-container">
    <div class="section-header-wrap">
        <div>
            <div class="section-title">
                <span class="section-index">4</span>
                What should I investigate now?
            </div>
            <div class="section-subtitle">Cognitive reasoning trace, non-destructive diagnostic execution, and advisory remediation.</div>
        </div>
    </div>
""", unsafe_allow_html=True)

c_inv1, c_inv2 = st.columns(2)

with c_inv1:
    st.markdown("<span style='font-size:13px; font-weight:700; color:#f8fafc; text-transform:uppercase;'>SRE Cognitive Reasoning Trace:</span>", unsafe_allow_html=True)
    if is_memory_enabled:
        st.markdown("""
        <div class="reasoning-box">
            <span class="reasoning-pill pill-observed">OBSERVED</span>
            <span style="font-size:13px; color:#f1f5f9;">Active p99 latency is 4.9s and database connection pool saturation is at 88% following release v2.4.5.</span>
        </div>
        <div class="reasoning-box">
            <span class="reasoning-pill pill-history">HISTORICAL</span>
            <span style="font-size:13px; color:#f1f5f9;">INC-101 had the exact same symptom signature. Scaling pod replicas worsened the outage (anti-pattern).</span>
        </div>
        <div class="reasoning-box">
            <span class="reasoning-pill pill-inference">INFERENCE</span>
            <span style="font-size:13px; color:#f1f5f9;">High confidence that a newly deployed query in v2.4.5 is acquiring transaction row locks without an index.</span>
        </div>
        <div class="reasoning-box" style="border-left:3px solid #10b981;">
            <span class="reasoning-pill pill-rec">RECOMMENDATION</span>
            <span style="font-size:13px; color:#f1f5f9;">Inspect active query locks on postgres-primary before considering pod restarts or scale adjustments.</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="reasoning-box">
            <span class="reasoning-pill pill-observed">OBSERVED</span>
            <span style="font-size:13px; color:#f1f5f9;">Elevated latency (4.9s) and 504 timeouts with 88% connection pool saturation.</span>
        </div>
        <div class="reasoning-box">
            <span class="reasoning-pill pill-inference">INFERENCE</span>
            <span style="font-size:13px; color:#f1f5f9;">Suspected general database overload or unoptimized release queries in v2.4.5.</span>
        </div>
        <div class="reasoning-box" style="border-left:3px solid #64748b;">
            <span class="reasoning-pill pill-rec">RECOMMENDATION</span>
            <span style="font-size:13px; color:#f1f5f9;">Inspect general database metrics, check commit logs, or consider service pod restart.</span>
        </div>
        """, unsafe_allow_html=True)

with c_inv2:
    st.markdown("<span style='font-size:13px; font-weight:700; color:#f8fafc; text-transform:uppercase;'>Diagnostic Workbench (Interactive & Real-Time):</span>", unsafe_allow_html=True)
    if is_memory_enabled:
        st.markdown("""
        <div class="terminal-window">
            <div class="terminal-bar">
                <span>postgres-primary &bull; lock_inspector.sql</span>
                <span style="color:#10b981;">READ-ONLY &bull; ZERO RISK</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.code("""SELECT pid, now() - query_start AS duration, state, query 
FROM pg_stat_activity 
WHERE state != 'idle' 
ORDER BY duration DESC LIMIT 5;""", language="sql")
        
        # Interactive Diagnostic Execution
        c_btn1, c_btn2 = st.columns([1, 1])
        with c_btn1:
            if st.button("▶ Run Live Diagnostic Query", use_container_width=True):
                with st.status("Querying postgres-primary for active locks...", expanded=True) as status:
                    st.write("Connecting to postgres-primary.prod (11ms)...")
                    st.write("Inspecting pg_stat_activity for duration > 5s...")
                    st.write("Found 1 blocking lock held by PID 48219.")
                    status.update(label="Diagnostic Complete: 1 Exclusive Lock Identified!", state="complete", expanded=False)
                st.session_state["ran_diagnostic"] = True

        if st.session_state["ran_diagnostic"]:
            st.markdown("""
            <div style="background:#090e1a; border:1px solid #1f2e4a; border-radius:6px; padding:10px 12px; margin: 10px 0;">
                <div style="font-size:12px; font-weight:700; color:#38bdf8; text-transform:uppercase; margin-bottom:6px;">Live Query Execution Results:</div>
            """, unsafe_allow_html=True)
            
            diag_results = pd.DataFrame([
                {
                    "PID": "48219",
                    "Duration": "42.8s",
                    "State": "active",
                    "Query Snippet": "SELECT * FROM exchange_rates WHERE currency = 'USD' FOR UPDATE;",
                    "Contention": "EXCLUSIVE LOCK (BLOCKING 44 TRANSACTIONS)"
                },
                {
                    "PID": "48220",
                    "Duration": "38.1s",
                    "State": "waiting for lock",
                    "Query Snippet": "UPDATE checkout_sessions SET status = 'PROCESSING'...",
                    "Contention": "Blocked on PID 48219"
                },
                {
                    "PID": "48224",
                    "Duration": "35.4s",
                    "State": "waiting for lock",
                    "Query Snippet": "SELECT * FROM inventory WHERE item_id = 9102 FOR SHARE;",
                    "Contention": "Blocked on PID 48219"
                }
            ])
            st.dataframe(diag_results, use_container_width=True, hide_index=True)
            st.markdown("""
                <div style="font-size:12.5px; color:#f87171; font-weight:600; margin-top:6px;">
                    &bull; Finding: PID 48219 is holding an unindexed exclusive row lock, starving all 44 downstream connection pools! Exactly matches INC-101 historical precedent!
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#090e1a; border:1px solid #182338; border-radius:6px; padding:12px; margin-top:8px;">
            <div style="font-size:12.5px; font-weight:700; color:#38bdf8; margin-bottom:4px;">Advisory Remediation Playbook (Sign-Off Required):</div>
            <div style="font-size:12px; color:#94a3b8; line-height:1.4;">
                &bull; Terminate blocking query PID: <code>SELECT pg_terminate_backend(48219);</code><br>
                &bull; Enforce per-pod connection limit ceiling to prevent pool starvation.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not is_recovered:
            st.checkbox("Authorize remediation plan (Level-2 SRE sign-off)", key="auth_plan_user")
            if st.session_state.get("auth_plan_user", False):
                if st.button("⚡ Execute Advisory Remediation (Kill PID 48219)", use_container_width=True):
                    with st.status("Executing live remediation sequence...", expanded=True) as status:
                        st.write("Connecting to postgres-primary cluster via administrative connection...")
                        st.write("Terminating blocking lock query PID 48219 via `SELECT pg_terminate_backend(48219)`... Terminated (0.02s).")
                        st.write("Draining PgBouncer client pooler connection backlog (44 active -> 18 healthy)... Complete.")
                        st.write("Observing service recovery: p99 latency returning to baseline (4,920ms -> 210ms)... Normalized!")
                        status.update(label="Remediation successfully executed! Baseline performance restored.", state="complete", expanded=False)
                    st.session_state["remediation_executed"] = True
                    st.rerun()
        else:
            st.markdown("""
            <div style="background:rgba(16, 185, 129, 0.12); border:1px solid rgba(16, 185, 129, 0.3); border-radius:6px; padding:10px 14px; margin-top:10px;">
                <span style="font-size:13px; font-weight:700; color:#34d399;">&check; Remediation Live: PID 48219 Terminated</span><br>
                <span style="font-size:12px; color:#a7f3d0;">Connection pool normalized to 22% capacity. P99 latency returned to 210ms.</span>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.code("""SHOW max_connections;
SELECT count(*) FROM pg_stat_activity;""", language="sql")
        st.caption("Target: generic-db | Basic connection count query.")
        st.checkbox("Authorize generic remediation option", key="auth_generic_user")

st.markdown("</div>", unsafe_allow_html=True)


# =========================================================================
# 5. WHAT SHOULD RECALLOPS REMEMBER? (MEMORY INGESTION STUDIO)
# =========================================================================
st.markdown("""
<div class="section-container">
    <div class="section-header-wrap">
        <div>
            <div class="section-title">
                <span class="section-index">5</span>
                What should RecallOps remember?
            </div>
            <div class="section-subtitle">Synthesize verified lessons and commit to Hindsight so future on-call engineers never repeat this outage.</div>
        </div>
    </div>
""", unsafe_allow_html=True)

c_sav1, c_sav2 = st.columns(2)

with c_sav1:
    st.markdown("""
    <div class="retention-summary">
        <div style="font-size:13px; font-weight:800; color:#34d399; text-transform:uppercase; letter-spacing:0.6px; margin-bottom:12px;">
            Institutional Memory Payload Prepared for Ingestion
        </div>
        <div class="retention-item">
            &bull; <b>Incident Postmortem:</b> Release v2.4.5 caused database connection pool exhaustion on checkout-service.
        </div>
        <div class="retention-item">
            &bull; <b>Anti-Pattern Registered:</b> Scaling application replicas from 4 to 12 worsened latency to 8.2s (Do Not Attempt).
        </div>
        <div class="retention-item">
            &bull; <b>Remediation Playbook:</b> Terminate unindexed query PID, enforce statement timeout, and cap pod connection limits to 8.
        </div>
        <div class="retention-item">
            &bull; <b>Verified Recovery:</b> P99 latency restored to 210ms in 90 seconds.
        </div>
        <div style="margin-top:14px; font-size:11.5px; color:#64748b; font-family:'JetBrains Mono';">
            Target Memory Bank: recallops-vault (Hindsight Persistent)
        </div>
    </div>
    """, unsafe_allow_html=True)

with c_sav2:
    st.markdown("<span style='font-size:13px; font-weight:700; color:#f8fafc; text-transform:uppercase;'>Incident Resolution Form</span>", unsafe_allow_html=True)
    with st.form("resolve_save_form"):
        default_cause = "Release v2.4.5 unindexed query acquired exclusive row lock on exchange_rates, starving Postgres connection pool." if is_recovered else (current_incident.root_cause or "Release v2.4.5 multi-currency calculation held exclusive row locks on exchange_rates without compound index.")
        default_res = "Terminated blocking lock PID 48219 via pg_terminate_backend; capped per-pod connection limit to 8." if is_recovered else (current_incident.final_resolution or "Terminated blocking query PID, added compound index on (currency, effective_date), capped pool size to 8 per pod.")
        default_rec = 19 if is_recovered else (current_incident.recovery_time_minutes or 24)

        f_cause = st.text_input("Confirmed Root Cause:", value=default_cause)
        f_res = st.text_input("Final Resolution:", value=default_res)
        f_rec = st.number_input("Recovery Duration (Minutes):", min_value=1, max_value=300, value=default_rec)

        submit_save = st.form_submit_button("Resolve & Save to Memory", use_container_width=True)

        if submit_save:
            attempts = [
                ActionAttempt(
                    action_id=f"ACT-{current_incident.incident_id}-1",
                    timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    action_taken="Scaled pod deployment replicas",
                    hypothesis="Distribute CPU load",
                    outcome=ActionOutcome.FAILED,
                    observable_effect="Exhausted database connection pool; worsened latency to 8.2s",
                    actor="@oncall-engineer"
                ),
                ActionAttempt(
                    action_id=f"ACT-{current_incident.incident_id}-2",
                    timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    action_taken="Terminated blocking lock PID and capped per-pod pool connections",
                    hypothesis="Eliminate transaction lock contention",
                    outcome=ActionOutcome.SUCCESSFUL,
                    observable_effect="Connection pool drained to 22%; p99 latency normalized to 210ms in 90s",
                    actor="@lead-sre"
                )
            ]
            lessons_list = [
                "Never scale out pods during database connection pool saturation.",
                "Enforce statement_timeout on all currency calculation queries.",
                "Add compound index on table row locks before deployment."
            ]

            with st.spinner("Retaining incident experience into Hindsight memory..."):
                inc_manager.resolve_and_retain(
                    incident_id=current_incident.incident_id,
                    root_cause=f_cause,
                    final_resolution=f_res,
                    recovery_time_minutes=f_rec,
                    actions_attempted=attempts,
                    lessons_learned=lessons_list,
                )
            st.success(f"Incident {current_incident.incident_id} marked as RESOLVED and committed to Hindsight memory bank '{mem_adapter.bank_id}'. Future incidents will immediately recall this experience!")
            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
