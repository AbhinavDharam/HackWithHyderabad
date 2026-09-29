<p align="center">
  <img src="assets/logo.png" alt="RecallOps Logo" width="220" />
</p>

# RecallOps

> **AI Incident Response Assistant with Persistent SRE Organizational Memory**  
> *Built for Hack with Hyderabad 3.0 — Powered by Hindsight (Vectorize)*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Memory: Hindsight](https://img.shields.io/badge/Memory-Hindsight%20(Vectorize)-brightgreen)](https://hindsight.vectorize.io/)
[![LLM: Groq / Llama-3.3](https://img.shields.io/badge/LLM-Groq%20%7C%20Llama--3.3-orange)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 🎯 The Problem

When production outages strike—APIs timing out, connection pools saturating, cache stampedes crashing databases—on-call engineers face two grueling challenges:
1. **Investigating unfamiliar telemetry under extreme pressure.**
2. **Remembering if the organization experienced this failure before, what worked, and what made things worse.**

Most AI chatbots treat memory as a glorified chat history. They provide generic advice (*"Have you tried restarting the pods or scaling out replicas?"*). But in complex distributed architectures, **generic advice can turn a minor degradation into a catastrophic total outage**.

---

## 💡 The Solution: RecallOps

**RecallOps** is an intelligent Incident Response Agent where **Hindsight persistent memory is the hero**. It accumulates institutional SRE wisdom over time, learning not just what happened, but **distinguishing between actions that failed, actions that proved ineffective, and actions that actually resolved the incident**.

When a new incident occurs, RecallOps:
1. Recalls relevant historical incidents using multi-signal contextual relevance.
2. Explains **why** they are relevant (no black-box vector dumps).
3. Warns against **anti-patterns and previous failed actions** (*"DO NOT scale replicas; in INC-101 this overwhelmed the database connection pool"*).
4. Recommends **safe, read-only diagnostic checks** to verify root causes.
5. Suggests **evidence-backed mitigations** requiring human sign-off.
6. Learns continuously by committing new postmortems and investigation journeys back into Hindsight.

---

## 🏆 Hackathon Value & Judging Alignment

| Hackathon Criterion | Weight | How RecallOps Delivers |
| :--- | :---: | :--- |
| **Innovation** | **30%** | Moves beyond conversational chatbots into an advisory SRE copilot that tracks *action-outcome causality* (Failed vs. Effective vs. Succeeded). |
| **Use of Hindsight Memory** | **25%** | Hindsight is the central nervous system: memory units are decomposed into postmortems, action experiences, and runbook anti-patterns using `retain`, `recall` (TEMPR), and `reflect`. |
| **Technical Implementation** | **20%** | Clean modular architecture (`/models`, `/memory`, `/retrieval`, `/agent`, `/llm`), multi-signal relevance scoring, Pydantic schemas, resilient cloud/local fallback, and automated unit test suite. |
| **User Experience** | **15%** | Intuitive Streamlit workbench featuring real-time telemetry, 1-click **"Before vs. After Memory"** judge demo, and an interactive Memory Brain Explorer. |
| **Real-world Impact** | **10%** | Directly targets MTTR (Mean Time to Resolution), prevents repeat engineering mistakes, and preserves institutional memory when engineers change teams. |

---

## 🏗️ Architecture

```
                                  +-------------------------------------+
                                  |     Streamlit SRE Workbench (app.py)|
                                  +------------------+------------------+
                                                     |
                                                     v
                                  +-------------------------------------+
                                  |      RecallOps SRE Agent (/agent)   |
                                  +------------------+------------------+
                                                     |
                   +---------------------------------+---------------------------------+
                   |                                                                   |
                   v                                                                   v
+--------------------------------------+                             +--------------------------------------+
|  Multi-Signal Relevance Engine       |                             |     Hindsight Memory Adapter         |
|  - Service Topology Match (25%)      |                             |     - Bank: recallops-vault          |
|  - Symptom TEMPR Match (35%)         |                             |     - retain() / recall() / reflect()|
|  - Trigger Context Match (20%)       |                             |     - Action-Outcome Decomposition   |
|  - Metric Profile Match (20%)        |                             |     - Resilient Offline Mirror       |
+--------------------------------------+                             +--------------------------------------+
                   |                                                                   |
                   +---------------------------------+---------------------------------+
                                                     |
                                                     v
                                  +-------------------------------------+
                                  |   Modular LLM Engine (Groq / Llama) |
                                  +-------------------------------------+
```

---

## 🧠 Hindsight Memory Strategy

Rather than dumping monolithic postmortem documents into memory, RecallOps decomposes every incident into **three high-signal cognitive artifacts**:

1. **Postmortem Entity (`[INC-xxx-POSTMORTEM]`)**: Symptoms, metrics, triggers, root cause, and recovery time.
2. **Action-Outcome Experience Units (`[INC-xxx-ACTION-yyy]`)**:
   - Explicitly records causality:
     > *"During INC-101 on checkout-service, action 'scaling replicas to 12' FAILED because DB connection pool became exhausted. Successful action was 'terminating blocking query PID 89104 and setting statement_timeout'."*
   - Categorized by outcome tags: `action:failed`, `action:ineffective`, `action:successful`.
3. **Runbook Rules & Anti-Patterns (`[INC-xxx-LESSONS]`)**:
   - Preserves institutional guardrails across the entire engineering organization.

---

## 🔬 The 60-Second Hackathon Demo Flow

1. **Step 1: The Outage (INC-105)**
   - Production alert: `checkout-service` p99 latency spikes from 195ms to 4900ms with HTTP 504 timeouts 14 minutes after deploying release v2.4.5.
2. **Step 2: Without Memory (Cold Start)**
   - Select **"🛑 Without Memory (Cold Start)"** in Tab 1 or Tab 2.
   - The generic agent advises: *"Scale checkout-service pods from 4 to 12"*.
   - **The Trap**: The engineer does not know that this exact action caused a cascading crash 14 days ago!
3. **Step 3: With Hindsight Memory (The Wow Factor)**
   - Switch to **"⚡ With Hindsight Memory"**.
   - RecallOps matches **INC-101 at 96% relevance** and explains the exact reasoning.
   - **Critical Red Warning**: *"DO NOT scale replicas! In INC-101 this caused PgBouncer connection resets and prolonged the outage."*
   - **Pinpointed Fix**: Run `SELECT pid, state, query FROM pg_stat_activity` to find the blocking unindexed lock and kill it.
4. **Step 4: Continuous Learning**
   - Head to **Tab 3 (Debrief Studio)**: Mark INC-105 resolved, enter the findings, and click **"Resolve & Retain into Hindsight"**.
   - Head to **Tab 4 (Brain Inspector)**: Watch Hindsight's memory bank expand dynamically with new action experiences!

---

## 🚀 Quickstart Guide

### 1. Prerequisites & Installation
```bash
git clone https://github.com/your-username/recallops.git
cd "Hyderabad Hackathon"

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(RecallOps includes a built-in deterministic SRE reasoning engine and local memory mirror out-of-the-box, so it runs smoothly even before adding API keys!)*

To enable live Cloud LLM and Hindsight Cloud:
- **Groq API Key**: Get a free key at [groq.com](https://groq.com/)
- **Hindsight Cloud**: Use promo code `MEMHACK99` for $50 free credits at [ui.hindsight.vectorize.io](https://ui.hindsight.vectorize.io)

### 3. Bootstrap Hindsight Memory Bank
Ingest realistic historical incident data into Hindsight:
```bash
python seed_memory.py
```

### 4. Launch Streamlit SRE Workbench
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 5. CLI Investigation Mode
You can also run triage directly from the terminal:
```bash
# With Hindsight persistent memory
python recallops/cli.py --incident INC-105 --mode memory

# Without memory (Cold Start comparison)
python recallops/cli.py --incident INC-105 --mode cold
```

---

## 🧪 Running Automated Tests

Run the built-in test suite:
```bash
python tests/test_recallops.py
```

---

## 📁 Repository Layout

```text
Hyderabad Hackathon/
├── app.py                         # Streamlit Interactive SRE Workbench
├── seed_memory.py                 # CLI Seeder for Hindsight memory bank
├── requirements.txt               # Dependencies
├── .env.example                   # Environment template
├── data/
│   └── synthetic_incidents.json   # Realistic production incident dataset
├── recallops/
│   ├── config.py                  # System & API configuration
│   ├── cli.py                     # Command-line investigation tool
│   ├── models/                    # Pydantic data schemas
│   │   ├── incident.py            # Incident, ActionAttempt, ActionOutcome
│   │   └── memory_record.py       # RelevanceScoreBreakdown, HistoricalMatch
│   ├── memory/                    # Hindsight memory subsystem
│   │   ├── hindsight_adapter.py   # Hindsight retain/recall/reflect wrapper
│   │   └── memory_formatter.py    # Incident cognitive decomposition
│   ├── retrieval/                 # Multi-signal relevance engine
│   │   ├── relevance_engine.py    # 4-signal weighted scoring
│   │   └── explanation_builder.py # Transparent rationale generator
│   ├── agent/                     # Incident response reasoning
│   │   ├── sre_agent.py           # Investigation orchestrator
│   │   └── prompt_templates.py    # Citation & anti-pattern prompts
│   ├── incidents/
│   │   └── incident_manager.py    # Incident persistence & resolution
│   └── llm/
│       └── llm_client.py          # Modular Groq/OpenAI client
└── tests/
    └── test_recallops.py          # Unit & integration test suite
```

---

## 👥 Hackathon Team

- **Product & SRE Ideation:** Leading the architectural vision and problem framing.
- **Technical Implementation:** Built with Python, Hindsight (Vectorize), Groq, and Streamlit.
- **Hackathon:** *Hack with Hyderabad 3.0 (2026)*.
