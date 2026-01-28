import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from ..client import client
from ..config import Theme

app = typer.Typer(name="keys", help="Exchange API key commands")
console = Console()


@app.command(name="list")
def list_keys(exchange: str = typer.Option(None, "--exchange", "-e")):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading...[/]"):
            keys = client.list_keys(exchange=exchange)
        
        table = Table(border_style=Theme.BORDER)
        table.add_column("ID", style=Theme.MUTED, max_width=8)
        table.add_column("Label", style=Theme.PRIMARY)
        table.add_column("Exchange")
        table.add_column("Status")
        
        for k in keys:
            status = k.get("status", "")
            style = Theme.ONLINE if status == "active" else Theme.ERROR
            
            table.add_row(
                str(k.get("id", ""))[:8],
                k.get("label", ""),
                k.get("exchange", ""),
                f"[{style}]●[/] {status}"
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def add():
    console.print()
    exchange = Prompt.ask(f"[{Theme.PRIMARY}]Exchange[/]", choices=["binance", "bybit", "okx"])
    label = Prompt.ask(f"[{Theme.PRIMARY}]Label[/]", default="")
    api_key = Prompt.ask(f"[{Theme.PRIMARY}]API Key[/]")
    secret = Prompt.ask(f"[{Theme.PRIMARY}]API Secret[/]", password=True)
    
    try:
        with console.status(f"[{Theme.MUTED}]Adding key...[/]"):
            client.add_key(exchange, api_key, secret, label)
        console.print(f"[{Theme.ONLINE}]✓[/] Key added")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def test(key_id: str):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Testing connection...[/]"):
            result = client.test_key(key_id)
        
        if result.get("success"):
            console.print(f"[{Theme.ONLINE}]✓[/] Connection successful")
            if result.get("balance"):
                console.print(f"[{Theme.MUTED}]Balance:[/] {result.get('balance')}")
        else:
            console.print(f"[{Theme.ERROR}]✗[/] Connection failed: {result.get('error', '')}")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def delete(key_id: str):
    console.print()
    confirm = Prompt.ask(f"[{Theme.WARNING}]Delete key {key_id[:8]}?[/]", choices=["y", "n"])
    
    if confirm != "y":
        console.print(f"[{Theme.MUTED}]Cancelled[/]")
        return
    
    try:
        with console.status(f"[{Theme.MUTED}]Deleting...[/]"):
            client.delete_key(key_id)
        console.print(f"[{Theme.ONLINE}]✓[/] Key deleted")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()
