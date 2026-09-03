"""Logging module with PRD-compliant Mandatory Evaluation Output Formatter."""
import logging
import sys
from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(force_terminal=True, legacy_windows=False)

# Configure standard logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("AI_Trading_Assistant")


def format_mandatory_evaluation_report(eval_data: Dict[str, Any]) -> str:
    """
    Format output evaluasi wajib sesuai PRD Section 3:
    1. Pencocokan Memori: (Korelasi dengan jurnal/data historis)
    2. Analisis Teknikal: (Struktur tren dan level kunci saat ini)
    3. Analisis Fundamental: (Katalis berita dan dampaknya)
    4. Skor Konfluensi: (% Probabilitas berdasarkan total pembobotan)
    5. POI & Invalidasi: (Level pantau (POI) dan batas toleransi kegagalan setup)
    """
    memory_match = eval_data.get("memory_match", "Tidak ada korelasi signifikan ditemukan.")
    tech_analysis = eval_data.get("technical_analysis", "Tren netral / Konsolidasi.")
    fundamental_analysis = eval_data.get("fundamental_analysis", "Netral, tidak ada rilis berita berdampak tinggi.")
    confluence_score = eval_data.get("confluence_score", 0.0)
    confluence_breakdown = eval_data.get("confluence_breakdown", "")
    poi_invalidation = eval_data.get("poi_invalidation", "POI: N/A, Invalidasi: N/A")
    action_decision = eval_data.get("action", "HOLD")
    pair = eval_data.get("pair", "UNKNOWN")

    report = (
        f"================================================================================\n"
        f"MANDATORY EVALUATION REPORT - {pair.upper()} | DECISION: {action_decision}\n"
        f"================================================================================\n"
        f"1. Pencocokan Memori:\n"
        f"   {memory_match}\n\n"
        f"2. Analisis Teknikal:\n"
        f"   {tech_analysis}\n\n"
        f"3. Analisis Fundamental:\n"
        f"   {fundamental_analysis}\n\n"
        f"4. Skor Konfluensi:\n"
        f"   {confluence_score:.2f}% Probabilitas ({confluence_breakdown})\n\n"
        f"5. POI & Invalidasi:\n"
        f"   {poi_invalidation}\n"
        f"================================================================================"
    )
    return report


def print_rich_evaluation_report(eval_data: Dict[str, Any]) -> None:
    """Render the mandatory evaluation report with a rich aesthetic panel for terminal."""
    pair = eval_data.get("pair", "UNKNOWN").upper()
    action = eval_data.get("action", "HOLD").upper()
    score = eval_data.get("confluence_score", 0.0)

    if action == "BUY":
        action_style = "bold green"
    elif action == "SELL":
        action_style = "bold red"
    else:
        action_style = "bold yellow"

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("No", style="bold cyan", width=4)
    table.add_column("Kategori", style="bold white", width=24)
    table.add_column("Keterangan Detail", style="bright_white")

    table.add_row(
        "1.",
        "Pencocokan Memori:",
        str(eval_data.get("memory_match", "-"))
    )
    table.add_row(
        "2.",
        "Analisis Teknikal:",
        str(eval_data.get("technical_analysis", "-"))
    )
    table.add_row(
        "3.",
        "Analisis Fundamental:",
        str(eval_data.get("fundamental_analysis", "-"))
    )
    table.add_row(
        "4.",
        "Skor Konfluensi:",
        f"[bold magenta]{score:.2f}% Probabilitas[/bold magenta] ({eval_data.get('confluence_breakdown', '')})"
    )
    table.add_row(
        "5.",
        "POI & Invalidasi:",
        f"[bold yellow]{eval_data.get('poi_invalidation', '-')}[/bold yellow]"
    )

    panel = Panel(
        table,
        title=f"[bold]AI TRADING ASSISTANT EVALUATION | [{action_style}]{action}[/{action_style}] on {pair}[/bold]",
        subtitle=f"Skor Total: [bold]{score:.2f}%[/bold] | Batas Minimal: 70.0%",
        border_style="cyan" if action == "HOLD" else ("green" if action == "BUY" else "red")
    )
    console.print(panel)
