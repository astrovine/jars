import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from ..client import client
from ..config import Theme
from ..session import session

app = typer.Typer(name="auth", help="Authentication commands")
console = Console()


@app.command()
def login():
    console.print()
    email = Prompt.ask(f"[{Theme.PRIMARY}]Email[/]")
    password = Prompt.ask(f"[{Theme.PRIMARY}]Password[/]", password=True)
    
    try:
        with console.status(f"[{Theme.MUTED}]Authenticating...[/]"):
            result = client.login(email, password)
        
        if result.get("require_2fa"):
            console.print(f"[{Theme.WARNING}]2FA required[/]")
            code = Prompt.ask(f"[{Theme.PRIMARY}]2FA Code[/]")
            with console.status(f"[{Theme.MUTED}]Verifying...[/]"):
                result = client.verify_2fa(code, result.get("pre_auth_token", ""))
        
        me = client.get_me()
        session.set_user(me)
        first_name = me.get("first_name", "Trader")
        
        console.print(f"[{Theme.ONLINE}]✓[/] Logged in as [{Theme.PRIMARY}]{email}[/]")
        console.print(f"[{Theme.ONLINE}]Welcome back, {first_name}![/]")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def register():
    console.print()
    first_name = Prompt.ask(f"[{Theme.PRIMARY}]First Name[/]")
    last_name = Prompt.ask(f"[{Theme.PRIMARY}]Last Name[/]")
    email = Prompt.ask(f"[{Theme.PRIMARY}]Email[/]")
    country = Prompt.ask(f"[{Theme.PRIMARY}]Country[/]")
    password = Prompt.ask(f"[{Theme.PRIMARY}]Password[/]", password=True)
    confirm = Prompt.ask(f"[{Theme.PRIMARY}]Confirm Password[/]", password=True)
    
    if password != confirm:
        console.print(f"[{Theme.ERROR}]✗[/] Passwords do not match")
        return
    
    try:
        with console.status(f"[{Theme.MUTED}]Creating account...[/]"):
            client.register(first_name, last_name, email, country, password)
        console.print(f"[{Theme.ONLINE}]✓[/] Account created. Check email for verification.")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command(name="register-plus")
def register_plus():
    console.print()
    first_name = Prompt.ask(f"[{Theme.PRIMARY}]First Name[/]")
    last_name = Prompt.ask(f"[{Theme.PRIMARY}]Last Name[/]")
    email = Prompt.ask(f"[{Theme.PRIMARY}]Email[/]")
    country = Prompt.ask(f"[{Theme.PRIMARY}]Country[/]")
    password = Prompt.ask(f"[{Theme.PRIMARY}]Password[/]", password=True)
    
    try:
        with console.status(f"[{Theme.MUTED}]Creating Plus account...[/]"):
            client.register_plus(first_name, last_name, email, country, password)
        console.print(f"[{Theme.ONLINE}]✓[/] Plus account created.")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command(name="register-business")
def register_business():
    console.print()
    first_name = Prompt.ask(f"[{Theme.PRIMARY}]First Name[/]")
    last_name = Prompt.ask(f"[{Theme.PRIMARY}]Last Name[/]")
    email = Prompt.ask(f"[{Theme.PRIMARY}]Email[/]")
    country = Prompt.ask(f"[{Theme.PRIMARY}]Country[/]")
    company = Prompt.ask(f"[{Theme.PRIMARY}]Company Name[/]", default="")
    password = Prompt.ask(f"[{Theme.PRIMARY}]Password[/]", password=True)
    
    try:
        with console.status(f"[{Theme.MUTED}]Creating Business account...[/]"):
            client.register_business(first_name, last_name, email, country, password, company)
        console.print(f"[{Theme.ONLINE}]✓[/] Business account created.")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def logout():
    console.print()
    client.logout()
    console.print(f"[{Theme.MUTED}]Logged out[/]")
    console.print()


@app.command(name="logout-all")
def logout_all():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Logging out all sessions...[/]"):
            client.logout_all()
        console.print(f"[{Theme.ONLINE}]✓[/] All sessions terminated")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command(name="2fa-setup")
def setup_2fa():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Generating 2FA...[/]"):
            result = client.setup_2fa()
        
        console.print(Panel(
            f"[{Theme.PRIMARY}]Secret:[/] {result.get('secret', 'N/A')}\n"
            f"[{Theme.MUTED}]Scan the QR code in your authenticator app[/]",
            title="2FA Setup",
            border_style=Theme.BORDER
        ))
        
        code = Prompt.ask(f"[{Theme.PRIMARY}]Enter code to confirm[/]")
        with console.status(f"[{Theme.MUTED}]Confirming...[/]"):
            client.confirm_2fa(code)
        console.print(f"[{Theme.ONLINE}]✓[/] 2FA enabled")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command(name="verify-email")
def verify_email(token: str):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Verifying email...[/]"):
            client.verify_email(token)
        console.print(f"[{Theme.ONLINE}]✓[/] Email verified")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command(name="resend-verification")
def resend_verification(email: str):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Sending verification...[/]"):
            client.resend_verification(email)
        console.print(f"[{Theme.ONLINE}]✓[/] Verification email sent")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command(name="password-reset")
def password_reset():
    console.print()
    email = Prompt.ask(f"[{Theme.PRIMARY}]Email[/]")
    
    try:
        with console.status(f"[{Theme.MUTED}]Requesting reset...[/]"):
            client.request_password_reset(email)
        console.print(f"[{Theme.ONLINE}]✓[/] Reset email sent to {email}")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command(name="password-reset-confirm")
def password_reset_confirm(token: str):
    console.print()
    new_password = Prompt.ask(f"[{Theme.PRIMARY}]New Password[/]", password=True)
    confirm = Prompt.ask(f"[{Theme.PRIMARY}]Confirm Password[/]", password=True)
    
    if new_password != confirm:
        console.print(f"[{Theme.ERROR}]✗[/] Passwords do not match")
        return
    
    try:
        with console.status(f"[{Theme.MUTED}]Resetting password...[/]"):
            client.confirm_password_reset(token, new_password)
        console.print(f"[{Theme.ONLINE}]✓[/] Password reset successfully")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def whoami():
    console.print()
    token = client.load_token()
    if token:
        console.print(f"[{Theme.ONLINE}]●[/] Authenticated")
        console.print(f"[{Theme.MUTED}]Token:[/] {token[:20]}...")
    else:
        console.print(f"[{Theme.OFFLINE}]●[/] Not logged in")
    console.print()
