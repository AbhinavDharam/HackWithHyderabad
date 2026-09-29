"""
RecallOps CLI Interface.
Investigate production incidents directly from the command line.
"""
import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Ensure workspace root in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from recallops.incidents.incident_manager import IncidentManager
from recallops.agent.sre_agent import SREAgent

console = Console(force_terminal=True, legacy_windows=False)


def main():
    parser = argparse.ArgumentParser(description="RecallOps CLI Incident Response Agent")
    parser.add_argument("--incident", "-i", default="INC-105", help="Incident ID to investigate (e.g. INC-105)")
    parser.add_argument(
        "--mode",
        "-m",
        choices=["memory", "cold"],
        default="memory",
        help="Investigation mode: 'memory' (with Hindsight) or 'cold' (without memory)",
    )
    args = parser.parse_args()

    inc_mgr = IncidentManager()
    incident = inc_mgr.get_by_id(args.incident)
    if not incident:
        console.print(f"[bold red]Incident {args.incident} not found![/bold red]")
        sys.exit(1)

    agent = SREAgent()
    mode = "WITH_HINDSIGHT_MEMORY" if args.mode == "memory" else "WITHOUT_MEMORY"
    historical = inc_mgr.get_historical_pool()

    console.print(f"\n[bold yellow]RecallOps CLI Triage[/bold yellow] | Mode: [bold cyan]{mode}[/bold cyan]")
    console.print(f"Incident: [bold white][{incident.incident_id}] {incident.title}[/bold white]")
    console.print(f"Service: [bold magenta]{incident.affected_service}[/bold magenta] | Severity: [bold red]{incident.severity.value if hasattr(incident.severity, 'value') else incident.severity}[/bold red]\n")

    report = agent.investigate(incident=incident, mode=mode, historical_pool=historical)

    console.print(Panel(report.status_summary, title="Status Summary", style="bold green" if mode == "WITH_HINDSIGHT_MEMORY" else "bold blue"))

    if report.historical_matches:
        table = Table(title="Relevant Historical Incidents Recalled from Hindsight")
        table.add_column("Incident ID", style="bold green")
        table.add_column("Title")
        table.add_column("Score", justify="right", style="bold yellow")
        table.add_column("Key Reasons", style="cyan")

        for m in report.historical_matches:
            reasons_str = "\n".join([f"• {r}" for r in m.relevance.reasons[:2]])
            table.add_row(m.incident.incident_id, m.incident.title, f"{int(m.relevance.composite_score * 100)}%", reasons_str)
        console.print(table)

    if report.actions_to_avoid:
        console.print("\n[bold red]🚨 CRITICAL ACTIONS TO AVOID (PAST INCIDENT MISTAKES)[/bold red]")
        for a in report.actions_to_avoid:
            console.print(f"  ❌ [bold red]{a.action}[/bold red]")
            console.print(f"     Precedent: [yellow]{a.historical_incident_id}[/yellow] — Consequence: {a.failure_impact}")

    console.print("\n[bold cyan]🎯 Ranked Diagnostic Hypotheses:[/bold cyan]")
    for hyp in report.hypotheses:
        citations = f" (Cited: {', '.join(hyp.citations)})" if hyp.citations else ""
        console.print(f"  [bold white]{hyp.rank}. {hyp.title}[/bold white] [{hyp.confidence}]{citations}")
        console.print(f"     {hyp.description}")

    console.print("\n[bold green]🔍 Recommended Safe Diagnostic Checks (Read-Only):[/bold green]")
    for c in report.next_checks:
        console.print(f"  • [bold white]{c.check_name}[/bold white] ({c.target_component})")
        console.print(f"    [dim]{c.command_or_query}[/dim]")

    console.print("\n[bold yellow]🛡️ Proposed Mitigations (Requires Human Authorization):[/bold yellow]")
    for mit in report.proposed_mitigations:
        console.print(f"  • {mit.mitigation_step}")
        if mit.historical_precedent:
            console.print(f"    [green]Precedent: {mit.historical_precedent}[/green]")
    console.print("")


if __name__ == "__main__":
    main()
