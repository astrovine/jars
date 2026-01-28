import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from ..client import client
from ..config import Theme

app = typer.Typer(name="wallet", help="Wallet commands")
console = Console()


@app.command()
def balance():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading...[/]"):
            data = client.get_balance()
        
        balance = data.get("available_balance", 0)
        currency = data.get("currency", "NGN")
        
        console.print(Panel(
            f"[{Theme.ONLINE}]{currency} {balance:,.2f}[/]",
            title="Available Balance",
            border_style=Theme.BORDER
        ))
    except Exception as e:
        if "404" in str(e) or "Wallet not found" in str(e):
             console.print(f"[{Theme.WARNING}]No Live Wallet found.[/]")
             console.print(f"[{Theme.MUTED}]Free users only have access to the Virtual Wallet.[/]")
             console.print(f"[{Theme.MUTED}]Try command: [bold white]wvs[/] (or 'wallet virtual-status')[/]")
        else:
            console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def summary():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading...[/]"):
            data = client.get_wallet_summary()
        
        table = Table(show_header=False, border_style=Theme.BORDER, box=None)
        table.add_column("", style=Theme.MUTED)
        table.add_column("", style=Theme.PRIMARY, justify="right")
        
        table.add_row("Available", f"{data.get('available_balance', 0):,.2f}")
        table.add_row("Locked", f"{data.get('locked_balance', 0):,.2f}")
        table.add_row("Total Deposited", f"{data.get('total_deposited', 0):,.2f}")
        table.add_row("Total Withdrawn", f"{data.get('total_withdrawn', 0):,.2f}")
        
        console.print(Panel(table, title="Wallet Summary", border_style=Theme.BORDER))
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def history(limit: int = 20):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading...[/]"):
            txns = client.get_transactions(limit=limit)
        
        table = Table(border_style=Theme.BORDER)
        table.add_column("Date", style=Theme.MUTED)
        table.add_column("Type", style=Theme.PRIMARY)
        table.add_column("Amount", justify="right")
        table.add_column("Status")
        
        for tx in txns:
            amount = tx.get("amount", 0)
            tx_type = tx.get("type", "")
            status = tx.get("status", "")
            
            amount_style = Theme.ONLINE if amount > 0 else Theme.ERROR
            status_style = Theme.ONLINE if status == "completed" else Theme.WARNING
            
            table.add_row(
                str(tx.get("created_at", ""))[:10],
                tx_type,
                f"[{amount_style}]{amount:,.2f}[/]",
                f"[{status_style}]{status}[/]"
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def deposit(amount: float):
    import webbrowser
    import time
    
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Initializing deposit...[/]"):
            result = client.init_deposit(amount)
            
        ref = result.get('reference', 'N/A')
        url = result.get('authorization_url')
        
        console.print(Panel(
            f"[{Theme.PRIMARY} bold]Deposit Initialized[/]\n"
            f"[white]Amount:[/] ₦{amount:,.2f}\n"
            f"[white]Reference:[/] {ref}\n\n"
            f"[dim]Opening payment gateway in your browser...[/]",
            title="Payment Gateway",
            border_style=Theme.ONLINE
        ))
        
        console.print(f"\n[{Theme.MUTED}]Attempting to open browser...[/]")
        try:
            if url:
                webbrowser.open(url)
        except:
            pass
            
        console.print(f"[{Theme.ONLINE}]If browser didn't open, click here to pay:[/]\n[link={url}]{url}[/link]")

        console.print(f"\n[{Theme.MUTED}]Waiting for confirmation... (Press Ctrl+C to cancel)[/]")
        
        start_time = time.time()
        timeout = 300  # 5 minutes
        
        with console.status(f"[{Theme.ONLINE}]Listening for webhook confirmation...[/]", spinner="dots") as status:
            while True:
                if time.time() - start_time > timeout:
                    console.print(f"[{Theme.WARNING}]Polling timed out. Please verify manually with: [white]wvd {ref}[/]")
                    break
                
                try:
                    check = client.verify_deposit(ref)
                    status_msg = check.get("status", "pending")
                    
                    if status_msg == "success":
                        console.print(f"\n[{Theme.ONLINE} bold]✓ Payment Confirmed![/]")
                        console.print(Panel(
                            f"[{Theme.PRIMARY} bold]Transaction Successful[/]\n"
                            f"[white]Amount Credited:[/] ₦{amount:,.2f}\n"
                            f"[white]New Balance:[/] {check.get('amount', '0.00')}\n"
                            f"[dim]Reference: {ref}[/]",
                            title="Receipt",
                            border_style=Theme.ONLINE
                        ))
                        break
                    
                    elif status_msg == "failed" or status_msg == "abandoned":
                        msg = check.get('message', '').lower()
                        if "not completed" in msg or "abandoned" in msg:
                             pass
                        else:
                            console.print(f"\n[{Theme.ERROR} bold]✗ Payment Failed[/]")
                            console.print(f"[{Theme.MUTED}]Reason: {check.get('message', 'Unknown')}[/]")
                            break
                        
                except Exception:
                    pass
                
                time.sleep(3)
                
    except KeyboardInterrupt:
        console.print(f"\n[{Theme.WARNING}]Polling Cancelled. check status later with: [white]wvd {ref}[/]")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command(name="verify-deposit")
def verify_deposit(reference: str):
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Verifying...[/]"):
            result = client.verify_deposit(reference)
        console.print(f"[{Theme.ONLINE}]✓[/] Deposit verified: {result.get('status', '')}")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command()
def banks():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading banks...[/]"):
            banks_list = client.get_banks()
        
        table = Table(border_style=Theme.BORDER)
        table.add_column("Code", style=Theme.MUTED)
        table.add_column("Name", style=Theme.PRIMARY)
        
        for bank in banks_list[:30]:
            table.add_row(bank.get("code", ""), bank.get("name", ""))
        
        console.print(table)
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command(name="virtual-status")
def virtual_status():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Loading...[/]"):
            data = client.get_virtual_wallet_status()
        
        table = Table(show_header=False, border_style=Theme.BORDER, box=None)
        table.add_column("", style=Theme.MUTED)
        table.add_column("", style=Theme.PRIMARY)
        
        table.add_row("Balance", f"{data.get('balance', 0):,.2f}")
        table.add_row("Resets Used", str(data.get("resets_used", 0)))
        table.add_row("Free Resets Left", str(data.get("free_resets_remaining", 0)))
        
        console.print(Panel(table, title="Virtual Wallet", border_style=Theme.BORDER))
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command(name="virtual-reset-free")
def virtual_reset_free():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Requesting reset...[/]"):
            client.request_free_reset()
        console.print(f"[{Theme.ONLINE}]✓[/] Virtual wallet reset")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()


@app.command(name="virtual-reset-paid")
def virtual_reset_paid():
    console.print()
    try:
        with console.status(f"[{Theme.MUTED}]Requesting paid reset...[/]"):
            result = client.request_paid_reset()
        console.print(f"[{Theme.ONLINE}]✓[/] Paid reset initiated")
    except Exception as e:
        console.print(f"[{Theme.ERROR}]✗[/] {e}")
    console.print()
