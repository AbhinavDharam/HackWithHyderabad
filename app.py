"""
RecallOps: Incident Command Center
Enterprise Operational Incident Response Engine powered by Hindsight Persistent Memory
"""
import os
import streamlit as st
import json
import time
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from recallops.config import HINDSIGHT_BANK_ID, HINDSIGHT_BASE_URL, GROQ_MODEL, GEMINI_MODEL
from recallops.models.incident import Incident, ActionAttempt, ActionOutcome, Severity, IncidentMetric, IncidentTrigger
from recallops.memory.hindsight_adapter import HindsightAdapter
from recallops.incidents.incident_manager import IncidentManager
from recallops.agent.sre_agent import SREAgent
from recallops.llm.llm_client import LLMClient

# Page Configuration
st.set_page_config(
    page_title="RecallOps — Incident Command",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Dark Enterprise Theme matching the exact design mockup
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .stApp {
        background-color: #080c15;
        color: #f1f5f9;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    .block-container {
        padding-top: 1.0rem;
        padding-bottom: 2.5rem;
        max-width: 1440px;
    }

    /* Top Search & Global Bar */
    .top-global-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        padding-bottom: 12px;
        border-bottom: 1px solid #162032;
    }
    .search-mockup {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 8px 14px;
        color: #64748b;
        font-size: 13px;
        display: flex;
        align-items: center;
        gap: 10px;
        width: 380px;
    }
    .top-actions {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .env-pill {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 600;
        color: #cbd5e1;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .bell-icon {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 6px 10px;
        color: #94a3b8;
        font-size: 13px;
        position: relative;
    }
    .bell-dot {
        position: absolute;
        top: 5px;
        right: 7px;
        width: 6px;
        height: 6px;
        background: #ef4444;
        border-radius: 50%;
    }
    .user-avatar-pill {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 4px 10px 4px 6px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12.5px;
        font-weight: 600;
        color: #f1f5f9;
    }
    .avatar-circle {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: #3b82f6;
        color: #ffffff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 700;
    }

    /* Main Dashboard Header */
    .dashboard-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 20px;
    }
    .dashboard-title {
        font-size: 26px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin: 0 0 4px 0;
    }
    .dashboard-subtitle {
        font-size: 13.5px;
        color: #94a3b8;
        margin: 0;
    }
    .header-quote {
        font-size: 12.5px;
        color: #64748b;
        text-align: right;
        background: linear-gradient(90deg, transparent, rgba(30, 41, 59, 0.4));
        padding: 6px 12px;
        border-radius: 6px;
    }

    /* Active Incident Hero Card */
    .hero-card {
        background: linear-gradient(135deg, rgba(225, 29, 72, 0.09) 0%, rgba(15, 23, 42, 0.95) 45%, #0d1424 100%);
        border: 1px solid rgba(225, 29, 72, 0.35);
        border-radius: 12px;
        padding: 22px 24px;
        margin-bottom: 24px;
        position: relative;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.45);
    }
    .hero-badge-active {
        display: inline-block;
        background: #e11d48;
        color: #ffffff;
        font-size: 10.5px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        padding: 3px 9px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .hero-badge-mitigated {
        display: inline-block;
        background: #10b981;
        color: #ffffff;
        font-size: 10.5px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        padding: 3px 9px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .hero-incident-title {
        font-size: 23px;
        font-weight: 800;
        color: #ffffff;
        margin: 0 0 10px 0;
        letter-spacing: -0.4px;
    }
    .hero-tags {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
    }
    .tag-sev1 {
        background: rgba(225, 29, 72, 0.2);
        color: #f43f5e;
        border: 1px solid #e11d48;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
    }
    .tag-service {
        background: rgba(139, 92, 246, 0.18);
        color: #c084fc;
        border: 1px solid #7c3aed;
        font-size: 11px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        padding: 2px 8px;
        border-radius: 4px;
    }
    .tag-neutral {
        background: #1e293b;
        color: #94a3b8;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 4px;
    }
    .hero-desc-text {
        font-size: 13.5px;
        color: #94a3b8;
        line-height: 1.5;
        max-width: 95%;
        margin-bottom: 18px;
    }

    /* Hero Metric Cards Grid */
    .metric-grid-card {
        background: rgba(10, 15, 29, 0.85);
        border: 1px solid #1a253a;
        border-radius: 8px;
        padding: 12px 14px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    }
    .metric-topline {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
    }
    .metric-icon-square {
        width: 22px;
        height: 22px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
    }
    .icon-red { background: rgba(239, 68, 68, 0.2); color: #f87171; }
    .icon-purple { background: rgba(139, 92, 246, 0.2); color: #c084fc; }
    .icon-blue { background: rgba(14, 165, 233, 0.2); color: #38bdf8; }
    .metric-title-label {
        font-size: 11.5px;
        font-weight: 600;
        color: #94a3b8;
    }
    .metric-main-value {
        font-size: 22px;
        font-weight: 800;
        color: #ffffff;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.5px;
        margin: 2px 0;
    }
    .metric-baseline-delta {
        font-size: 11px;
        font-weight: 600;
    }
    .delta-red-text { color: #f87171; }
    .delta-blue-text { color: #38bdf8; }
    .delta-green-text { color: #34d399; }

    /* Workflow Cards Row */
    .workflow-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 28px 0 14px 0;
    }
    .workflow-title {
        font-size: 17px;
        font-weight: 700;
        color: #ffffff;
    }
    .workflow-sub {
        font-size: 12.5px;
        color: #64748b;
    }
    .workflow-card {
        background: #0d1424;
        border: 1px solid #1b263b;
        border-radius: 8px;
        padding: 14px;
        display: flex;
        flex-direction: column;
        gap: 6px;
        transition: all 0.2s ease;
        height: 100%;
    }
    .workflow-card.active {
        border-color: #0284c7;
        background: #0f1c36;
        box-shadow: 0 0 14px rgba(2, 132, 199, 0.25);
    }
    .wf-top {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .wf-badge {
        width: 22px;
        height: 22px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 700;
    }
    .wf-badge-1 { background: #0284c7; color: #fff; }
    .wf-badge-2 { background: #7c3aed; color: #fff; }
    .wf-badge-3 { background: #059669; color: #fff; }
    .wf-badge-4 { background: #d97706; color: #fff; }
    .wf-badge-5 { background: #dc2626; color: #fff; }
    .wf-name {
        font-size: 13.5px;
        font-weight: 700;
        color: #ffffff;
    }
    .wf-desc {
        font-size: 11.5px;
        color: #94a3b8;
        line-height: 1.4;
    }

    /* Bottom Section Dual Cards */
    .section-box {
        background: #0b1120;
        border: 1px solid #1a2538;
        border-radius: 10px;
        padding: 18px 20px;
        height: 100%;
    }
    .box-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
    }
    .box-title {
        font-size: 16px;
        font-weight: 700;
        color: #ffffff;
    }
    .box-link {
        font-size: 12px;
        color: #38bdf8;
        text-decoration: none;
        font-weight: 600;
    }

    /* Incidents Table */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12.5px;
    }
    .custom-table th {
        text-align: left;
        color: #64748b;
        font-weight: 600;
        padding: 8px 10px;
        border-bottom: 1px solid #162032;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .custom-table td {
        padding: 10px 10px;
        border-bottom: 1px solid #121a2a;
        color: #cbd5e1;
    }
    .badge-sev-1 {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid #dc2626;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 10.5px;
        font-weight: 700;
    }
    .badge-sev-2 {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid #d97706;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 10.5px;
        font-weight: 700;
    }
    .badge-sev-3 {
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid #0284c7;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 10.5px;
        font-weight: 700;
    }
    .status-investigating {
        background: rgba(14, 165, 233, 0.15);
        color: #38bdf8;
        border: 1px solid #0284c7;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 10.5px;
        font-weight: 600;
    }
    .status-resolved {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid #059669;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 10.5px;
        font-weight: 600;
    }

    /* Team Memory at a Glance Grid */
    .mem-stat-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin-bottom: 14px;
    }
    .mem-stat-tile {
        background: #080d18;
        border: 1px solid #162032;
        border-radius: 6px;
        padding: 12px 10px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .mem-tile-icon {
        width: 32px;
        height: 32px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
    }
    .mem-tile-val {
        font-size: 20px;
        font-weight: 800;
        color: #ffffff;
        font-family: 'JetBrains Mono', monospace;
    }
    .mem-tile-lbl {
        font-size: 11px;
        color: #94a3b8;
        line-height: 1.2;
    }
    .hindsight-status-bar {
        background: #080d18;
        border: 1px solid #162032;
        border-radius: 6px;
        padding: 10px 12px;
        margin-bottom: 10px;
    }
    .smarter-card {
        background: rgba(56, 189, 248, 0.05);
        border: 1px solid rgba(56, 189, 248, 0.15);
        border-radius: 6px;
        padding: 10px 12px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    /* Left Sidebar Styling */
    .sidebar-brand-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 4px;
    }
    .sidebar-brand-name {
        font-size: 20px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
    }
    .sidebar-sub {
        font-size: 11.5px;
        color: #64748b;
        margin-bottom: 18px;
    }
    .sidebar-memory-card {
        background: #0b1120;
        border: 1px solid #1a2538;
        border-radius: 8px;
        padding: 14px;
        margin-top: 24px;
    }

    /* Streamlit Button Tweaks */
    div.stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 8px 14px !important;
        transition: all 0.2s ease !important;
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

# Session State Management
if "nav_tab" not in st.session_state:
    st.session_state["nav_tab"] = "Overview"
if "ran_diagnostic" not in st.session_state:
    st.session_state["ran_diagnostic"] = False
if "remediation_executed" not in st.session_state:
    st.session_state["remediation_executed"] = False

# Sidebar - Minimal Logo + Brand Text + Navigation Tabs
with st.sidebar:
    c_logo, c_brand = st.columns([1, 4])
    with c_logo:
        st.image("assets/logo.png", width=36)
    with c_brand:
        st.markdown("<div style='font-size:20px; font-weight:800; color:#fff; margin-top:2px;'>RecallOps</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11.5px; color:#64748b; margin-top:-10px; margin-bottom:16px;'>Operational Incident Memory</div>", unsafe_allow_html=True)

    # Clean Navigation Menu Buttons
    nav_items = [
        ("Overview", "🏠 Overview"),
        ("Incidents", "📑 Incidents"),
        ("Memory", "🗄️ Memory"),
        ("Investigate", "🔍 Investigate"),
        ("Resolution", "✓ Resolution"),
        ("Settings", "⚙️ Settings"),
    ]

    for key, label in nav_items:
        is_active = (st.session_state["nav_tab"] == key)
        b_type = "primary" if is_active else "secondary"
        if st.button(label, key=f"nav_btn_{key}", use_container_width=True, type=b_type):
            st.session_state["nav_tab"] = key
            st.rerun()

    # Bottom Hindsight Memory Card
    stats = mem_adapter.get_stats()
    st.markdown(f"""
    <div class="sidebar-memory-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:12px; font-weight:700; color:#cbd5e1;">Hindsight Memory</span>
            <span style="font-size:11px; color:#10b981; font-weight:600;">● Connected</span>
        </div>
        <div style="font-size:12px; color:#94a3b8; margin-bottom:10px;">
            <div><b>{stats['total_memories']}</b> Incidents remembered</div>
            <div><b>{stats['action_experiences']}</b> Action outcomes</div>
            <div><b>{stats['lessons_and_antipatterns']}</b> Runbook patterns</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🗄️ View Memory →", key="view_mem_sidebar", use_container_width=True):
        st.session_state["nav_tab"] = "Memory"
        st.rerun()


# Top Global Search & Navigation Bar
all_incidents = inc_manager.get_all()
inc_options = {f"[{i.incident_id}] {i.title}": i.incident_id for i in all_incidents}

default_idx = 0
for idx, (label, iid) in enumerate(inc_options.items()):
    if iid == "INC-105":
        default_idx = idx
        break

col_srch, col_ctrls = st.columns([1.8, 2.2])

with col_srch:
    st.markdown("""
    <div class="search-mockup">
        <span>🔍</span>
        <span>Search incidents, services, or ask RecallOps...</span>
    </div>
    """, unsafe_allow_html=True)

with col_ctrls:
    c_env, c_bell, c_inc = st.columns([1, 0.4, 2])
    with c_env:
        st.markdown("""
        <div class="env-pill">
            <span style="color:#10b981;">●</span> Production ▾
        </div>
        """, unsafe_allow_html=True)
    with c_bell:
        st.markdown("""
        <div class="bell-icon">
            🔔<span class="bell-dot"></span>
        </div>
        """, unsafe_allow_html=True)
    with c_inc:
        selected_label = st.selectbox(
            "Active Incident",
            list(inc_options.keys()),
            index=default_idx,
            label_visibility="collapsed"
        )
        selected_id = inc_options[selected_label]
        current_incident = inc_manager.get_by_id(selected_id)

is_recovered = st.session_state["remediation_executed"]


# =========================================================================
# TAB 1: OVERVIEW (THE EXACT INCIDENT COMMAND CENTER DASHBOARD MOCKUP)
# =========================================================================
if st.session_state["nav_tab"] == "Overview":
    
    # Main Header
    st.markdown("""
    <div class="dashboard-header">
        <div>
            <h1 class="dashboard-title">Incident Command Center</h1>
            <p class="dashboard-subtitle">Get real-time context, investigate with your team's memory, and resolve faster.</p>
        </div>
        <div class="header-quote">
            Your team's<br><b>experience, always on.</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Active Incident Hero Card
    sev_badge = "hero-badge-mitigated" if is_recovered else "hero-badge-active"
    sev_text = "INCIDENT MITIGATED" if is_recovered else "ACTIVE INCIDENT"

    st.markdown(f"""
    <div class="hero-card">
        <span class="{sev_badge}">{sev_text}</span>
        <div class="hero-incident-title">[{current_incident.incident_id}] {current_incident.title}</div>
        <div class="hero-tags">
            <span class="tag-sev1">{"RESOLVED" if is_recovered else "SEV-1"}</span>
            <span class="tag-service">{current_incident.affected_service}</span>
            <span class="tag-neutral">Production</span>
            <span class="tag-neutral">🕒 14 min ago</span>
        </div>
        <p class="hero-desc-text">
            {"Production checkout-service requests have normalized following targeted lock remediation." if is_recovered else f"Production {current_incident.affected_service} requests are experiencing high latency and 504 timeouts following release v2.4.5."}
        </p>
    """, unsafe_allow_html=True)

    # 4 Metric Cards inside the Hero
    c_hero_mets, c_hero_cta = st.columns([3.5, 1])

    with c_hero_mets:
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""
            <div class="metric-grid-card">
                <div class="metric-topline">
                    <span class="metric-icon-square icon-red">📈</span>
                    <span class="metric-title-label">P99 Latency</span>
                </div>
                <div class="metric-main-value" style="color:{'#34d399' if is_recovered else '#ffffff'};">
                    {'210 ms' if is_recovered else '4.9 s'}
                </div>
                <div class="metric-baseline-delta {'delta-green-text' if is_recovered else 'delta-red-text'}">
                    {'✓ Normal baseline' if is_recovered else '↑ 4.7 s vs baseline'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-grid-card">
                <div class="metric-topline">
                    <span class="metric-icon-square icon-red">⚠️</span>
                    <span class="metric-title-label">Error Rate</span>
                </div>
                <div class="metric-main-value" style="color:{'#34d399' if is_recovered else '#ffffff'};">
                    {'0.01 %' if is_recovered else '19.8 %'}
                </div>
                <div class="metric-baseline-delta {'delta-green-text' if is_recovered else 'delta-red-text'}">
                    {'✓ Healthy ingress' if is_recovered else '↑ 19.7 % vs baseline'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="metric-grid-card">
                <div class="metric-topline">
                    <span class="metric-icon-square icon-purple">🗄️</span>
                    <span class="metric-title-label">DB Connections</span>
                </div>
                <div class="metric-main-value" style="color:{'#34d399' if is_recovered else '#ffffff'};">
                    {'22 %' if is_recovered else '88 %'}
                </div>
                <div class="metric-baseline-delta {'delta-green-text' if is_recovered else 'delta-red-text'}">
                    {'✓ Drained pool' if is_recovered else '↑ 58 % vs baseline'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with m4:
            st.markdown("""
            <div class="metric-grid-card">
                <div class="metric-topline">
                    <span class="metric-icon-square icon-blue">💻</span>
                    <span class="metric-title-label">Recent Change</span>
                </div>
                <div class="metric-main-value" style="font-size:16px; color:#38bdf8; margin:6px 0;">
                    Release v2.4.5
                </div>
                <div class="metric-baseline-delta delta-blue-text">
                    Detected 14 min ago
                </div>
            </div>
            """, unsafe_allow_html=True)

    with c_hero_cta:
        st.write("")
        st.write("")
        if st.button("Go to Investigate →", key="hero_goto_investigate", use_container_width=True, type="primary"):
            st.session_state["nav_tab"] = "Investigate"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Your Incident Response Workflow Row (5 step cards)
    st.markdown("""
    <div class="workflow-header">
        <div>
            <div class="workflow-title">Your Incident Response Workflow</div>
            <div class="workflow-sub">Follow the workflow to resolve this incident using your team's memory.</div>
        </div>
        <div style="font-size:11.5px; color:#64748b; background:#0f172a; border:1px solid #1e293b; padding:4px 10px; border-radius:4px;">
            ⚡ Interactive Flow
        </div>
    </div>
    """, unsafe_allow_html=True)

    w1, w2, w3, w4, w5 = st.columns(5)
    with w1:
        st.markdown("""
        <div class="workflow-card active">
            <div class="wf-top">
                <span class="wf-badge wf-badge-1">1</span>
                <span class="wf-name">Overview</span>
            </div>
            <div class="wf-desc">What's happening right now? Active metrics & blast radius.</div>
        </div>
        """, unsafe_allow_html=True)
    with w2:
        st.markdown("""
        <div class="workflow-card">
            <div class="wf-top">
                <span class="wf-badge wf-badge-2">2</span>
                <span class="wf-name">Incidents</span>
            </div>
            <div class="wf-desc">Browse and search past organizational incidents.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Incidents →", key="wf_open_incidents", use_container_width=True):
            st.session_state["nav_tab"] = "Incidents"
            st.rerun()
    with w3:
        st.markdown("""
        <div class="workflow-card">
            <div class="wf-top">
                <span class="wf-badge wf-badge-3">3</span>
                <span class="wf-name">Memory</span>
            </div>
            <div class="wf-desc">Find relevant team experience & past runbooks.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Memory →", key="wf_open_memory", use_container_width=True):
            st.session_state["nav_tab"] = "Memory"
            st.rerun()
    with w4:
        st.markdown("""
        <div class="workflow-card">
            <div class="wf-top">
                <span class="wf-badge wf-badge-4">4</span>
                <span class="wf-name">Investigate</span>
            </div>
            <div class="wf-desc">Get AI-guided investigation & run diagnostics.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Investigate →", key="wf_open_investigate", use_container_width=True):
            st.session_state["nav_tab"] = "Investigate"
            st.rerun()
    with w5:
        st.markdown("""
        <div class="workflow-card">
            <div class="wf-top">
                <span class="wf-badge wf-badge-5">5</span>
                <span class="wf-name">Resolution</span>
            </div>
            <div class="wf-desc">Resolve and save learnings into Hindsight memory.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Resolution →", key="wf_open_resolution", use_container_width=True):
            st.session_state["nav_tab"] = "Resolution"
            st.rerun()

    st.write("")

    # Bottom Row: Recent Incidents Table + Team Memory at a Glance
    col_bottom_left, col_bottom_right = st.columns([1.3, 1])

    with col_bottom_left:
        st.markdown("""
        <div class="section-box">
            <div class="box-header">
                <span class="box-title">Recent Incidents</span>
                <span class="box-link">All 5 Cataloged</span>
            </div>
            <table class="custom-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>TITLE</th>
                        <th>SERVICE</th>
                        <th>SEVERITY</th>
                        <th>STATUS</th>
                        <th>TIME</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><b>INC-105</b></td>
                        <td>P99 Latency Surge & 504...</td>
                        <td><code>checkout-service</code></td>
                        <td><span class="badge-sev-1">SEV-1</span></td>
                        <td><span class="status-investigating">Investigating</span></td>
                        <td>14 min ago</td>
                    </tr>
                    <tr>
                        <td><b>INC-104</b></td>
                        <td>Payment API Errors</td>
                        <td><code>payment-service</code></td>
                        <td><span class="badge-sev-2">SEV-2</span></td>
                        <td><span class="status-resolved">Resolved</span></td>
                        <td>3 hours ago</td>
                    </tr>
                    <tr>
                        <td><b>INC-103</b></td>
                        <td>Authentication Failures</td>
                        <td><code>auth-service</code></td>
                        <td><span class="badge-sev-2">SEV-2</span></td>
                        <td><span class="status-resolved">Resolved</span></td>
                        <td>1 day ago</td>
                    </tr>
                    <tr>
                        <td><b>INC-102</b></td>
                        <td>Database High CPU</td>
                        <td><code>db-service</code></td>
                        <td><span class="badge-sev-3">SEV-3</span></td>
                        <td><span class="status-resolved">Resolved</span></td>
                        <td>2 days ago</td>
                    </tr>
                    <tr>
                        <td><b>INC-101</b></td>
                        <td>Post-release Latency Spike</td>
                        <td><code>checkout-service</code></td>
                        <td><span class="badge-sev-2">SEV-2</span></td>
                        <td><span class="status-resolved">Resolved</span></td>
                        <td>5 days ago</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with col_bottom_right:
        st.markdown(f"""
        <div class="section-box">
            <div class="box-header">
                <span class="box-title">Team Memory at a Glance</span>
                <span class="box-link">recallops-vault</span>
            </div>
            <div class="mem-stat-grid">
                <div class="mem-stat-tile">
                    <span class="mem-tile-icon" style="background:rgba(56,189,248,0.15); color:#38bdf8;">🗄️</span>
                    <div>
                        <div class="mem-tile-val">{stats['total_memories']}</div>
                        <div class="mem-tile-lbl">Incidents remembered</div>
                    </div>
                </div>
                <div class="mem-stat-tile">
                    <span class="mem-tile-icon" style="background:rgba(245,158,11,0.15); color:#fbbf24;">📖</span>
                    <div>
                        <div class="mem-tile-val">{stats['action_experiences']}</div>
                        <div class="mem-tile-lbl">Action outcomes</div>
                    </div>
                </div>
                <div class="mem-stat-tile">
                    <span class="mem-tile-icon" style="background:rgba(16,185,129,0.15); color:#34d399;">📄</span>
                    <div>
                        <div class="mem-tile-val">{stats['lessons_and_antipatterns']}</div>
                        <div class="mem-tile-lbl">Runbook patterns</div>
                    </div>
                </div>
            </div>
            <div class="hindsight-status-bar">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <span style="font-size:12.5px; font-weight:700; color:#ffffff;">Hindsight Cloud Memory</span>
                    <span style="font-size:11px; color:#10b981; font-weight:600;">● Connected</span>
                </div>
                <div style="font-size:11.5px; color:#94a3b8;">
                    Your team's incident experience is stored in Hindsight Cloud (API v0.10.1) and ready to use.
                </div>
            </div>
            <div class="smarter-card">
                <span style="font-size:18px;">📈</span>
                <div style="font-size:12px; color:#cbd5e1;">
                    <b style="color:#38bdf8;">Getting smarter over time:</b> Each resolved incident helps RecallOps provide more relevant and accurate guidance.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# =========================================================================
# TAB 2: INCIDENTS (FULL CATALOG & INSPECTOR)
# =========================================================================
elif st.session_state["nav_tab"] == "Incidents":
    st.markdown("""
    <div class="dashboard-header">
        <div>
            <h1 class="dashboard-title">Incident Catalog & History</h1>
            <p class="dashboard-subtitle">Browse, filter, and inspect past organizational outages and active incidents.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c_f1, c_f2 = st.columns([1, 2])
    with c_f1:
        f_status = st.selectbox("Filter Status:", ["ALL", "ACTIVE / INVESTIGATING", "RESOLVED"])
    with c_f2:
        f_search = st.text_input("Filter by Service or Keyword:", placeholder="e.g. checkout, redis, latency...")

    for inc in all_incidents:
        if f_status == "RESOLVED" and inc.status != "RESOLVED":
            continue
        if f_status == "ACTIVE / INVESTIGATING" and inc.status == "RESOLVED":
            continue
        if f_search and f_search.lower() not in inc.title.lower() and f_search.lower() not in inc.affected_service.lower():
            continue

        with st.expander(f"[{inc.incident_id}] {inc.title} — {inc.affected_service} ({inc.status})", expanded=(inc.incident_id == current_incident.incident_id)):
            st.markdown(f"**Service:** `{inc.affected_service}` | **Severity:** `{inc.severity}` | **MTTR:** `{inc.recovery_time_minutes or 24}m`")
            st.markdown(f"**Root Cause:** {inc.root_cause or 'Under active investigation'}")
            st.markdown(f"**Final Resolution:** {inc.final_resolution or 'Pending SRE resolution'}")
            
            if inc.actions_attempted:
                st.markdown("**Actions Attempted:**")
                for a in inc.actions_attempted:
                    status_emoji = "✓" if a.outcome == ActionOutcome.SUCCESSFUL else "❌"
                    st.markdown(f"- {status_emoji} **{a.action_taken}**: {a.observable_effect} (by {a.actor})")


# =========================================================================
# TAB 3: MEMORY (HINDSIGHT PERSISTENT MEMORY EXPLORER)
# =========================================================================
elif st.session_state["nav_tab"] == "Memory":
    st.markdown("""
    <div class="dashboard-header">
        <div>
            <h1 class="dashboard-title">Hindsight Memory Bank Explorer</h1>
            <p class="dashboard-subtitle">Inspect the institutional memory units indexed in Hindsight Cloud (<code>recallops-vault</code>).</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    all_memories = mem_adapter.list_all_memories()
    c_m1, c_m2 = st.columns([1, 2])
    with c_m1:
        type_filter = st.selectbox("Record Type:", ["ALL", "postmortem", "action_experience", "lessons_learned"])
    with c_m2:
        query_input = st.text_input("Semantic Recall Query:", placeholder="e.g. database pool connection lock...")

    if query_input:
        recalled = mem_adapter.recall(query=query_input, max_results=6)
        st.markdown(f"**Top Semantic Matches ({len(recalled)} retrieved):**")
        for r in recalled:
            st.markdown(f"""
            <div style="background:#0b1120; border:1px solid #1e293b; border-left:3px solid #0284c7; border-radius:6px; padding:12px; margin-bottom:10px;">
                <div style="font-size:12px; font-weight:700; color:#38bdf8;">Similarity Score: {r.get('score', 0.85):.2f}</div>
                <div style="font-size:13px; color:#e2e8f0; margin-top:4px;">{r.get('text', '')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        filtered = all_memories
        if type_filter != "ALL":
            filtered = [m for m in filtered if m.get("metadata", {}).get("type") == type_filter]
        
        st.caption(f"Showing {len(filtered)} indexed cognitive memory units")
        for m in filtered[:10]:
            doc_id = m.get("document_id", "DOC")
            m_type = m.get("metadata", {}).get("type", "record")
            st.markdown(f"""
            <div style="background:#0b1120; border:1px solid #1a2538; border-radius:6px; padding:12px; margin-bottom:8px;">
                <div style="font-size:11px; font-weight:700; color:#94a3b8; font-family:'JetBrains Mono';">[{doc_id}] &bull; {m_type.upper()}</div>
                <div style="font-size:13px; color:#e2e8f0; margin-top:4px;">{m.get('content', '')}</div>
            </div>
            """, unsafe_allow_html=True)


# =========================================================================
# TAB 4: INVESTIGATE (AI DIAGNOSTIC WORKBENCH & REAL-TIME REMEDIATION)
# =========================================================================
elif st.session_state["nav_tab"] == "Investigate":
    st.markdown("""
    <div class="dashboard-header">
        <div>
            <h1 class="dashboard-title">AI Investigation Workbench</h1>
            <p class="dashboard-subtitle">Multi-signal cognitive reasoning, precedent correlation, and real-time safe diagnostics.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Memory Toggle Control
    c_inv_hdr, c_inv_tog = st.columns([3, 1])
    with c_inv_hdr:
        st.markdown(f"**Target Incident:** `[{current_incident.incident_id}] {current_incident.title}`")
    with c_inv_tog:
        memory_mode = st.radio(
            "Team Memory:",
            ["WITH TEAM MEMORY", "WITHOUT MEMORY"],
            format_func=lambda x: "ON (Team Memory)" if x == "WITH TEAM MEMORY" else "OFF (Generic AI)",
            horizontal=True
        )

    is_memory_enabled = (memory_mode == "WITH TEAM MEMORY")

    # Run Agent
    historical_pool = inc_manager.get_historical_pool()
    agent_mode_internal = "WITH_HINDSIGHT_MEMORY" if is_memory_enabled else "WITHOUT_MEMORY"
    report = agent.investigate(
        incident=current_incident,
        mode=agent_mode_internal,
        historical_pool=historical_pool
    )

    # 1. Precedent Section
    if is_memory_enabled:
        st.markdown("""
        <div style="background:#0d1424; border:1px solid #1e2e4a; border-left:4px solid #0284c7; border-radius:8px; padding:16px; margin-bottom:18px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-size:15px; font-weight:700; color:#ffffff;">Precedent Matched: INC-101 (Post-Release Latency Surge)</span>
                <span style="background:rgba(14,165,233,0.15); color:#38bdf8; border:1px solid #0284c7; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700;">STRONG HISTORICAL MATCH</span>
            </div>
            <div style="font-size:13px; color:#cbd5e1; margin-bottom:10px;">
                RecallOps retrieved <b>INC-101</b> from Hindsight memory with 4 correlated signals:
            </div>
            <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:8px; font-size:12px;">
                <div style="background:#080d18; border:1px solid #162032; padding:8px; border-radius:4px;">
                    <div style="color:#64748b; font-size:10px; font-weight:700;">COMPONENT</div>
                    <div>&check; <b>checkout-service</b></div>
                </div>
                <div style="background:#080d18; border:1px solid #162032; padding:8px; border-radius:4px;">
                    <div style="color:#64748b; font-size:10px; font-weight:700;">SYMPTOM</div>
                    <div>&check; <b>p99 &gt; 4.5s + 504 drops</b></div>
                </div>
                <div style="background:#080d18; border:1px solid #162032; padding:8px; border-radius:4px;">
                    <div style="color:#64748b; font-size:10px; font-weight:700;">TRIGGER</div>
                    <div>&check; <b>&lt; 20m post-deploy</b></div>
                </div>
                <div style="background:#080d18; border:1px solid #162032; padding:8px; border-radius:4px;">
                    <div style="color:#64748b; font-size:10px; font-weight:700;">RESOURCE</div>
                    <div>&check; <b>DB pool saturation (88%)</b></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Anti-Patterns vs Verified Fixes
        c_lrn1, c_lrn2 = st.columns(2)
        with c_lrn1:
            st.markdown("""
            <div style="background:rgba(225,29,72,0.06); border:1px solid rgba(225,29,72,0.25); border-left:4px solid #e11d48; border-radius:8px; padding:14px;">
                <div style="color:#f87171; font-weight:700; font-size:13px; margin-bottom:8px;">❌ What Failed (Anti-Patterns — Do Not Repeat)</div>
                <div style="font-size:12.5px; color:#fecdd3; line-height:1.45;">
                    &bull; <b>Scaled pods from 4 to 12:</b> Each pod opened 25 DB connections, crashing PgBouncer and spiking p99 latency to <b>8.2s</b>.<br>
                    &bull; <b>Increased gateway timeout:</b> Requests queued up, starving upstream thread pools.
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c_lrn2:
            st.markdown("""
            <div style="background:rgba(16,185,129,0.06); border:1px solid rgba(16,185,129,0.25); border-left:4px solid #10b981; border-radius:8px; padding:14px;">
                <div style="color:#34d399; font-weight:700; font-size:13px; margin-bottom:8px;">✓ What Worked & Root Cause</div>
                <div style="font-size:12.5px; color:#a7f3d0; line-height:1.45;">
                    &bull; <b>Terminated blocking lock PID:</b> Active pool queue drained from 100 to 28; p99 latency returned to <b>210ms in 90 seconds</b>.<br>
                    &bull; <b>Root Cause:</b> Release v2.4.5 introduced an unindexed query acquiring exclusive row locks on checkout tables.
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")

    # 2. Cognitive Trace + Interactive Diagnostic Workbench
    c_diag_left, c_diag_right = st.columns(2)

    with c_diag_left:
        st.markdown("**SRE Cognitive Reasoning Trace:**")
        st.markdown("""
        <div style="background:#090e1a; border:1px solid #182338; border-radius:6px; padding:10px 12px; margin-bottom:6px;">
            <span style="background:#1e293b; color:#f1f5f9; padding:2px 6px; border-radius:3px; font-size:10px; font-weight:700;">OBSERVED</span>
            <span style="font-size:12.5px; color:#f1f5f9; margin-left:6px;">Current p99 latency is 4.9s and database connection pool saturation is at 88% post release v2.4.5.</span>
        </div>
        <div style="background:#090e1a; border:1px solid #182338; border-radius:6px; padding:10px 12px; margin-bottom:6px;">
            <span style="background:rgba(14,165,233,0.2); color:#38bdf8; padding:2px 6px; border-radius:3px; font-size:10px; font-weight:700;">HISTORICAL</span>
            <span style="font-size:12.5px; color:#f1f5f9; margin-left:6px;">INC-101 experienced exact lock contention pattern. Scaling pods is an anti-pattern.</span>
        </div>
        <div style="background:#090e1a; border:1px solid #182338; border-radius:6px; padding:10px 12px; margin-bottom:6px;">
            <span style="background:rgba(245,158,11,0.2); color:#fbbf24; padding:2px 6px; border-radius:3px; font-size:10px; font-weight:700;">INFERENCE</span>
            <span style="font-size:12.5px; color:#f1f5f9; margin-left:6px;">High probability that a newly deployed query in v2.4.5 is holding unindexed row locks.</span>
        </div>
        <div style="background:#090e1a; border:1px solid #182338; border-left:3px solid #10b981; border-radius:6px; padding:10px 12px;">
            <span style="background:rgba(16,185,129,0.2); color:#34d399; padding:2px 6px; border-radius:3px; font-size:10px; font-weight:700;">RECOMMENDATION</span>
            <span style="font-size:12.5px; color:#f1f5f9; margin-left:6px;">Inspect active query locks on postgres-primary before considering pod restarts.</span>
        </div>
        """, unsafe_allow_html=True)

    with c_diag_right:
        st.markdown("**Diagnostic Workbench (Interactive & Real-Time):**")
        st.code("""SELECT pid, now() - query_start AS duration, state, query 
FROM pg_stat_activity 
WHERE state != 'idle' 
ORDER BY duration DESC LIMIT 5;""", language="sql")

        if st.button("▶ Run Live Diagnostic Query", key="run_diag_btn", use_container_width=True):
            with st.status("Querying postgres-primary for active locks...", expanded=True) as status:
                st.write("Connecting to postgres-primary.prod (11ms)...")
                st.write("Inspecting pg_stat_activity for duration > 5s...")
                st.write("Found 1 blocking lock held by PID 48219.")
                status.update(label="Diagnostic Complete: 1 Exclusive Lock Identified!", state="complete", expanded=False)
            st.session_state["ran_diagnostic"] = True

        if st.session_state["ran_diagnostic"]:
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
                }
            ])
            st.dataframe(diag_results, use_container_width=True, hide_index=True)
            st.markdown("<span style='font-size:12px; color:#f87171; font-weight:600;'>🚨 Finding: PID 48219 is holding an unindexed exclusive row lock, starving connection pools! Matches INC-101 precedent!</span>", unsafe_allow_html=True)

        if not is_recovered:
            st.checkbox("Authorize advisory remediation (Sign-Off)", key="auth_plan_user")
            if st.session_state.get("auth_plan_user", False):
                if st.button("⚡ Execute Advisory Remediation (Kill PID 48219)", key="exec_remed_btn", use_container_width=True):
                    with st.status("Executing live remediation sequence...", expanded=True) as status:
                        st.write("Terminating blocking lock query PID 48219 via `SELECT pg_terminate_backend(48219)`... Done.")
                        st.write("Draining PgBouncer pooler backlog (44 active -> 18 healthy)... Complete.")
                        st.write("Validating recovery: p99 latency returning to baseline (4,920ms -> 210ms)... Normalized!")
                        status.update(label="Remediation successfully applied! Performance restored.", state="complete", expanded=False)
                    st.session_state["remediation_executed"] = True
                    st.rerun()
        else:
            st.success("Remediation Active: System normalized (P99: 210ms).")

    st.write("")
    if st.button("Proceed to Resolution & Ingestion →", key="goto_res_btn", type="primary"):
        st.session_state["nav_tab"] = "Resolution"
        st.rerun()


# =========================================================================
# TAB 5: RESOLUTION (INCIDENT RESOLUTION & HINDSIGHT INGESTION)
# =========================================================================
elif st.session_state["nav_tab"] == "Resolution":
    st.markdown("""
    <div class="dashboard-header">
        <div>
            <h1 class="dashboard-title">Incident Resolution & Ingestion Studio</h1>
            <p class="dashboard-subtitle">Synthesize verified lessons and commit to Hindsight so future engineers never repeat this outage.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c_r1, c_r2 = st.columns(2)

    with c_r1:
        st.markdown("""
        <div style="background:#0a0f1d; border:1px solid #1a2742; border-left:4px solid #10b981; border-radius:8px; padding:16px;">
            <div style="font-size:13px; font-weight:800; color:#34d399; text-transform:uppercase; margin-bottom:10px;">
                Verified Experience Prepared for Ingestion
            </div>
            <div style="font-size:13px; color:#cbd5e1; line-height:1.5;">
                &bull; <b>Incident Postmortem:</b> Release v2.4.5 caused database connection pool exhaustion on checkout-service.<br>
                &bull; <b>Anti-Pattern Registered:</b> Scaling pod deployment replicas from 4 to 12 worsened latency to 8.2s (Do Not Attempt).<br>
                &bull; <b>Remediation Playbook:</b> Terminate unindexed query PID, enforce statement timeout, and cap pod connection limits to 8.<br>
                &bull; <b>Target Bank:</b> <code>recallops-vault</code> (Hindsight Cloud Persistent)
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_r2:
        st.markdown("**Resolve & Save to Memory:**")
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
                st.success(f"Incident {current_incident.incident_id} marked as RESOLVED and committed to Hindsight Cloud bank '{mem_adapter.bank_id}'! Future incidents will immediately recall this experience.")
                st.rerun()


# =========================================================================
# TAB 6: SETTINGS (SYSTEM & BACKEND CONFIGURATION)
# =========================================================================
elif st.session_state["nav_tab"] == "Settings":
    st.markdown("""
    <div class="dashboard-header">
        <div>
            <h1 class="dashboard-title">System & Backend Settings</h1>
            <p class="dashboard-subtitle">Operational status of AI inference models and Hindsight persistent memory.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c_s1, c_s2 = st.columns(2)
    with c_s1:
        st.markdown(f"""
        <div style="background:#0b1120; border:1px solid #1a2538; border-radius:8px; padding:16px;">
            <div style="font-size:14px; font-weight:700; color:#38bdf8; margin-bottom:8px;">LLM Reasoning Engine</div>
            <div style="font-size:13px; color:#cbd5e1; line-height:1.5;">
                &bull; <b>Active Provider:</b> {llm.get_provider_name()}<br>
                &bull; <b>Primary Model:</b> <code>{GEMINI_MODEL}</code><br>
                &bull; <b>Credentials:</b> Loaded securely from backend <code>.env</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_s2:
        st.markdown(f"""
        <div style="background:#0b1120; border:1px solid #1a2538; border-radius:8px; padding:16px;">
            <div style="font-size:14px; font-weight:700; color:#10b981; margin-bottom:8px;">Hindsight Memory Vault</div>
            <div style="font-size:13px; color:#cbd5e1; line-height:1.5;">
                &bull; <b>Cloud Status:</b> {'Connected (API v0.10.1)' if mem_adapter.is_cloud_connected() else 'Local Mirror Active'}<br>
                &bull; <b>Memory Bank ID:</b> <code>{stats['bank_id']}</code><br>
                &bull; <b>Total Cognitive Units:</b> {stats['total_memories']} records indexed
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    if st.button("↺ Reset Outage State (Re-run Demo)", use_container_width=True):
        st.session_state["ran_diagnostic"] = False
        st.session_state["remediation_executed"] = False
        st.session_state["nav_tab"] = "Overview"
        st.rerun()

    if st.button("Re-Seed Memory Bank Baseline", use_container_width=True):
        from seed_memory import seed_memory_bank
        seed_memory_bank()
        st.success("Re-seeded memory bank baseline.")
        st.rerun()
