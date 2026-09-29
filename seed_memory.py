"""
RecallOps: Bootstrap Memory Bank
Seeds historical incidents from data/synthetic_incidents.json into Hindsight memory bank.
"""
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from recallops.models.incident import Incident
from recallops.memory.hindsight_adapter import HindsightAdapter
from recallops.memory.memory_formatter import MemoryFormatter

console = Console()


def seed_memory_bank(force_reset: bool = False):
    """Ingests historical incidents into Hindsight memory bank."""
    data_path = Path(__file__).parent / "data" / "synthetic_incidents.json"
    if not data_path.exists():
        console.print(f"[bold red]Data file not found at {data_path}[/bold red]")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        incidents_raw = json.load(f)

    adapter = HindsightAdapter()
    console.print(f"[bold cyan]Initializing RecallOps Memory Seeding...[/bold cyan]")
    console.print(f"Target Hindsight Bank: [yellow]{adapter.bank_id}[/yellow]")
    console.print(f"Connected to live Hindsight Cloud: [green]{adapter.is_cloud_connected()}[/green]\n")

    table = Table(title="Historical Incidents Ingested into Hindsight")
    table.add_column("Incident ID", style="bold green")
    table.add_column("Service", style="cyan")
    table.add_column("Title")
    table.add_column("Memory Units Retained", justify="right", style="yellow")
    table.add_column("Failed Actions Caught", justify="right", style="red")

    total_units = 0

    for inc_data in incidents_raw:
        incident = Incident(**inc_data)
        # Only seed resolved historical incidents as memory base
        if incident.status != "RESOLVED":
            continue

        units = MemoryFormatter.decompose_incident(incident)
        for unit in units:
            adapter.retain(
                content=unit["content"],
                document_id=unit["document_id"],
                metadata=unit["metadata"],
                tags=unit["tags"],
            )
            total_units += 1

        failed_count = len(incident.failed_actions())
        table.add_row(
            incident.incident_id,
            incident.affected_service,
            incident.title,
            str(len(units)),
            str(failed_count),
        )

    console.print(table)
    console.print(f"\n[bold green]Successfully retained {total_units} cognitive memory units into Hindsight![/bold green]")
    
    # Also save to data/baseline_memory_bank.json for cloud deployments
    baseline_path = Path(__file__).parent / "data" / "baseline_memory_bank.json"
    try:
        with open(baseline_path, "w", encoding="utf-8") as f:
            json.dump(adapter.list_all_memories(), f, indent=2)
        console.print(f"[bold cyan]Updated baseline memory file at {baseline_path}[/bold cyan]")
    except Exception as e:
        console.print(f"[yellow]Could not update baseline file: {e}[/yellow]")

    stats = adapter.get_stats()
    console.print(f"Current Memory Bank Stats: {stats}\n")


if __name__ == "__main__":
    seed_memory_bank()
