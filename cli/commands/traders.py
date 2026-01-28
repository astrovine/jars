import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from ..client import client
from ..config import Theme

app = typer.Typer(name="traders", help="Trader profile commands")
console = Console()


@app.command(name="list")
def list_traders(limit: int = 20):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading traders...[/]"):
            traders = client.list_traders(limit=limit)
        
        table = Table(border_style=Theme.BORDER)
        table.add_column("ID", style=Theme.MUTED, max_width=8)
        table.add_column("Alias", style=Theme.PRIMARY)
        table.add_column("Fee %", justify="right")
        table.add_column("Status")
        
        for t in traders:
            status = "active" if t.get("is_active") else "inactive"
            status_style = Theme.ONLINE if t.get("is_active") else Theme.MUTED
            
            table.add_row(
                str(t.get("id", ""))[:8],
                t.get("alias", ""),
                f"{t.get('performance_fee_percentage', 0):.1f}%",
                f"[{status_style}]{status}[/]"
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def profile(trader_id: str):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading...[/]"):
            t = client.get_trader(trader_id)
        
        table = Table(show_header=False, border_style=Theme.BORDER, box=None)
        table.add_column("", style=Theme.MUTED)
        table.add_column("", style=Theme.PRIMARY)
        
        table.add_row("Alias", t.get("alias", ""))
        table.add_row("Bio", t.get("bio", "")[:50])
        table.add_row("Fee", f"{t.get('performance_fee_percentage', 0):.1f}%")
        table.add_row("Status", "Active" if t.get("is_active") else "Inactive")
        
        console.print(Panel(table, title="Trader Profile", border_style=Theme.BORDER))
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def me():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading...[/]"):
            t = client.get_my_trader_profile()
        
        table = Table(show_header=False, border_style=Theme.BORDER, box=None)
        table.add_column("", style=Theme.MUTED)
        table.add_column("", style=Theme.PRIMARY)
        
        table.add_row("Alias", t.get("alias", ""))
        table.add_row("Bio", t.get("bio", ""))
        table.add_row("Fee", f"{t.get('performance_fee_percentage', 0):.1f}%")
        table.add_row("Active", "Yes" if t.get("is_active") else "No")
        
        console.print(Panel(table, title="My Trader Profile", border_style=Theme.BORDER))
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def kyc():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading KYC...[/]"):
            k = client.get_my_kyc()
        
        table = Table(show_header=False, border_style=Theme.BORDER, box=None)
        table.add_column("", style=Theme.MUTED)
        table.add_column("", style=Theme.PRIMARY)
        
        table.add_row("Status", k.get("status", ""))
        table.add_row("Name", f"{k.get('first_name', '')} {k.get('last_name', '')}")
        table.add_row("Country", k.get("country", ""))
        
        console.print(Panel(table, title="My KYC", border_style=Theme.BORDER))
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def apply():
    console.print()
    alias = Prompt.ask(f"[{Theme.PRIMARY}]Trader Alias[/]")
    bio = Prompt.ask(f"[{Theme.PRIMARY}]Bio[/]", default="")
    fee = Prompt.ask(f"[{Theme.PRIMARY}]Performance Fee %[/]", default="10.0")
    
    try:
        with console.status(f"[{Theme.MUTED}]Applying...[/]"):
            client.apply_trader(alias, bio, float(fee))
        console.print(f"[{Theme.ONLINE}]✓[/] Trader application submitted")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def update():
    console.print()
    alias = Prompt.ask(f"[{Theme.PRIMARY}]Alias[/]", default="")
    bio = Prompt.ask(f"[{Theme.PRIMARY}]Bio[/]", default="")
    fee = Prompt.ask(f"[{Theme.PRIMARY}]Fee %[/]", default="")
    
    data = {}
    if alias:
        data["alias"] = alias
    if bio:
        data["bio"] = bio
    if fee:
        data["performance_fee_percentage"] = float(fee)
    
    if not data:
        console.print(f"[{Theme.MUTED}]No changes[/]")
        return
    
    try:
        with console.status(f"[{Theme.MUTED}]Updating...[/]"):
            client.update_trader_profile(data)
        console.print(f"[{Theme.ONLINE}]✓[/] Profile updated")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def delete():
    console.print()
    confirm = Prompt.ask(f"[{Theme.ERROR}]Delete trader profile?[/]", choices=["y", "n"])
    
    if confirm != "y":
        console.print(f"[{Theme.MUTED}]Cancelled[/]")
        return
    
    try:
        with console.status(f"[{Theme.MUTED}]Deleting...[/]"):
            client.delete_trader_profile()
        console.print(f"[{Theme.ONLINE}]✓[/] Trader profile deleted")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def deactivate():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Deactivating...[/]"):
            client.deactivate_trader()
        console.print(f"[{Theme.ONLINE}]✓[/] Trader profile deactivated")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def reactivate():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Reactivating...[/]"):
            client.reactivate_trader()
        console.print(f"[{Theme.ONLINE}]✓[/] Trader profile reactivated")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command(name="approve-kyc")
def approve_kyc(trader_id: str):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Approving...[/]"):
            client.approve_kyc(trader_id)
        console.print(f"[{Theme.ONLINE}]✓[/] KYC approved")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command(name="reject-kyc")
def reject_kyc(trader_id: str, reason: str = ""):
    console.print()
    if not reason:
        reason = Prompt.ask(f"[{Theme.PRIMARY}]Rejection reason[/]")
    
    try:
        with console.status(f"[{Theme.MUTED}]Rejecting...[/]"):
            client.reject_kyc(trader_id, reason)
        console.print(f"[{Theme.ONLINE}]✓[/] KYC rejected")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def graduate(trader_id: str):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Graduating...[/]"):
            client.graduate_trader(trader_id)
        console.print(f"[{Theme.ONLINE}]✓[/] Trader graduated")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def suspend(trader_id: str):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Suspending...[/]"):
            client.suspend_trader(trader_id)
        console.print(f"[{Theme.ONLINE}]✓[/] Trader suspended")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()
