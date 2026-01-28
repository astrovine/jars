import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..client import client
from ..config import Theme

app = typer.Typer(name="payments", help="Payment commands")
console = Console()


@app.command()
def pricing():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading pricing...[/]"):
            data = client.get_tier_pricing()
        
        table = Table(border_style=Theme.BORDER)
        table.add_column("Tier", style=Theme.PRIMARY)
        table.add_column("Price", justify="right")
        table.add_column("Features")
        
        for tier in data.get("tiers", []):
            table.add_row(
                tier.get("name", ""),
                f"{tier.get('currency', 'NGN')} {tier.get('price', 0):,.2f}",
                tier.get("description", "")
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def upgrade(tier: str = typer.Argument(..., help="plus or business")):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Initiating upgrade...[/]"):
            result = client.initiate_tier_upgrade(tier)
        
        console.print(Panel(
            f"[{Theme.PRIMARY}]Reference:[/] {result.get('reference', 'N/A')}\n"
            f"[{Theme.PRIMARY}]Authorization URL:[/] {result.get('authorization_url', 'N/A')}",
            title="Payment Initiated",
            border_style=Theme.BORDER
        ))
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def verify(reference: str):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Verifying payment...[/]"):
            result = client.verify_payment(reference)
        
        status = result.get("status", "")
        style = Theme.ONLINE if status == "success" else Theme.ERROR
        
        console.print(f"[{style}]●[/] Payment {status}")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def banks():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading banks...[/]"):
            banks_list = client.get_payment_banks()
        
        table = Table(border_style=Theme.BORDER)
        table.add_column("Code", style=Theme.MUTED)
        table.add_column("Name", style=Theme.PRIMARY)
        
        for bank in banks_list[:30]:
            table.add_row(bank.get("code", ""), bank.get("name", ""))
        
        console.print(table)
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()
