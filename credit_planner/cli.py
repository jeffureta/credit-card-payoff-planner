"""Interactive CLI for Universal Credit Card Statement Parser & Payoff Planner."""
import argparse
import sys
import os
from pypdf import PdfReader
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from credit_planner.db import DatabaseManager
from credit_planner.parsers.detector import IssuerDetector
from credit_planner.parsers.registry import ParserRegistry
from credit_planner.models import CardProfile, StatementData, PaymentTarget, VarianceStatus, get_currency_symbol
from credit_planner.calculator import amortize_card, solve_payment_for_target_months
from credit_planner.strategies import DebtCardInput, simulate_multi_card_payoff
from credit_planner.ai.assistant import AIAssistant

console = Console()


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a local PDF statement."""
    if not os.path.exists(pdf_path):
        console.print(f"[bold red]Error: File not found at {pdf_path}[/bold red]")
        sys.exit(1)

    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


def cmd_parse(args, db: DatabaseManager):
    """Parses a statement PDF, displays extracted metrics, and saves to database."""
    console.print(f"[bold cyan]🔍 Reading statement:[/bold cyan] {args.file}")
    text = extract_text_from_pdf(args.file)

    detector = IssuerDetector()
    detected_issuer, confidence = detector.detect(text)

    console.print(f"[bold green]✓ Issuer Detected:[/bold green] {detected_issuer} (Confidence: {confidence*100:.0f}%)")

    registry = ParserRegistry()
    parser = registry.resolve_for_text(text)
    statement_data = parser.parse_text(text)

    sym = get_currency_symbol(statement_data.currency)

    # Render summary table
    table = Table(title="Statement Summary", header_style="bold magenta")
    table.add_column("Field", style="dim")
    table.add_column("Extracted Value", style="bold green")

    table.add_row("Issuer", statement_data.issuer or detected_issuer)
    table.add_row("Card Last 4", f"*{statement_data.account_last4}")
    table.add_row("Statement Date", str(statement_data.statement_date))
    table.add_row("Payment Due Date", str(statement_data.due_date))
    table.add_row("Statement Balance", f"{sym}{statement_data.statement_balance:,.2f}")
    table.add_row("Minimum Payment Due", f"{sym}{statement_data.minimum_payment:,.2f}")
    table.add_row("Purchase Rate (APR)", f"{statement_data.purchase_apr:.2f}%")

    console.print(table)

    if not args.no_save:
        card = CardProfile(
            issuer=statement_data.issuer or detected_issuer,
            card_name=f"{statement_data.issuer or detected_issuer} *{statement_data.account_last4}",
            last4=statement_data.account_last4,
            current_apr=statement_data.purchase_apr,
        )
        card_id = db.add_card(card)
        statement_data.card_id = card_id
        db.save_statement(statement_data)
        console.print(f"[bold green]✓ Saved to local database (Card ID: {card_id}).[/bold green]")


def cmd_cards(args, db: DatabaseManager):
    """Lists all registered credit cards and latest balances."""
    cards = db.get_cards()
    if not cards:
        console.print("[yellow]No credit cards found in local database. Run 'parse' on a statement first.[/yellow]")
        return

    table = Table(title="Registered Credit Cards", header_style="bold blue")
    table.add_column("ID", justify="center")
    table.add_column("Issuer")
    table.add_column("Card Name")
    table.add_column("Last 4")
    table.add_column("APR", justify="right")
    table.add_column("Latest Balance", justify="right")
    table.add_column("Min Payment", justify="right")
    table.add_column("Statement Date")

    for c in cards:
        stmts = db.get_statements_for_card(c.id)
        if stmts:
            latest = stmts[0]
            sym = get_currency_symbol(latest.currency)
            bal_str = f"{sym}{latest.statement_balance:,.2f}"
            min_str = f"{sym}{latest.minimum_payment:,.2f}"
            date_str = str(latest.statement_date)
            apr = latest.purchase_apr or c.current_apr
        else:
            bal_str = "$0.00"
            min_str = "$0.00"
            date_str = "None"
            apr = c.current_apr

        table.add_row(str(c.id), c.issuer, c.card_name, c.last4, f"{apr:.2f}%", bal_str, min_str, date_str)

    console.print(table)


def cmd_plan(args, db: DatabaseManager):
    """Calculates month-by-month debt amortization schedules for a card."""
    card = db.get_card(args.card_id)
    if not card:
        console.print(f"[bold red]Card ID {args.card_id} not found in database.[/bold red]")
        return

    stmts = db.get_statements_for_card(card.id)
    if not stmts:
        console.print(f"[bold red]No statement records found for card {card.id}.[/bold red]")
        return

    latest = stmts[0]
    balance = args.balance if args.balance else latest.statement_balance
    apr = args.apr if args.apr else (latest.purchase_apr or card.current_apr)

    if args.target_months:
        needed_payment = solve_payment_for_target_months(balance, apr, args.target_months)
        console.print(
            f"[bold green]To pay off ${balance:,.2f} in {args.target_months} months, "
            f"your monthly payment should be: ${needed_payment:,.2f}[/bold green]"
        )
        monthly_payment = needed_payment
    elif args.budget:
        monthly_payment = args.budget
    else:
        monthly_payment = latest.minimum_payment

    try:
        result = amortize_card(balance, apr, monthly_payment)
    except ValueError as e:
        console.print(f"[bold red]Plan Error: {e}[/bold red]")
        return

    table = Table(
        title=f"Payoff Schedule: {card.card_name} (Payment: ${monthly_payment:,.2f}/mo)",
        header_style="bold cyan",
    )
    table.add_column("Month", justify="center")
    table.add_column("Starting", justify="right")
    table.add_column("Payment", justify="right")
    table.add_column("Interest", justify="right")
    table.add_column("Principal", justify="right")
    table.add_column("Ending Balance", justify="right")
    table.add_column("Total Interest", justify="right")

    for row in result.schedule[:args.limit]:
        table.add_row(
            str(row.month),
            f"${row.starting_balance:,.2f}",
            f"${row.payment:,.2f}",
            f"${row.interest_paid:,.2f}",
            f"${row.principal_paid:,.2f}",
            f"${row.ending_balance:,.2f}",
            f"${row.cumulative_interest:,.2f}",
        )

    if len(result.schedule) > args.limit:
        table.add_row("...", "...", "...", "...", "...", "...", "...")
        final_row = result.schedule[-1]
        table.add_row(
            str(final_row.month),
            f"${final_row.starting_balance:,.2f}",
            f"${final_row.payment:,.2f}",
            f"${final_row.interest_paid:,.2f}",
            f"${final_row.principal_paid:,.2f}",
            f"${final_row.ending_balance:,.2f}",
            f"${final_row.cumulative_interest:,.2f}",
        )

    console.print(table)
    console.print(
        f"[bold green]Debt-free in {result.months} months. "
        f"Total Interest Paid: ${result.total_interest:,.2f}[/bold green]"
    )


def cmd_strategy(args, db: DatabaseManager):
    """Compares Avalanche vs. Snowball allocations across all cards."""
    cards = db.get_cards()
    debt_inputs = []
    total_min = 0.0

    for c in cards:
        stmts = db.get_statements_for_card(c.id)
        if stmts and stmts[0].statement_balance > 0.01:
            latest = stmts[0]
            debt_inputs.append(
                DebtCardInput(
                    id=c.id,
                    name=c.card_name,
                    balance=latest.statement_balance,
                    apr=latest.purchase_apr or c.current_apr,
                    min_payment=latest.minimum_payment,
                )
            )
            total_min += latest.minimum_payment

    if not debt_inputs:
        console.print("[yellow]No outstanding card balances found to simulate.[/yellow]")
        return

    budget = args.budget if args.budget else total_min + 150.0
    if budget < total_min:
        console.print(f"[bold red]Budget (${budget:,.2f}) must be at least total minimum payments (${total_min:,.2f})[/bold red]")
        return

    comparison = simulate_multi_card_payoff(debt_inputs, budget)

    table = Table(title=f"Multi-Card Payoff Strategy Comparison (Budget: ${budget:,.2f}/mo)", header_style="bold yellow")
    table.add_column("Strategy")
    table.add_column("Payoff Time", justify="center")
    table.add_column("Total Interest Paid", justify="right")
    table.add_column("Total Amount Paid", justify="right")

    table.add_row(
        "Debt Avalanche (Highest APR First)",
        f"{comparison.avalanche_result.months} months",
        f"${comparison.avalanche_result.total_interest:,.2f}",
        f"${comparison.avalanche_result.total_paid:,.2f}",
    )
    table.add_row(
        "Debt Snowball (Lowest Balance First)",
        f"{comparison.snowball_result.months} months",
        f"${comparison.snowball_result.total_interest:,.2f}",
        f"${comparison.snowball_result.total_paid:,.2f}",
    )

    console.print(table)
    if comparison.interest_saved_by_avalanche > 0:
        console.print(
            f"[bold green]💡 Avalanche saves ${comparison.interest_saved_by_avalanche:,.2f} in interest "
            f"compared to Snowball![/bold green]"
        )


def cmd_status(args, db: DatabaseManager):
    """Displays tracking status for all cards (Ahead / On Target / Behind)."""
    cards = db.get_cards()
    if not cards:
        console.print("[yellow]No credit cards registered.[/yellow]")
        return

    table = Table(title="Debt Payoff Progress Tracker", header_style="bold magenta")
    table.add_column("Card Name")
    table.add_column("Actual Balance", justify="right")
    table.add_column("Expected Balance", justify="right")
    table.add_column("Variance", justify="right")
    table.add_column("Status", justify="center")

    for c in cards:
        report = db.get_progress_report(c.id)
        if not report:
            continue
        if report.status == VarianceStatus.AHEAD:
            status_style = "[bold green]🟢 AHEAD[/bold green]"
            var_str = f"+${report.variance:,.2f}"
        elif report.status == VarianceStatus.BEHIND:
            status_style = "[bold red]🔴 BEHIND[/bold red]"
            var_str = f"-${abs(report.variance):,.2f}"
        else:
            status_style = "[bold yellow]🟡 ON TARGET[/bold yellow]"
            var_str = "$0.00"

        table.add_row(
            report.card_name,
            f"${report.actual_balance:,.2f}",
            f"${report.expected_balance:,.2f}",
            var_str,
            status_style,
        )

    console.print(table)


def cmd_chat(args, db: DatabaseManager):
    """Interactive or single-shot AI debt strategist."""
    assistant = AIAssistant(db=db)
    if args.question:
        console.print(f"[bold cyan]User:[/bold cyan] {args.question}")
        answer = assistant.ask(args.question)
        console.print(Panel(answer, title="[bold green]AI Financial Advisor[/bold green]", border_style="green"))
    else:
        console.print("[bold green]💬 Free AI Financial Advisor (Type 'exit' to quit):[/bold green]")
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input or user_input.lower() in ("exit", "quit"):
                    break
                answer = assistant.ask(user_input)
                console.print(Panel(answer, title="[bold green]AI Advisor[/bold green]", border_style="green"))
            except (KeyboardInterrupt, EOFError):
                break


def main():
    parser = argparse.ArgumentParser(description="Universal Credit Card Statement Parser & Payoff Planner")
    parser.add_argument("--db", default="data/credit_planner.db", help="Path to SQLite database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # parse
    p_parse = subparsers.add_parser("parse", help="Parse statement PDF")
    p_parse.add_argument("file", help="Path to PDF statement")
    p_parse.add_argument("--no-save", action="store_true", help="Do not save to database")

    # cards
    subparsers.add_parser("cards", help="List credit cards")

    # plan
    p_plan = subparsers.add_parser("plan", help="Amortization plan for a card")
    p_plan.add_argument("--card-id", type=int, required=True, help="Card ID")
    p_plan.add_argument("--budget", type=float, help="Monthly payment amount")
    p_plan.add_argument("--target-months", type=int, help="Target payoff duration in months")
    p_plan.add_argument("--balance", type=float, help="Override starting balance")
    p_plan.add_argument("--apr", type=float, help="Override APR")
    p_plan.add_argument("--limit", type=int, default=12, help="Max rows to display")

    # strategy
    p_strat = subparsers.add_parser("strategy", help="Avalanche vs. Snowball comparison")
    p_strat.add_argument("--budget", type=float, help="Total monthly budget across all cards")

    # status
    subparsers.add_parser("status", help="Track payoff variance and status")

    # chat / ask
    p_chat = subparsers.add_parser("chat", help="AI debt strategist assistant")
    p_chat.add_argument("question", nargs="?", help="Optional single-shot question")

    args = parser.parse_args()
    db = DatabaseManager(args.db)
    db.init_db()

    if args.command == "parse":
        cmd_parse(args, db)
    elif args.command == "cards":
        cmd_cards(args, db)
    elif args.command == "plan":
        cmd_plan(args, db)
    elif args.command == "strategy":
        cmd_strategy(args, db)
    elif args.command == "status":
        cmd_status(args, db)
    elif args.command == "chat":
        cmd_chat(args, db)


if __name__ == "__main__":
    main()
