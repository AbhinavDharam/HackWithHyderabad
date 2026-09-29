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
    page_title="RecallOps — Incident Command Center",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dark Technical SaaS Theme (High contrast, professional, restrained)
st.markdown("""
<style>
    /* Global Container Styles */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
    }
    
    /* Technical Header & Nav */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0 16px 0;
        border-bottom: 1px solid #1e293b;
        margin-bottom: 20px;
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
    
    /* Incident Hero Cards */
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
    .badge-resolved {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid #059669;
    }

    /* Signal Metric Tiles */
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

    /* Centerpiece Memory Panels */
    .memory-panel {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-top: 3px solid #0ea5e9;
        border-radius: 6px;
        padding: 18px 20px;
        margin: 18px 0;
    }
    .match-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .match-tag {
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

    /* Timeline step */
    .timeline-item {
        font-size: 13px;
        color: #cbd5e1;
        padding: 4px 0;
        border-left: 2px solid #334155;
        padding-left: 12px;
        margin-left: 6px;
    }
    .timeline-time {
        font-weight: 600;
        color: #94a3b8;
        margin-right: 8px;
        font-family: monospace;
    }

    /* Lifecycle Step Strip */
    .lifecycle-strip {
        font-size: 11px;
        font-weight: 600;
        color: #64748b;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin: 20px 0 10px 0;
        display: flex;
        gap: 6px;
        align-items: center;
    }
    .lifecycle-active {
        color: #38bdf8;
    }
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

# Minimized Left Sidebar
with st.sidebar:
    st.image("assets/logo.png", width=180)
    st.caption("Operational Incident Memory Engine")
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

    selected_label = st.selectbox("Active Incident Scenario:", list(inc_options.keys()), index=default_idx)
    selected_id = inc_options[selected_label]
    current_incident = inc_manager.get_by_id(selected_id)

    st.markdown("---")

    # Real Memory Stats from Application State
    stats = mem_adapter.get_stats()
    st.markdown("**Hindsight Memory State**")
    st.caption(f"Bank: `{stats['bank_id']}`")
    st.markdown(f"- **{stats['total_memories']}** incident records stored")
    st.markdown(f"- **{stats['action_experiences']}** action outcome experiences")
    st.markdown(f"- **{stats['lessons_and_antipatterns']}** organizational runbook rules")
    
    cloud_status = "Connected (Cloud)" if stats["connected_to_hindsight"] else "Active (Local Mirror)"
    st.caption(f"Status: **{cloud_status}**")

    if st.button("Reset Baseline Memory", use_container_width=True):
        from seed_memory import seed_memory_bank
        seed_memory_bank()
        st.rerun()

    st.markdown("---")
    with st.expander("System Configuration"):
        st.caption(f"Inference Model: `{GROQ_MODEL}`")
        st.caption(f"Hindsight Endpoint: `{HINDSIGHT_BASE_URL}`")
        llm_ready = "Ready (Cloud)" if llm.is_live_llm_ready() else "Deterministic SRE Engine"
        st.caption(f"Inference Engine: **{llm_ready}**")


# Guard clause
if not current_incident:
    st.error("Selected incident not found.")
    st.stop()

# =========================================================================
# TOP NAVIGATION & INCIDENT HERO (WHAT IS HAPPENING?)
# =========================================================================

# Top Navigation Bar
st.markdown(f"""
<div class="top-nav">
    <div>
        <span class="brand-title">RecallOPS</span>
        <span class="brand-subtitle">Operational Incident Memory</span>
    </div>
    <div style="display:flex; gap:10px; align-items:center;">
        <span class="status-badge badge-prod">Production</span>
        <span class="status-badge badge-memory-active">● Hindsight Memory Active</span>
        <span class="status-badge badge-prod" style="font-family:monospace;">{current_incident.incident_id}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Incident Hero Summary
sev_val = current_incident.severity.value if hasattr(current_incident.severity, 'value') else current_incident.severity
sev_badge = "badge-sev1" if "SEV-1" in sev_val else "badge-sev2"
status_badge = "badge-status" if current_incident.status == "INVESTIGATING" else "badge-resolved"

st.markdown(f"""
<div class="hero-card">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
        <div>
            <span class="status-badge {sev_badge}">{sev_val}</span>
            <span class="status-badge {status_badge}">{current_incident.status}</span>
            <span class="status-badge badge-service">{current_incident.affected_service}</span>
            <h2 style="margin: 8px 0 4px 0; color:#f8fafc; font-size:24px;">[{current_incident.incident_id}] {current_incident.title}</h2>
            <p style="color:#94a3b8; font-size:14px; margin:0;">
                Production {current_incident.affected_service} requests are experiencing high latency and gateway degradation following recent release activities.
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 4 Key Signals Strip
sig1, sig2, sig3, sig4 = st.columns(4)

# Signal 1: p99 Latency
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

# Signal 2: Error Rate
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

# Signal 3: Resource / Connection Saturation
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

# Signal 4: Recent Change / Trigger
with sig4:
    trig = current_incident.triggers[0] if current_incident.triggers else None
    trig_title = trig.description.split("deployed")[0] if trig and "deployed" in trig.description else "Recent Change"
    trig_time = trig.timestamp if trig else "Unknown"
    st.markdown(f"""
    <div class="signal-card">
        <div class="signal-label">Recent Change</div>
        <div class="signal-value" style="font-size:16px; margin-top:6px; color:#38bdf8;">Release v2.4.5</div>
        <div style="font-size:12px; color:#94a3b8;">Detected 14 min prior to alert</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# Optional collapsible details for raw logs & timeline
with st.expander("Reported Symptoms & Detailed Telemetry"):
    c_sym1, c_sym2 = st.columns(2)
    with c_sym1:
        st.markdown("**Observable Error Signatures:**")
        for s in current_incident.symptoms:
            st.markdown(f"- `{s}`")
    with c_sym2:
        st.markdown("**Incident Timeline & Investigation Steps:**")
        for stp in current_incident.investigation_steps:
            st.markdown(f"- {stp}")

st.write("")

# =========================================================================
# MEMORY VS NO MEMORY (DEMO TOGGLE)
# =========================================================================
col_ctl1, col_ctl2 = st.columns([2, 1])
with col_ctl1:
    st.markdown("### Team Memory & Investigation Analysis")
with col_ctl2:
    agent_mode = st.radio(
        "Investigation Mode:",
        ["WITH_HINDSIGHT_MEMORY", "WITHOUT_MEMORY"],
        format_func=lambda x: "WITH TEAM MEMORY" if x == "WITH_HINDSIGHT_MEMORY" else "WITHOUT MEMORY",
        horizontal=True
    )

# Execute Agent Reasoning
historical_pool = inc_manager.get_historical_pool()
with st.spinner("Analyzing incident context..."):
    report = agent.investigate(
        incident=current_incident,
        mode=agent_mode,
        historical_pool=historical_pool
    )

st.write("")

# =========================================================================
# STEP 2 & 3: HAVE WE SEEN THIS BEFORE? & WHAT DID WE LEARN?
# =========================================================================
if agent_mode == "WITH_HINDSIGHT_MEMORY":
    # Visual Centerpiece: Team Memory Match
    st.markdown("""
    <div class="memory-panel">
        <div class="match-header">
            <div>
                <span style="font-size:18px; font-weight:700; color:#f8fafc;">TEAM MEMORY</span>
                <span style="color:#94a3b8; font-size:13px; margin-left:8px;">Relevant experience from your organization's previous incidents</span>
            </div>
            <span class="match-tag">STRONG HISTORICAL MATCH</span>
        </div>
        <p style="color:#cbd5e1; font-size:14px; margin: 4px 0 12px 0;">
            <b>RecallOps found relevant organizational precedent in INC-101:</b> 
            Post-release latency spike caused by PostgreSQL connection pool exhaustion.
        </p>
        <div style="background-color:rgba(15, 23, 42, 0.7); border:1px solid #1e293b; border-radius:4px; padding:10px 14px; margin-bottom:12px;">
            <div style="font-size:12px; font-weight:600; text-transform:uppercase; color:#94a3b8; margin-bottom:6px;">Evidence Supporting Relevance:</div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:6px; font-size:13px; color:#e2e8f0;">
                <div>✓ <b>Same Affected Service:</b> checkout-service</div>
                <div>✓ <b>Matching Telemetry Pattern:</b> Latency surge to >5000ms with 504 timeouts</div>
                <div>✓ <b>Identical Trigger Vector:</b> Outage occurred within 20m of service release</div>
                <div>✓ <b>Resource Correlation:</b> Database connection pool ceiling saturation (88% vs 100%)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # What Happened in the Historical Incident: What Failed vs What Worked
    st.markdown("#### Past Incident Experience (INC-101)")
    
    col_exp_left, col_exp_right = st.columns([1, 1])

    with col_exp_left:
        st.markdown("**What Engineers Attempted & What Failed:**")
        st.markdown("""
        <div class="panel-failed">
            <b style="color:#f87171;">Action Attempt: Scaled pod deployment from 4 to 12 replicas</b><br>
            <span style="font-size:13px; color:#fecdd3;"><b>Result:</b> Failed — Each new pod opened 25 database connections; overwhelmed PgBouncer, caused connection resets, and increased p99 latency to 8.2s.</span>
        </div>
        <div class="panel-failed">
            <b style="color:#f87171;">Action Attempt: Increased ingress gateway timeout from 5s to 15s</b><br>
            <span style="font-size:13px; color:#fecdd3;"><b>Result:</b> Failed — Requests accumulated longer, causing upstream gateway thread pool exhaustion.</span>
        </div>
        """, unsafe_allow_html=True)

    with col_exp_right:
        st.markdown("**What Succeeded & Root Cause Discovered:**")
        st.markdown("""
        <div class="panel-worked">
            <b style="color:#34d399;">Successful Intervention: Terminated blocking lock query PID</b><br>
            <span style="font-size:13px; color:#a7f3d0;"><b>Result:</b> Active connection queue drained from 100 to 28; p99 latency recovered to 210ms in 90 seconds.</span>
        </div>
        <div class="panel-worked">
            <b style="color:#34d399;">Successful Intervention: Capped per-pod connection limit to 8</b><br>
            <span style="font-size:13px; color:#a7f3d0;"><b>Result:</b> Enforced strict ceiling per pod to prevent cascading database starvation.</span>
        </div>
        <div class="panel-neutral" style="border-left: 4px solid #64748b;">
            <b style="color:#f1f5f9;">Root Cause Identified in Postmortem:</b><br>
            <span style="font-size:13px; color:#cbd5e1;">Release introduced an unindexed query with exclusive row locks on checkout tables, holding open connections under concurrent traffic.</span>
        </div>
        """, unsafe_allow_html=True)

else:
    # WITHOUT MEMORY: Reasonable generic analysis without organizational context
    st.markdown("""
    <div class="memory-panel" style="border-top:3px solid #64748b;">
        <div class="match-header">
            <div>
                <span style="font-size:18px; font-weight:700; color:#f8fafc;">Standard Assistant</span>
                <span style="color:#94a3b8; font-size:13px; margin-left:8px;">Analyzing incident from first principles without organizational memory</span>
            </div>
            <span class="status-badge badge-prod">NO MEMORY ACCESSED</span>
        </div>
        <p style="color:#cbd5e1; font-size:14px; margin: 4px 0;">
            No organizational incident history available. Evaluating observable telemetry from current symptoms.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Generic Diagnostic Assessment")
    st.markdown("""
    <div class="panel-neutral">
        <b style="color:#f8fafc;">Observable Factors:</b><br>
        <span style="font-size:13px; color:#cbd5e1;">
        - High database connection utilization (88%) suggests backend saturation or long-running transactions.<br>
        - Recent release v2.4.5 deployed 14 minutes prior correlates with latency spike.<br>
        - Ingress gateway 504 timeouts indicate upstream request deadlines exceeded.
        </span>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# =========================================================================
# STEP 4: WHAT SHOULD THE ENGINEER INVESTIGATE NOW?
# =========================================================================
st.markdown("### Recommended Investigation")
st.caption("Advisory only: Evidence-backed investigation steps. Production changes require engineer approval.")

col_inv_left, col_inv_right = st.columns([1, 1])

with col_inv_left:
    st.markdown("**Ranked Investigation Steps:**")
    if agent_mode == "WITH_HINDSIGHT_MEMORY":
        st.markdown("""
        1. **Inspect PostgreSQL connection pool utilization & active locks**  
           *Historical precedent indicates lock contention is the primary failure mode during post-release latency.*
        2. **Compare v2.4.5 database queries against INC-101**  
           *Verify if newly introduced calculations hold exclusive table or row locks.*
        3. **Verify per-pod connection limits**  
           *Ensure pod connection ceilings are enforced to prevent PgBouncer overload.*
        """)
        st.markdown("""
        <div class="panel-neutral" style="border-left: 3px solid #0ea5e9;">
            <b style="color:#38bdf8;">Why RecallOps Recommends This:</b><br>
            <span style="font-size:13px; color:#cbd5e1;">
            Historical incidents with the same service and deployment trigger confirmed that database connection saturation caused by unindexed row locks was the recurring root cause. Scaling application pods failed previously.
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        1. **Inspect database connection utilization**  
           *Check active connection count against configured pool limits.*
        2. **Inspect recent commit changes in release v2.4.5**  
           *Review git log for newly introduced database queries or configuration alterations.*
        3. **Inspect ingress gateway logs**  
           *Check failing URI paths and upstream timeout errors.*
        """)
        st.markdown("""
        <div class="panel-neutral" style="border-left: 3px solid #64748b;">
            <b style="color:#94a3b8;">Why This Is Recommended:</b><br>
            <span style="font-size:13px; color:#cbd5e1;">
            General DevOps heuristics associate concurrent latency surges and 504 timeouts with downstream database saturation or release regressions.
            </span>
        </div>
        """, unsafe_allow_html=True)

with col_inv_right:
    st.markdown("**Safe Diagnostic Verification (Read-Only):**")
    if agent_mode == "WITH_HINDSIGHT_MEMORY":
        st.markdown("Check for active long-running queries holding transaction locks:")
        st.code("""SELECT pid, now() - query_start AS duration, state, query 
FROM pg_stat_activity 
WHERE state != 'idle' 
ORDER BY duration DESC LIMIT 5;""", language="sql")
        st.caption("Component: postgres-primary | Rationale: Proven diagnostic in INC-101 to find blocking query PID.")
        
        st.markdown("**Proposed Remediation Plan:**")
        st.markdown("- **Step:** Terminate blocking lock PID via `SELECT pg_terminate_backend(pid)` and verify connection pool normalization.")
        st.markdown("- **Precedent:** Successfully resolved INC-101 and recovered p99 latency back to 210ms in 90 seconds.")
        st.checkbox("Authorize remediation plan (Engineer sign-off required)", key="auth_remediation")
    else:
        st.markdown("General diagnostic command to inspect active connections:")
        st.code("""SHOW max_connections;
SELECT count(*) FROM pg_stat_activity;""", language="sql")
        st.caption("Component: database-pool | Rationale: Basic connection count verification.")
        
        st.markdown("**Generic Remediation Options:**")
        st.markdown("- **Option A:** Rollback release v2.4.5 to v2.4.4 if database saturation is directly tied to the new release.")
        st.markdown("- **Option B:** Restart application service pods to clear connection states.")
        st.checkbox("Authorize generic remediation option", key="auth_remediation_generic")

st.write("")
st.markdown("---")

# =========================================================================
# STEP 5: WHAT WILL RECALLOPS REMEMBER? (MEMORY LIFECYCLE & RETENTION)
# =========================================================================
st.markdown("### What RecallOps Will Remember")
st.caption("The continuous memory loop: Resolving an incident commits verified experience into Hindsight for future on-call response.")

col_ret_info, col_ret_act = st.columns([1, 1])

with col_ret_info:
    st.markdown("""
    <div class="panel-neutral" style="border-left: 3px solid #10b981;">
        <b style="color:#34d399;">Experience Prepared for Retention:</b><br>
        <span style="font-size:13px; color:#cbd5e1;">
        • Release v2.4.5 was associated with database connection pool exhaustion on checkout-service.<br>
        • Increasing application replicas did not resolve the incident (anti-pattern).<br>
        • Terminating the unindexed query PID and capping pool limits normalized latency.<br>
        • Verified recovery: p99 latency restored to baseline within 90 seconds.
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"Target Memory Bank: `{mem_adapter.bank_id}` (Persistent)")

with col_ret_act:
    st.markdown("**Incident Resolution Action:**")
    with st.form("resolve_incident_form"):
        f_root_cause = st.text_input(
            "Confirmed Root Cause:",
            value=current_incident.root_cause or "Release v2.4.5 multi-currency calculation held exclusive row locks on exchange_rates without compound index."
        )
        f_fix = st.text_input(
            "Final Resolution:",
            value=current_incident.final_resolution or "Terminated blocking query PID, added compound index on (currency, effective_date), capped pool size to 8 per pod."
        )
        f_time = st.number_input("Recovery Time (Minutes):", min_value=1, max_value=300, value=current_incident.recovery_time_minutes or 24)
        
        submit_btn = st.form_submit_button("RESOLVE INCIDENT & REMEMBER", use_container_width=True)

        if submit_btn:
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
                    root_cause=f_root_cause,
                    final_resolution=f_fix,
                    recovery_time_minutes=f_time,
                    actions_attempted=attempts,
                    lessons_learned=lessons_list,
                )
            st.success(f"Incident {current_incident.incident_id} marked as RESOLVED and committed to Hindsight memory bank '{mem_adapter.bank_id}'. Future incidents can now recall this experience!")
            st.rerun()

st.write("")

# =========================================================================
# SECONDARY DRAWER: ORGANIZATIONAL KNOWLEDGE BASE
# =========================================================================
with st.expander("Organizational Incident History & Hindsight Inspector"):
    st.markdown("Browse all postmortems and action experiences indexed in Hindsight.")
    
    all_mem = mem_adapter.list_all_memories()
    c_k1, c_k2 = st.columns([1, 2])
    with c_k1:
        type_filter = st.selectbox("Record Type:", ["ALL", "postmortem", "action_experience", "lessons_learned"])
    with c_k2:
        search_kw = st.text_input("Search:", "")

    filtered = all_mem
    if type_filter != "ALL":
        filtered = [m for m in filtered if m.get("metadata", {}).get("type") == type_filter]
    if search_kw:
        filtered = [m for m in filtered if search_kw.lower() in m.get("content", "").lower()]

    st.caption(f"Showing {len(filtered)} of {len(all_mem)} indexed records")
    for m in filtered[:6]:
        doc_id = m.get("document_id", "DOC")
        m_type = m.get("metadata", {}).get("type", "record")
        st.markdown(f"**[{doc_id}]** `{m_type.upper()}`")
        st.text(m.get("content", "")[:220] + "...")
