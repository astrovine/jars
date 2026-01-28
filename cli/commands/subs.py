import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from ..client import client
from ..config import Theme

app = typer.Typer(name="subs", help="Subscription commands")
console = Console()


@app.command(name="list")
def list_subs(all: bool = typer.Option(False, "--all", "-a", help="Include inactive")):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading...[/]"):
            subs = client.get_subscriptions(active_only=not all)
        
        table = Table(border_style=Theme.BORDER)
        table.add_column("ID", style=Theme.MUTED, max_width=8)
        table.add_column("Trader", style=Theme.PRIMARY)
        table.add_column("Allocation", justify="right")
        table.add_column("Status")
        
        for s in subs:
            status = s.get("status", "")
            style = Theme.ONLINE if status == "active" else Theme.WARNING if status == "paused" else Theme.MUTED
            
            table.add_row(
                str(s.get("id", ""))[:8],
                s.get("trader_alias", str(s.get("trader_id", ""))[:8]),
                f"{s.get('allocation_amount', 0):,.2f}",
                f"[{style}]{status}[/]"
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def get(sub_id: str):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading...[/]"):
            s = client.get_subscription(sub_id)
        
        table = Table(show_header=False, border_style=Theme.BORDER, box=None)
        table.add_column("", style=Theme.MUTED)
        table.add_column("", style=Theme.PRIMARY)
        
        table.add_row("ID", str(s.get("id", "")))
        table.add_row("Trader", s.get("trader_alias", str(s.get("trader_id", ""))))
        table.add_row("Allocation", f"{s.get('allocation_amount', 0):,.2f}")
        table.add_row("Status", s.get("status", ""))
        table.add_row("Created", str(s.get("created_at", ""))[:10])
        
        console.print(Panel(table, title="Subscription", border_style=Theme.BORDER))
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def follow(trader_id: str, allocation: float):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Following...[/]"):
            client.follow_trader(trader_id, allocation)
        console.print(f"[{Theme.ONLINE}]✓[/] Now following trader")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def unfollow(sub_id: str):
    console.print()
    confirm = Prompt.ask(f"[{Theme.WARNING}]Unfollow?[/]", choices=["y", "n"])
    
    if confirm != "y":
        console.print(f"[{Theme.MUTED}]Cancelled[/]")
        return
    
    try:
        with console.status(f"[{Theme.MUTED}]Unfollowing...[/]"):
            client.unfollow_trader(sub_id)
        console.print(f"[{Theme.ONLINE}]✓[/] Subscription cancelled")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def pause(sub_id: str, reason: str = ""):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Pausing...[/]"):
            client.pause_subscription(sub_id, reason)
        console.print(f"[{Theme.WARNING}]⏸[/] Subscription paused")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def resume(sub_id: str):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Resuming...[/]"):
            client.resume_subscription(sub_id)
        console.print(f"[{Theme.ONLINE}]▶[/] Subscription resumed")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def tier():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading...[/]"):
            data = client.get_tier_info()
        
        table = Table(show_header=False, border_style=Theme.BORDER, box=None)
        table.add_column("", style=Theme.MUTED)
        table.add_column("", style=Theme.PRIMARY)
        
        table.add_row("Tier", data.get("tier_name", data.get("tier", "FREE")))
        table.add_row("Max Follows", str(data.get("max_follows", data.get("max_subscriptions", 1))))
        table.add_row("Status", data.get("status", data.get("tier_status", "")))
        
        console.print(Panel(table, title="Tier Info", border_style=Theme.BORDER))
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def subscribers(all: bool = typer.Option(False, "--all", "-a")):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading...[/]"):
            subs = client.get_subscribers(active_only=not all)
        
        table = Table(border_style=Theme.BORDER)
        table.add_column("User", style=Theme.PRIMARY)
        table.add_column("Allocation", justify="right")
        table.add_column("Since", style=Theme.MUTED)
        table.add_column("Status")
        
        for s in subs:
            status = s.get("status", "")
            style = Theme.ONLINE if status == "active" else Theme.MUTED
            
            table.add_row(
                s.get("copier_email", str(s.get("copier_id", ""))[:8]),
                f"{s.get('allocation_amount', 0):,.2f}",
                str(s.get("created_at", ""))[:10],
                f"[{style}]{status}[/]"
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()
