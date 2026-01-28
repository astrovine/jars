from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live

from ..config import Theme

console = Console()


class StatusPanel:
    def __init__(self):
        self.services = {}
    
    def set_status(self, name: str, status: str, details: str = ""):
        self.services[name] = {"status": status, "details": details}
    
    def render(self) -> Table:
        table = Table(
            title="System Status",
            title_style=Theme.HEADER,
            border_style=Theme.BORDER,
            show_header=True,
            header_style=Theme.PRIMARY,
        )
        
        table.add_column("Service", style=Theme.PRIMARY)
        table.add_column("Status")
        table.add_column("Details", style=Theme.MUTED)
        
        for name, info in self.services.items():
            status = info["status"]
            if status == "online":
                style = Theme.ONLINE
            elif status == "offline":
                style = Theme.OFFLINE
            else:
                style = Theme.PENDING
            
            table.add_row(name, f"[{style}]●[/] {status}", info["details"])
        
        return table


class EventLogPanel:
    def __init__(self, max_events: int = 10):
        self.events = []
        self.max_events = max_events
    
    def add_event(self, event: str, style: str = Theme.MUTED):
        self.events.append({"text": event, "style": style})
        if len(self.events) > self.max_events:
            self.events.pop(0)
    
    def render(self) -> Panel:
        lines = []
        for event in self.events:
            lines.append(f"[{event['style']}]{event['text']}[/]")
        
        content = "\n".join(lines) if lines else "[dim]No events[/]"
        
        return Panel(
            content,
            title="Event Log",
            title_align="left",
            border_style=Theme.BORDER,
            padding=(0, 1),
        )
