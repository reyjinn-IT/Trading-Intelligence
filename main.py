import argparse
import sys
import uvicorn
from rich.console import Console
from rich.panel import Panel

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.core.config import settings
from src.core.deadman_switch import deadman_switch
from src.engine.evaluator import evaluator

console = Console(force_terminal=True, legacy_windows=False)

def run_server(host: str = settings.APP_HOST, port: int = settings.APP_PORT):
    console.print(
        Panel(
            f"[bold cyan]AI EXPERT TRADING ASSISTANT[/bold cyan]\n"
            f"Mode: [bold {'red' if settings.LIVE_TRADING else 'green'}]{'LIVE TRADING (CAUTION)' if settings.LIVE_TRADING else 'PAPER TRADING (SAFE)'}[/]\n"
            f"Web Dashboard URL: [bold yellow]http://{host}:{port}[/bold yellow]\n"
            f"Deadman Switch: [bold green]ARMED ({settings.DEADMAN_TIMEOUT_SEC}s)[/bold green]",
            title="SYSTEM STARTUP",
            border_style="cyan"
        )
    )
    uvicorn.run("src.web.app:app", host=host, port=port, reload=settings.DEBUG)

def run_evaluation(pair: str = "btc_idr", timeframe: str = "1h", execute: bool = False):
    eval_result = evaluator.evaluate_pair(pair=pair, timeframe=timeframe, print_report=True)
    if execute:
        exec_res = evaluator.execute_evaluated_trade(eval_result)
        console.print(f"[bold yellow]Execution Result:[/bold yellow] {exec_res}")
    return eval_result

def run_interactive_cli():
    while True:
        console.print("\n[bold cyan]=== AI TRADING ASSISTANT CLI MENU ===[/bold cyan]")
        console.print("1. Evaluasi BTC/IDR (Indodax)")
        console.print("2. Evaluasi ETH/IDR (Indodax)")
        console.print("3. Evaluasi XAU/USD (Gold Spot)")
        console.print("4. Status Deadman Switch & Akun")
        console.print("5. Mulai Web Dashboard (Server)")
        console.print("0. Keluar")

        try:
            choice = input("\nPilih menu [0-5]: ").strip()
            if choice == "1":
                run_evaluation(pair="btc_idr")
            elif choice == "2":
                run_evaluation(pair="eth_idr")
            elif choice == "3":
                run_evaluation(pair="xau_usd")
            elif choice == "4":
                dm = deadman_switch.get_status()
                console.print(f"[bold]Deadman Status:[/bold] {dm}")
            elif choice == "5":
                run_server()
                break
            elif choice == "0":
                console.print("[yellow]Menutup bot trading. Sampai jumpa![/yellow]")
                break
            else:
                console.print("[red]Pilihan tidak valid.[/red]")
        except (KeyboardInterrupt, EOFError):
            break

def main():
    parser = argparse.ArgumentParser(description="AI Expert Trading Assistant")
    parser.add_argument("--server", action="store_true", help="Start Web Dashboard server")
    parser.add_argument("--eval", action="store_true", help="Evaluate market pair")
    parser.add_argument("--pair", type=str, default="btc_idr", help="Market pair (e.g. btc_idr, xau_usd)")
    parser.add_argument("--timeframe", type=str, default="1h", help="Timeframe (e.g. 15m, 1h, 4h, 1d)")
    parser.add_argument("--trade", action="store_true", help="Execute order if confluence condition is met")
    parser.add_argument("--cli", action="store_true", help="Start interactive CLI loop")
    parser.add_argument("--port", type=int, default=settings.APP_PORT, help="Server port")
    parser.add_argument("--host", type=str, default=settings.APP_HOST, help="Server host")

    args = parser.parse_args()

    if args.server:
        run_server(host=args.host, port=args.port)
    elif args.eval:
        run_evaluation(pair=args.pair, timeframe=args.timeframe, execute=args.trade)
    elif args.cli:
        run_interactive_cli()
    else:
        # If no arguments provided, default to starting the web dashboard
        run_server(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
