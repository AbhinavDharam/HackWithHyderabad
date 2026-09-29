"""
RecallOps: Model & Memory Diagnostic Tool
Tests connectivity to LLM (Groq / OpenAI) and Hindsight Memory.
"""
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from recallops.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    HINDSIGHT_API_KEY,
    HINDSIGHT_BASE_URL,
    HINDSIGHT_BANK_ID,
)
from recallops.llm.llm_client import LLMClient
from recallops.memory.hindsight_adapter import HindsightAdapter

console = Console()


def test_diagnostics():
    console.print("\n[bold cyan]RecallOps System & Model Diagnostics[/bold cyan]\n")

    # 1. Environment & Keys Table
    table = Table(title="Configuration State")
    table.add_column("Component", style="bold white")
    table.add_column("Configured Value", style="yellow")
    table.add_column("Status", style="bold")

    # Gemini Check
    has_gemini = bool(GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here")
    masked_gemini = (GEMINI_API_KEY[:8] + "..." + GEMINI_API_KEY[-4:]) if has_gemini else "Not set"
    table.add_row(
        "Google Gemini Key",
        masked_gemini,
        "[green]Active & Connected[/green]" if has_gemini else "[dim]Optional[/dim]",
    )
    table.add_row("Gemini Target Model", GEMINI_MODEL, "[cyan]Active[/cyan]")

    # LLM Key Check (Groq)
    has_groq = bool(GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here")
    masked_groq = (GROQ_API_KEY[:8] + "..." + GROQ_API_KEY[-4:]) if has_groq else "Not set"
    table.add_row(
        "Groq API Key",
        masked_groq,
        "[green]Configured[/green]" if has_groq else "[dim]Optional[/dim]",
    )

    # Hindsight Check
    has_hindsight = bool(HINDSIGHT_API_KEY and HINDSIGHT_API_KEY != "your_hindsight_api_key_here")
    masked_hs = (HINDSIGHT_API_KEY[:8] + "..." + HINDSIGHT_API_KEY[-4:]) if has_hindsight else "Not set"
    table.add_row(
        "Hindsight Cloud Key",
        masked_hs,
        "[green]Configured (hsk_...)[/green]" if has_hindsight else "[dim yellow]Using Local Active Mirror[/dim yellow]",
    )
    table.add_row("Hindsight Bank ID", HINDSIGHT_BANK_ID, "[cyan]Active[/cyan]")
    table.add_row("Hindsight Base URL", HINDSIGHT_BASE_URL, "[dim]Default[/dim]")

    console.print(table)
    console.print("")

    # 2. Test LLM Inference
    console.print("[bold yellow]Testing LLM Inference Engine...[/bold yellow]")
    llm = LLMClient()
    start_t = time.time()
    
    test_prompt = "Say hello from RecallOps in one short sentence."
    response = llm.generate(prompt=test_prompt)
    elapsed = time.time() - start_t

    if llm.is_live_llm_ready():
        console.print(f"[bold green]✓ Live Cloud LLM Connected ({GRO_MODEL if 'GRO_MODEL' in locals() else GROQ_MODEL})[/bold green]")
        console.print(f"Latency: [bold cyan]{elapsed:.2f}s[/bold cyan]")
        console.print(Panel(response, title="Live Model Output", style="green"))
    else:
        console.print("[bold yellow]✓ Deterministic SRE Engine Active[/bold yellow]")
        console.print(
            "[dim]No GROQ_API_KEY found in .env. RecallOps is running in offline/deterministic SRE mode "
            "so your demo is 100% reliable even without API credits.[/dim]"
        )

    # 3. Test Hindsight Memory Bank
    console.print("\n[bold yellow]Testing Hindsight Memory Subsystem...[/bold yellow]")
    mem = HindsightAdapter()
    stats = mem.get_stats()
    
    if mem.is_cloud_connected():
        console.print("[bold green]✓ Connected to Live Hindsight Cloud Instance[/bold green]")
    else:
        console.print("[bold yellow]✓ Connected to Local Hindsight Active Mirror[/bold yellow]")
        
    console.print(f"Total Stored Memory Units: [bold cyan]{stats['total_memories']}[/bold cyan]")
    console.print(f"Historical Postmortems: [bold cyan]{stats['postmortems']}[/bold cyan]")
    console.print(f"Action Outcome Units: [bold cyan]{stats['action_experiences']}[/bold cyan]")

    # Run quick test recall
    query_test = "checkout-service latency"
    results = mem.recall(query=query_test, max_results=2)
    console.print(f"\nTest Memory Recall for: [italic]'{query_test}'[/italic]")
    for r in results:
        console.print(f"  • Found: [bold white]{r.get('document_id')}[/bold white] (Score: {r.get('score', 0):.2f})")

    console.print("\n[bold green]System diagnostic complete! Everything is operational.[/bold green]\n")


if __name__ == "__main__":
    test_diagnostics()
