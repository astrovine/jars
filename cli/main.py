import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

@app.command()
def info():
    table = Table(title="JARS System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    
    table.add_row("CLI", "Active")
    table.add_row("Sentinel", "Pending")
    table.add_row("Gatekeeper", "Pending")

    console.print(table)

@app.command()
def hello(name: str):
    console.print(f"[bold blue]Hello[/bold blue] {name}, welcome to JARS CLI.")

if __name__ == "__main__":
    app()
