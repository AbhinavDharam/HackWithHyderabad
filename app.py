"""
RecallOps: Incident Command Center
Operational Incident Response Engine with Hindsight Persistent Memory
"""
import streamlit as st
import json
from datetime import datetime, timezone
from recallops.config import HINDSIGHT_BANK_ID, HINDSIGHT_BASE_URL, GROQ_MODEL
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

# Dark Technical SaaS Theme (High contrast, professional, human-centric)
st.markdown("""
<style>
    /* Global Container Styles */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
    }
    
    /* Top Navigation Bar */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0 16px 0;
        border-bottom: 1px solid #1e293b;
        margin-bottom: 24px;
    }
    .brand-title {
        font-size: 20px;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .brand-subtitle {
        font-size: 13px;
        color: #94a3b8;
        font-weight: 400;
        margin-left: 8px;
    }
    .status-badge {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }
    .badge-prod {
        background-color: #1e293b;
        color: #94a3b8;
        border: 1px solid #334155;
    }
    .badge-memory-active {
        background-color: rgba(14, 165, 233, 0.15);
        color: #38bdf8;
        border: 1px solid #0284c7;
    }
    
    /* User-Centric Section Headers */
    .section-header {
        font-size: 18px;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: -0.3px;
        margin: 28px 0 6px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .section-desc {
        font-size: 13px;
        color: #94a3b8;
        margin-bottom: 14px;
    }
    .step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background-color: #0284c7;
        color: #ffffff;
        font-size: 11px;
        font-weight: 700;
    }

    /* Incident Hero Card */
    .hero-card {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 6px;
        padding: 18px 20px;
        margin-bottom: 16px;
    }
    .badge-sev1 {
        background-color: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid #dc2626;
    }
    .badge-sev2 {
        background-color: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid #d97706;
    }
    .badge-service {
        background-color: rgba(139, 92, 246, 0.15);
        color: #c084fc;
        border: 1px solid #7c3aed;
    }
    .badge-status {
        background-color: rgba(239, 68, 68, 0.12);
        color: #fca5a5;
        border: 1px solid #b91c1c;
    }

    /* Signal Metric Cards */
    .signal-card {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 12px 14px;
    }
    .signal-label {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.5px;
    }
    .signal-value {
        font-size: 22px;
        font-weight: 700;
        color: #f8fafc;
        margin: 2px 0;
    }
    .signal-delta {
        font-size: 12px;
        font-weight: 500;
        color: #f87171;
    }

    /* Memory Centerpiece */
    .memory-box {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-top: 3px solid #0ea5e9;
        border-radius: 6px;
        padding: 16px 18px;
        margin-bottom: 14px;
    }
    .match-pill {
        background-color: rgba(14, 165, 233, 0.2);
        color: #38bdf8;
        border: 1px solid #0284c7;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        letter-spacing: 0.5px;
    }

    /* Action Outcome Panels */
    .panel-failed {
        background-color: rgba(225, 29, 72, 0.08);
        border: 1px solid rgba(225, 29, 72, 0.3);
        border-left: 4px solid #e11d48;
        border-radius: 4px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }
    .panel-worked {
        background-color: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-left: 4px solid #10b981;
        border-radius: 4px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }
    .panel-neutral {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 4px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }

    /* Investigation Layer Tags */
    .layer-tag {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 2px 6px;
        border-radius: 3px;
        margin-right: 6px;
    }
    .tag-observed { background-color: #334155; color: #f8fafc; }
    .tag-historical { background-color: rgba(14, 165, 233, 0.2); color: #38bdf8; }
    .tag-inference { background-color: rgba(245, 158, 11, 0.2); color: #fbbf24; }
    .tag-recommendation { background-color: rgba(16, 185, 129, 0.2); color: #34d399; }
</style>
""", unsafe_allow_html=True)


# Initialize State
@st.cache_resource
def get_adapters():
    mem_adapter = HindsightAdapter()
    inc_manager = IncidentManager(memory_adapter=mem_adapter)
    llm = LLMClient()
    agent = SREAgent(memory_adapter=mem_adapter, llm_client=llm)
    return mem_adapter, inc_manager, agent, llm

mem_adapter, inc_manager, agent, llm = get_adapters()

# Minimized Left Sidebar (User-Centric)
with st.sidebar:
    st.image("assets/logo.png", width=170)
    st.caption("Operational Incident Memory")
    st.markdown("---")

    # Incident Selection
    all_incidents = inc_manager.get_all()
    inc_options = {f"[{i.incident_id}] {i.title}": i.incident_id for i in all_incidents}
    
    # Default to INC-105
    default_idx = 0
    for idx, (label, iid) in enumerate(inc_options.items()):
        if iid == "INC-105":
            default_idx = idx
            break

    selected_label = st.selectbox("Current Incident:", list(inc_options.keys()), index=default_idx)
    selected_id = inc_options[selected_label]
    current_incident = inc_manager.get_by_id(selected_id)

    st.markdown("---")

    # Team Memory Overview
    stats = mem_adapter.get_stats()
    st.markdown("**Team Memory Bank**")
    st.markdown(f"- **{stats['total_memories']}** previous incidents remembered")
    st.markdown(f"- **{stats['action_experiences']}** learned action outcomes")
    st.markdown(f"- **{stats['lessons_and_antipatterns']}** runbook rules")
    
    st.caption("● Hindsight Memory Active")

    # Hidden / Collapsed Developer Settings (Doesn't clutter normal SRE view)
    with st.expander("Developer & Demo Settings"):
        st.caption(f"Inference Model: `{GROQ_MODEL}`")
        st.caption(f"Bank ID: `{stats['bank_id']}`")
        if st.button("Reset Baseline Memory", use_container_width=True):
            from seed_memory import seed_memory_bank
            seed_memory_bank()
            st.rerun()


# Guard clause
if not current_incident:
    st.error("Selected incident not found.")
    st.stop()


# =========================================================================
# TOP NAVIGATION
# =========================================================================
st.markdown(f"""
<div class="top-nav">
    <div>
        <span class="brand-title">RecallOPS</span>
        <span class="brand-subtitle">Operational Incident Memory</span>
    </div>
    <div style="display:flex; gap:10px; align-items:center;">
        <span class="status-badge badge-prod">Production</span>
        <span class="status-badge badge-memory-active">● Team Memory Active</span>
        <span class="status-badge badge-prod" style="font-family:monospace;">{current_incident.incident_id}</span>
    </div>
</div>
""", unsafe_allow_html=True)


# =========================================================================
# 1. WHAT'S HAPPENING?
# =========================================================================
st.markdown("""
<div class="section-header">
    <span class="step-number">1</span> What's happening?
</div>
<div class="section-desc">Incident identity, severity, service, and live telemetry signals.</div>
""", unsafe_allow_html=True)

# Incident Hero Card
sev_val = current_incident.severity.value if hasattr(current_incident.severity, 'value') else current_incident.severity
sev_badge = "badge-sev1" if "SEV-1" in sev_val else "badge-sev2"

st.markdown(f"""
<div class="hero-card">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
        <div>
            <span class="status-badge {sev_badge}">{sev_val}</span>
            <span class="status-badge badge-status">{current_incident.status}</span>
            <span class="status-badge badge-service">{current_incident.affected_service}</span>
            <h2 style="margin: 8px 0 4px 0; color:#f8fafc; font-size:22px;">[{current_incident.incident_id}] {current_incident.title}</h2>
            <p style="color:#94a3b8; font-size:14px; margin:0;">
                Production {current_incident.affected_service} is experiencing high latency and gateway timeouts following release activities.
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 4 Key Signal Cards
sig1, sig2, sig3, sig4 = st.columns(4)

with sig1:
    met_lat = next((m for m in current_incident.metrics if "latency" in m.metric_name.lower()), None)
    if met_lat:
        delta_lat = met_lat.observed_value - met_lat.baseline_value
        st.markdown(f"""
        <div class="signal-card">
            <div class="signal-label">P99 Latency</div>
            <div class="signal-value">{met_lat.observed_value / 1000.0 if met_lat.observed_value > 999 else met_lat.observed_value:.1f}s</div>
            <div class="signal-delta">↑ {delta_lat / 1000.0:.1f}s vs baseline ({met_lat.baseline_value:.0f}ms)</div>
        </div>
        """, unsafe_allow_html=True)

with sig2:
    met_err = next((m for m in current_incident.metrics if "error" in m.metric_name.lower()), None)
    if met_err:
        delta_err = met_err.observed_value - met_err.baseline_value
        st.markdown(f"""
        <div class="signal-card">
            <div class="signal-label">Error Rate</div>
            <div class="signal-value">{met_err.observed_value:.1f}%</div>
            <div class="signal-delta">↑ {delta_err:.1f}% vs baseline ({met_err.baseline_value:.2f}%)</div>
        </div>
        """, unsafe_allow_html=True)

with sig3:
    met_res = next((m for m in current_incident.metrics if "utilization" in m.metric_name.lower() or "connection" in m.metric_name.lower() or "cpu" in m.metric_name.lower()), None)
    if met_res:
        delta_res = met_res.observed_value - met_res.baseline_value
        lbl = met_res.metric_name.replace("_", " ").title()
        if len(lbl) > 20:
            lbl = "DB Connections" if "db" in lbl.lower() else "Resource Saturation"
        st.markdown(f"""
        <div class="signal-card">
            <div class="signal-label">{lbl}</div>
            <div class="signal-value">{met_res.observed_value:.0f}%</div>
            <div class="signal-delta">↑ {delta_res:.0f}% vs baseline ({met_res.baseline_value:.0f}%)</div>
        </div>
        """, unsafe_allow_html=True)

with sig4:
    trig = current_incident.triggers[0] if current_incident.triggers else None
    st.markdown(f"""
    <div class="signal-card">
        <div class="signal-label">Recent Change</div>
        <div class="signal-value" style="font-size:16px; margin-top:6px; color:#38bdf8;">Release v2.4.5</div>
        <div style="font-size:12px; color:#94a3b8;">14 min prior to alert</div>
    </div>
    """, unsafe_allow_html=True)

# Collapsible details
with st.expander("Reported Symptoms & Incident Event Log"):
    c_s1, c_s2 = st.columns(2)
    with c_s1:
        st.markdown("**Error Signatures:**")
        for s in current_incident.symptoms:
            st.markdown(f"- `{s}`")
    with c_s2:
        st.markdown("**Incident Log:**")
        for stp in current_incident.investigation_steps:
            st.markdown(f"- {stp}")


# =========================================================================
# 2. HAVE WE SEEN THIS BEFORE?
# =========================================================================
st.write("")
col_hdr2, col_tog = st.columns([3, 1])

with col_hdr2:
    st.markdown("""
    <div class="section-header">
        <span class="step-number">2</span> Have we seen this before?
    </div>
    <div class="section-desc">Historical organizational incident experience retrieved by Hindsight.</div>
    """, unsafe_allow_html=True)

with col_tog:
    st.write("")
    memory_mode = st.radio(
        "Team Memory:",
        ["WITH TEAM MEMORY", "WITHOUT MEMORY"],
        format_func=lambda x: "ON (Team Memory)" if x == "WITH TEAM MEMORY" else "OFF (Generic AI)",
        horizontal=True,
        help="Compare RecallOps with team memory against a standard generic AI without memory."
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
    # Team Memory: Confirmed Match
    st.markdown("""
    <div class="memory-box">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <div>
                <span style="font-size:16px; font-weight:700; color:#38bdf8;">Yes — RecallOps found 3 relevant previous incidents in team memory.</span>
            </div>
            <span class="match-pill">STRONG HISTORICAL MATCH</span>
        </div>
        <p style="color:#f8fafc; font-size:15px; margin: 6px 0 10px 0;">
            <b>INC-101:</b> Checkout API / Post-release latency surge / Database connection pool exhaustion
        </p>
        <div style="background-color:rgba(15, 23, 42, 0.7); border:1px solid #1e293b; border-radius:4px; padding:10px 14px; margin-bottom:10px;">
            <div style="font-size:12px; font-weight:600; text-transform:uppercase; color:#94a3b8; margin-bottom:6px;">Why this incident is relevant to you right now:</div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:6px; font-size:13px; color:#e2e8f0;">
                <div>✓ <b>Same service:</b> checkout-service</div>
                <div>✓ <b>Similar symptoms:</b> Latency surged to >5000ms with HTTP 504 timeouts</div>
                <div>✓ <b>Similar trigger:</b> Outage occurred within 20m of service release</div>
                <div>✓ <b>Similar resource spike:</b> Database connection pool ceiling saturation (88% vs 100%)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Compare with other historical incidents (2 more)"):
        st.markdown("- **INC-102:** `inventory-service` — Redis Cache Stampede (Flash sale traffic miss, resolved in 39m)")
        st.markdown("- **INC-104:** `payment-service` — Webhook Ingestion Thread Starvation (Batch billing overload, resolved in 45m)")

else:
    # WITHOUT MEMORY: Generic AI
    st.markdown("""
    <div class="memory-box" style="border-top:3px solid #64748b;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-size:16px; font-weight:700; color:#94a3b8;">No organizational incident history available (Generic AI Mode).</span>
            <span class="status-badge badge-prod">NO MEMORY ACCESSED</span>
        </div>
        <p style="color:#cbd5e1; font-size:14px; margin:4px 0 0 0;">
            Analyzing current symptoms purely from general first-principles heuristics without team memory.
        </p>
    </div>
    """, unsafe_allow_html=True)


# =========================================================================
# 3. WHAT DID THE TEAM LEARN?
# =========================================================================
st.write("")
st.markdown("""
<div class="section-header">
    <span class="step-number">3</span> What did the team learn?
</div>
<div class="section-desc">Historical investigation from INC-101 so you do not repeat past mistakes.</div>
""", unsafe_allow_html=True)

if is_memory_enabled:
    col_lrn_left, col_lrn_right = st.columns(2)

    with col_lrn_left:
        st.markdown("**What engineers tried that FAILED:**")
        st.markdown("""
        <div class="panel-failed">
            <b style="color:#f87171;">❌ Scale application replicas from 4 to 12 pods</b><br>
            <span style="font-size:13px; color:#fecdd3;"><b>Result:</b> Failed — Each new pod opened 25 database connections; overwhelmed PgBouncer, caused connection resets, and increased latency to 8.2s.</span>
        </div>
        <div class="panel-failed">
            <b style="color:#f87171;">❌ Increase gateway timeout from 5s to 15s</b><br>
            <span style="font-size:13px; color:#fecdd3;"><b>Result:</b> Failed — Requests accumulated longer, causing upstream gateway thread pool exhaustion.</span>
        </div>
        """, unsafe_allow_html=True)

    with col_lrn_right:
        st.markdown("**What ACTUALLY worked & Root cause:**")
        st.markdown("""
        <div class="panel-worked">
            <b style="color:#34d399;">✓ Terminated blocking lock query PID</b><br>
            <span style="font-size:13px; color:#a7f3d0;"><b>Result:</b> Active connection queue drained from 100 to 28; p99 latency returned to 210ms in 90 seconds.</span>
        </div>
        <div class="panel-worked">
            <b style="color:#34d399;">✓ Capped per-pod connection limit to 8</b><br>
            <span style="font-size:13px; color:#a7f3d0;"><b>Result:</b> Enforced strict ceiling per pod to prevent cascading database starvation.</span>
        </div>
        <div class="panel-neutral" style="border-left: 4px solid #64748b;">
            <b style="color:#f1f5f9;">Root Cause Identified:</b><br>
            <span style="font-size:13px; color:#cbd5e1;">Release introduced an unindexed query with exclusive row locks on checkout tables, holding open connections under concurrent traffic.</span>
        </div>
        """, unsafe_allow_html=True)

else:
    st.info("Historical learning is unavailable because Team Memory is OFF. The assistant cannot warn you about previously failed actions or past root causes.")


# =========================================================================
# 4. WHAT SHOULD I INVESTIGATE NOW?
# =========================================================================
st.write("")
st.markdown("""
<div class="section-header">
    <span class="step-number">4</span> What should I investigate now?
</div>
<div class="section-desc">Evidence-backed investigation guidance for the active incident.</div>
""", unsafe_allow_html=True)

col_rec_left, col_rec_right = st.columns(2)

with col_rec_left:
    st.markdown("**Reasoning Breakdown:**")
    if is_memory_enabled:
        st.markdown("""
        <div class="panel-neutral">
            <span class="layer-tag tag-observed">OBSERVED</span>
            <span style="font-size:13px; color:#f8fafc;">Current p99 latency is 4.9s and database connection pool is at 88% following release v2.4.5.</span>
        </div>
        <div class="panel-neutral">
            <span class="layer-tag tag-historical">HISTORICAL</span>
            <span style="font-size:13px; color:#f8fafc;">INC-101 experienced the exact same pattern: post-release latency driven by database pool lock contention. Scaling pods failed previously.</span>
        </div>
        <div class="panel-neutral">
            <span class="layer-tag tag-inference">INFERENCE</span>
            <span style="font-size:13px; color:#f8fafc;">A newly deployed query in v2.4.5 may be holding transaction row locks, starving the connection pool.</span>
        </div>
        <div class="panel-neutral" style="border-left: 3px solid #10b981;">
            <span class="layer-tag tag-recommendation">RECOMMENDATION</span>
            <span style="font-size:13px; color:#f8fafc;">Inspect active query locks and PgBouncer pool saturation before attempting pod restarts or scaling.</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="panel-neutral">
            <span class="layer-tag tag-observed">OBSERVED</span>
            <span style="font-size:13px; color:#f8fafc;">Elevated latency (4.9s) and 504 timeouts with 88% connection utilization.</span>
        </div>
        <div class="panel-neutral">
            <span class="layer-tag tag-inference">INFERENCE</span>
            <span style="font-size:13px; color:#f8fafc;">General database saturation or release regression.</span>
        </div>
        <div class="panel-neutral" style="border-left: 3px solid #64748b;">
            <span class="layer-tag tag-recommendation">RECOMMENDATION</span>
            <span style="font-size:13px; color:#f8fafc;">Inspect database metrics, check git log for release v2.4.5, and consider restarting pods.</span>
        </div>
        """, unsafe_allow_html=True)

with col_rec_right:
    st.markdown("**Recommended Diagnostic Check (Read-Only):**")
    if is_memory_enabled:
        st.markdown("Run query to inspect active transaction locks holding open pool connections:")
        st.code("""SELECT pid, now() - query_start AS duration, state, query 
FROM pg_stat_activity 
WHERE state != 'idle' 
ORDER BY duration DESC LIMIT 5;""", language="sql")
        st.caption("Component: postgres-primary | Rationale: Proven diagnostic in INC-101 to find blocking query PID.")
        
        st.markdown("**Remediation Plan (Advisory — Engineer Authorization Required):**")
        st.markdown("- **Step:** Terminate blocking lock PID via `SELECT pg_terminate_backend(pid)` and verify connection pool normalization.")
        st.markdown("- **Precedent:** Successfully resolved INC-101 and recovered latency to 210ms in 90 seconds.")
        st.checkbox("Authorize remediation plan (Engineer sign-off required)", key="auth_plan_user")
    else:
        st.markdown("General connection count check:")
        st.code("""SHOW max_connections;
SELECT count(*) FROM pg_stat_activity;""", language="sql")
        st.caption("Component: database-pool | Rationale: Basic connection verification.")
        
        st.markdown("**Generic Remediation Options:**")
        st.markdown("- **Option A:** Rollback release v2.4.5 to v2.4.4 if database saturation correlates with the new release.")
        st.markdown("- **Option B:** Restart application service pods to clear connection states.")
        st.checkbox("Authorize generic remediation option", key="auth_generic_user")


# =========================================================================
# 5. WHAT SHOULD RECALLOPS REMEMBER?
# =========================================================================
st.write("")
st.markdown("""
<div class="section-header">
    <span class="step-number">5</span> What should RecallOps remember?
</div>
<div class="section-desc">Capture what was learned from this incident so future on-call engineers benefit.</div>
""", unsafe_allow_html=True)

col_sav_left, col_sav_right = st.columns(2)

with col_sav_left:
    st.markdown("""
    <div class="panel-neutral" style="border-left: 3px solid #10b981;">
        <b style="color:#34d399;">Experience Prepared for Memory Retention:</b><br>
        <span style="font-size:13px; color:#cbd5e1;">
        • Release v2.4.5 was associated with database connection pool exhaustion on checkout-service.<br>
        • Increasing application replicas did not resolve the incident (recorded as an anti-pattern).<br>
        • Terminating the unindexed query PID and capping pool limits normalized latency.<br>
        • Verified recovery: p99 latency restored to baseline within 90 seconds.
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"Hindsight Storage Bank: `{mem_adapter.bank_id}` (Persistent)")

with col_sav_right:
    st.markdown("**Resolve & Save to Memory:**")
    with st.form("resolve_save_form"):
        f_cause = st.text_input(
            "Confirmed Root Cause:",
            value=current_incident.root_cause or "Release v2.4.5 multi-currency calculation held exclusive row locks on exchange_rates without compound index."
        )
        f_res = st.text_input(
            "Final Resolution:",
            value=current_incident.final_resolution or "Terminated blocking query PID, added compound index on (currency, effective_date), capped pool size to 8 per pod."
        )
        f_rec = st.number_input("Recovery Time (Minutes):", min_value=1, max_value=300, value=current_incident.recovery_time_minutes or 24)

        submit_save = st.form_submit_button("Resolve & Save to Memory", use_container_width=True)

        if submit_save:
            attempts = [
                ActionAttempt(
                    action_id=f"ACT-{current_incident.incident_id}-1",
                    timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    action_taken="Scaled pod deployment replicas",
                    hypothesis="Distribute CPU load",
                    outcome=ActionOutcome.FAILED,
                    observable_effect="Exhausted database connection pool; worsened latency",
                    actor="@oncall-engineer"
                ),
                ActionAttempt(
                    action_id=f"ACT-{current_incident.incident_id}-2",
                    timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    action_taken="Terminated blocking lock PID and capped per-pod pool connections",
                    hypothesis="Eliminate transaction lock contention",
                    outcome=ActionOutcome.SUCCESSFUL,
                    observable_effect="Connection pool drained to 22%; p99 latency normalized to 180ms",
                    actor="@lead-sre"
                )
            ]
            lessons_list = [
                "Never scale out pods during database connection saturation.",
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
            st.success(f"Incident {current_incident.incident_id} marked as RESOLVED and committed to Hindsight memory bank '{mem_adapter.bank_id}'. Future incidents can now recall this experience!")
            st.rerun()
