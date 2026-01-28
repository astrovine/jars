import sys
import asyncio
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
import pyfiglet

from .config import Theme
from .client import client, JarsApiError
from .session import session
from .commands import auth_app, user_app, wallet_app, traders_app, subs_app, keys_app, payments_app

console = Console()


style = Style.from_dict({
    "prompt": f"bold {Theme.PRIMARY}",
    "input": "#ffffff",
    "bottom-toolbar": f"bg:#333333 #ffffff",
})

bindings = KeyBindings()

@bindings.add(Keys.Escape)
def _(event):
    event.app.exit(result="exit")

@bindings.add(Keys.ControlC)
def _(event):
    event.app.exit(result="exit")

from .shortcuts import resolve_alias



from rich import box
from rich.layout import Layout

def render_massive_splash(user: Optional[dict] = None) -> bool:
    console.clear()

    fonts_to_try = ["ansi_shadow"]
    logo = ""
    for f in fonts_to_try:
        try:
            logo = pyfiglet.figlet_format("JARS", font=f)
            if logo.strip(): break
        except: continue
            
    console.print("\n" * 2)
    
    lines = logo.split("\n")
    styled_logo = Text()
    
    colors = ["#ffffff", "#cfd8dc", "#b0bec5", "#90a4ae", "#78909c", "#607d8b", "#546e7a", "#455a64"]
    
    for i, line in enumerate(lines):
        if not line.strip(): continue
        color = colors[i % len(colors)]
        styled_logo.append(line + "\n", style=f"bold {color}")

    console.print(Align.center(styled_logo))
    console.print("\n")

    if user:
        email = user.get("email", "User")
        greeting = f"[bold white]Welcome back, {email}[/]"
        action = "[blink]Press Enter to Continue...[/]"
    else:
        greeting = "[bold white]INFRASTRUCTURE FOR COPY TRADING[/]"
        action = "[blink]Press Enter to Log In...[/]"

    console.print(Align.center(greeting))
    console.print(Align.center(f"[{Theme.MUTED}]v2.0.1 • Interactive Session[/]"))
    console.print("\n" * 2)
    
    console.print(Align.center(action))
    input()
    
    console.clear()
    
    if not user:
        return True
    
    welcome_panel = Panel(
        Align.center(
            f"[{Theme.PRIMARY} bold]JARS TERMINAL V2.0[/]\n"
            f"[white]Interactive Session Active[/]\n\n"
            f"[dim]Tips for getting started:[/]\n"
            f"[dim]1. Type [bold white]help[/] to see available commands.[/]\n"
            f"[dim]2. Use aliases like [bold white]al[/] (login) or [bold white]wb[/] (balance).[/]\n"
            f"[dim]3. Press [bold white]Esc[/] to quit at any time.[/]",
        ),
        box=box.ROUNDED,
        style=f"{Theme.ONLINE}",
        border_style=f"{Theme.ONLINE}",
        padding=(1, 4),
        title="[bold]SYSTEM ONLINE[/]",
        title_align="center",
    )
    console.print(Align.center(welcome_panel))
    console.print()
    return False

def get_bottom_toolbar():
    api_status = "API: ●" 
    auth_status = "Auth: " + (session.current_user.get("email") if session.current_user else "Guest")
    
    return HTML(f" <b>{api_status}</b> | <b>{auth_status}</b> | <style bg='#ff0000' fg='white'> [Esc] Quit </style> ")

def dispatch_command(cmd_input: str):
    if not cmd_input.strip():
        return

    full_cmd = resolve_alias(cmd_input)
    parts = full_cmd.split()
    cmd = parts[0].lower()
    args = parts[1:]

    console.print()
    
    if cmd in ["exit", "quit"]:
        return False

    try:
        if cmd == "help":
            from rich.table import Table
            
            from rich.table import Table
            
            table = Table(title=f"[{Theme.PRIMARY} bold]JARS COMMAND REFERENCE[/]", box=box.ROUNDED, expand=True)
            table.add_column("Category", style=f"{Theme.MUTED}")
            table.add_column("Command", style="bold white")
            table.add_column("Alias/Arg", style="cyan")
            table.add_column("Description", style="dim")

            def add_cat(cat, cmds):
                for i, c in enumerate(cmds):
                    table.add_row(cat if i == 0 else "", c[0], c[1], c[2])
                table.add_section()

            add_cat("Authentication", [
                ("auth login", "al", "Log in to your account"),
                ("auth register", "ar", "Create an account"),
                ("auth logout", "alo", "Log out of session"),
                ("auth logout-all", "ala", "Log out everywhere"),
                ("auth 2fa-setup", "a2s", "Enable 2FA security"),
                ("auth 2fa-verify", "a2v <code>", "Verify 2FA code"),
                ("auth password-reset", "apr", "Request reset email"),
                ("auth whoami", "who", "Current session info"),
            ])
            
            add_cat("Wallet", [
                ("wallet balance", "wb", "View active balance"),
                ("wallet summary", "ws", "View deposits/withdrawals/PnL"),
                ("wallet history", "wh", "View transaction history"),
                ("wallet deposit", "wd", "Initialize a deposit"),
                ("wallet verify-deposit", "wvd <ref>", "Check deposit status"),
                ("wallet banks", "wba", "List supported banks"),
            ])

            add_cat("Virtual Wallet", [
                ("wallet virtual-status", "wvs", "Check reset eligibility"),
                ("wallet virtual-reset-free", "wvrf", "Reset balance (Free)"),
                ("wallet virtual-reset-paid", "wvrp", "Reset balance ($5.00)"),
            ])

            add_cat("Copy Trading", [
                ("traders list", "tl", "List top performing traders"),
                ("traders profile", "tp <id>", "View specific trader details"),
                ("traders apply", "ta", "Apply to become a trader"),
                ("traders me", "tm", "Manage your profile"),
                ("traders kyc", "tk", "View KYC status"),
                ("traders kyc-submit", "tks", "Upload ID documents"),
                ("traders update", "tu", "Update bio/fees"),
                ("traders deactivate", "td", "Deactivate profile"),
                ("traders reactivate", "tr", "Reactivate profile"),
            ])

            add_cat("Subscriptions", [
                ("subs list", "sl", "View your active copies"),
                ("subs follow", "sf <id>", "Copy a new trader"),
                ("subs unfollow", "su <id>", "Stop copying a trader"),
                ("subs pause", "sp <id>", "Pause copying temporarily"),
                ("subs resume", "sr <id>", "Resume copying"),
                ("subs subscribers", "ss", "View who copies you"),
                ("subs tier", "st", "View subscription limits"),
            ])
            
            add_cat("Payments", [
                ("payments pricing", "pp", "View tier pricing"),
                ("payments upgrade", "pu <tier>", "Upgrade (plus/business)"),
                ("payments verify", "pv <ref>", "Verify payment"),
                ("payments banks", "pb", "List payment banks"),
            ])

            add_cat("User Settings", [
                ("user me", "um", "View profile details"),
                ("user password", "up", "Change password"),
                ("user update", "uu", "Update name/country"),
                ("user activity", "ua", "View audit logs"),
                ("user ensure-demo", "ued", "Create demo wallet"),
                ("user upgrade-plus", "uup", "Direct upgrade (Plus)"),
                ("user upgrade-business", "uub", "Direct upgrade (Biz)"),
            ])

            add_cat("API Keys", [
                ("keys list", "kl", "Manage exchange API keys"),
                ("keys add", "ka", "Link a new exchange account"),
                ("keys test", "kt <id>", "Test connection"),
                ("keys delete", "kd <id>", "Remove key"),
            ])

            console.print(table)
            console.print(f"[{Theme.MUTED}]Type any command to execute. Use aliases for speed (e.g. 'al' for 'auth login').[/]")
            console.print(f"[{Theme.MUTED}]For arguments, type the command and follow prompts, or supply them (e.g. 'wd 5000').[/]")

        elif cmd == "auth":
            _handle_typer_group(auth_app, args)
        elif cmd == "user":
            _handle_typer_group(user_app, args)
        elif cmd == "wallet":
            _handle_typer_group(wallet_app, args)
        elif cmd == "traders":
            _handle_typer_group(traders_app, args)
        elif cmd == "subs":
            _handle_typer_group(subs_app, args)
        elif cmd == "keys":
            _handle_typer_group(keys_app, args)
        elif cmd == "payments":
            _handle_typer_group(payments_app, args)
            
        elif cmd == "login":
             _handle_typer_group(auth_app, ["login"] + args)
        elif cmd == "register":
             _handle_typer_group(auth_app, ["register"] + args)
        elif cmd == "balance":
             _handle_typer_group(wallet_app, ["balance"] + args)
        elif cmd == "status":
            from .main import status
            status()

        else:
            console.print(f"[red]Unknown command: {cmd}[/]")

    except SystemExit:
        pass
    except JarsApiError as e:
        status_code_str = f"Error {e.status_code}" if e.status_code else "API Error"
        console.print(Panel(
            f"[bold white]{e.message}[/]",
            title=f"[bold red]⚠  {status_code_str}[/]",
            border_style="red",
            padding=(0, 2)
        ))
    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/]{e}")

    console.print()

def _handle_typer_group(typer_app, args):
    try:
        typer_app(args, standalone_mode=False)
    except SystemExit:
        pass 
    except Exception as e:
        console.print(f"[red]Command Error:[/]{e}")

async def run_repl():
    token = client.load_token()
    is_logged_in = False
    
    if token:
        try:
            me = client.get_me()
            session.set_user(me)
            is_logged_in = True
        except:
            session.clear_user()
            
    user_obj = me if is_logged_in else None
    should_login = render_massive_splash(user_obj)
    
    if should_login:
        dispatch_command("auth login")

    prompt_session = PromptSession(style=style)

    while True:
        try:
            cmd_input = await prompt_session.prompt_async(
                HTML(f"<b>{session.get_prompt_symbol()}</b>"),
                bottom_toolbar=get_bottom_toolbar(),
                key_bindings=bindings,
            )
            
            should_continue = dispatch_command(cmd_input)
            if should_continue is False:
                break
            
        except (EOFError, KeyboardInterrupt):
            break
            
    console.print("[bold cyan]Exiting JARS... See you space cowboy.[/]")


if __name__ == "__main__":
    asyncio.run(run_repl())
