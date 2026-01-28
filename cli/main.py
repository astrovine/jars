import typer
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.table import Table
import pyfiglet

from .config import Theme
from .client import client
from .commands import auth_app, user_app, wallet_app, traders_app, subs_app, keys_app, payments_app

app = typer.Typer(
    name="jars",
    help="JARS Copy Trading CLI",
    add_completion=False,
    no_args_is_help=False,
)
console = Console()

app.add_typer(auth_app, name="auth")
app.add_typer(user_app, name="user")
app.add_typer(wallet_app, name="wallet")
app.add_typer(traders_app, name="traders")
app.add_typer(subs_app, name="subs")
app.add_typer(keys_app, name="keys")
app.add_typer(payments_app, name="payments")


def render_splash():
    logo = pyfiglet.figlet_format("JARS", font="slant")
    
    content = Text()
    for line in logo.split("\n"):
        content.append(line + "\n", style=Theme.PRIMARY)
    content.append("Copy Trading Infrastructure", style=Theme.MUTED)
    
    console.print()
    console.print(Panel(
        Align.center(content),
        border_style=Theme.BORDER,
        padding=(1, 4),
    ))


def render_status():
    table = Table(
        title="System Status",
        title_style=Theme.HEADER,
        border_style=Theme.BORDER,
        show_header=True,
        header_style=Theme.PRIMARY,
    )
    
    table.add_column("Service", style=Theme.PRIMARY)
    table.add_column("Status")
    
    health = client.health()
    api_status = health["status"]
    api_style = Theme.ONLINE if api_status == "online" else Theme.OFFLINE
    table.add_row("API", f"[{api_style}]●[/] {api_status}")
    
    token = client.load_token()
    auth_status = "authenticated" if token else "not logged in"
    auth_style = Theme.ONLINE if token else Theme.MUTED
    table.add_row("Auth", f"[{auth_style}]●[/] {auth_status}")
    
    console.print(table)
    console.print()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        import asyncio
        from .repl import run_repl
        asyncio.run(run_repl())
    else:
        pass


@app.command()
def status():
    render_status()


@app.command()
def waitlist(email: str):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Joining waitlist...[/]"):
            client.join_waitlist(email)
        console.print(f"[{Theme.ONLINE}]✓[/] Added to waitlist: {email}")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


if __name__ == "__main__":
    app()
