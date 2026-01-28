from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
import pyfiglet

from ..config import Theme, LOGO_FONT

console = Console()

LOGO_ART = pyfiglet.figlet_format("JARS", font=LOGO_FONT)


def render_splash():
    logo = Text(LOGO_ART)
    logo.stylize(Theme.PRIMARY)
    
    tagline = Text("Copy Trading Infrastructure", style=Theme.MUTED)
    
    content = Text()
    content.append_text(logo)
    content.append("\n")
    content.append_text(tagline)
    
    panel = Panel(
        Align.center(content),
        border_style=Theme.BORDER,
        padding=(1, 4),
    )
    
    console.print()
    console.print(panel)
    console.print()
