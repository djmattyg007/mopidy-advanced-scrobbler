from rich.console import Console
from rich.style import Style
from rich.theme import Theme


success_style = Style(color="bright_green", bold=True)
info_style = Style(dim=True)
notice_style = Style(dim=False)
warning_style = Style(color="orange1", bold=True)
error_style = Style(color="bright_red", bold=True)

theme = Theme(
    {
        "success": success_style,
        "info": info_style,
        "notice": notice_style,
        "warning": warning_style,
        "error": error_style,
    }
)

stdout = Console(theme=theme)
stderr = Console(theme=theme, stderr=True)

__all__ = (
    "stdout",
    "stderr",
)
