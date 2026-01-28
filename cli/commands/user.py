import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from ..client import client
from ..config import Theme

app = typer.Typer(name="user", help="User profile commands")
console = Console()


@app.command()
def me():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading profile...[/]"):
            data = client.get_me()
        
        table = Table(show_header=False, border_style=Theme.BORDER, box=None)
        table.add_column("Field", style=Theme.MUTED)
        table.add_column("Value", style=Theme.PRIMARY)
        
        table.add_row("ID", str(data.get("id", ""))[:8])
        table.add_row("Name", f"{data.get('first_name', '')} {data.get('last_name', '')}")
        table.add_row("Email", data.get("email", "N/A"))
        table.add_row("Country", data.get("country", "N/A"))
        table.add_row("Tier", data.get("tier", "FREE"))
        table.add_row("2FA", "Enabled" if data.get("is_2fa_enabled") else "Disabled")
        table.add_row("Status", data.get("status", "N/A"))
        
        console.print(Panel(table, title="Profile", border_style=Theme.BORDER))
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def full():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading full profile...[/]"):
            data = client.get_me_full()
        
        table = Table(show_header=False, border_style=Theme.BORDER, box=None)
        table.add_column("Field", style=Theme.MUTED)
        table.add_column("Value", style=Theme.PRIMARY)
        
        table.add_row("Name", f"{data.get('first_name', '')} {data.get('last_name', '')}")
        table.add_row("Email", data.get("email", "N/A"))
        table.add_row("Tier", data.get("tier", "FREE"))
        
        if data.get("wallet_balance") is not None:
            table.add_row("Wallet", f"{data.get('wallet_currency', 'NGN')} {data.get('wallet_balance', 0):,.2f}")
        
        if data.get("trader_profile"):
            tp = data["trader_profile"]
            table.add_row("Trader Alias", tp.get("alias", ""))
        
        console.print(Panel(table, title="Full Profile", border_style=Theme.BORDER))
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def refresh():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Refreshing...[/]"):
            data = client.refresh_user_data()
        console.print(f"[{Theme.ONLINE}]✓[/] User data refreshed")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def update():
    console.print()
    first_name = Prompt.ask(f"[{Theme.PRIMARY}]First Name[/]", default="")
    last_name = Prompt.ask(f"[{Theme.PRIMARY}]Last Name[/]", default="")
    country = Prompt.ask(f"[{Theme.PRIMARY}]Country[/]", default="")
    
    data = {}
    if first_name:
        data["first_name"] = first_name
    if last_name:
        data["last_name"] = last_name
    if country:
        data["country"] = country
    
    if not data:
        console.print(f"[{Theme.MUTED}]No changes[/]")
        return
    
    try:
        with console.status(f"[{Theme.MUTED}]Updating...[/]"):
            client.update_me(data)
        console.print(f"[{Theme.ONLINE}]✓[/] Profile updated")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def delete():
    console.print()
    confirm = Prompt.ask(f"[{Theme.ERROR}]Delete your account? This is irreversible[/]", choices=["y", "n"])
    
    if confirm != "y":
        console.print(f"[{Theme.MUTED}]Cancelled[/]")
        return
    
    try:
        with console.status(f"[{Theme.MUTED}]Deleting...[/]"):
            client.delete_me()
        console.print(f"[{Theme.ONLINE}]✓[/] Account deleted")
        client.clear_token()
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def activity():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading activity...[/]"):
            logs = client.get_activity()
        
        table = Table(border_style=Theme.BORDER)
        table.add_column("Time", style=Theme.MUTED)
        table.add_column("Action", style=Theme.PRIMARY)
        table.add_column("IP", style=Theme.MUTED)
        
        for log in logs[:20]:
            table.add_row(
                str(log.get("created_at", ""))[:19],
                log.get("action", ""),
                log.get("ip_address", "")
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def password():
    console.print()
    old = Prompt.ask(f"[{Theme.PRIMARY}]Current password[/]", password=True)
    new = Prompt.ask(f"[{Theme.PRIMARY}]New password[/]", password=True)
    confirm = Prompt.ask(f"[{Theme.PRIMARY}]Confirm new password[/]", password=True)
    
    if new != confirm:
        console.print(f"[{Theme.ERROR}]✗[/] Passwords do not match")
        return
    
    try:
        with console.status(f"[{Theme.MUTED}]Updating...[/]"):
            client.change_password(old, new, confirm)
        console.print(f"[{Theme.ONLINE}]✓[/] Password updated")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command(name="upgrade")
def upgrade(tier: str = typer.Argument(..., help="plus or business")):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Upgrading...[/]"):
            if tier.lower() == "plus":
                client.upgrade_plus()
            elif tier.lower() == "business":
                client.upgrade_business()
            else:
                console.print(f"[{Theme.ERROR}]✗[/] Invalid tier: {tier}")
                return
        console.print(f"[{Theme.ONLINE}]✓[/] Upgraded to {tier.upper()}")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def downgrade():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Downgrading...[/]"):
            client.downgrade_free()
        console.print(f"[{Theme.ONLINE}]✓[/] Downgraded to FREE")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command(name="demo-wallet")
def demo_wallet():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Creating demo wallet...[/]"):
            client.ensure_demo_wallet()
        console.print(f"[{Theme.ONLINE}]✓[/] Demo wallet ready")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()
