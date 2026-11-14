"""Deterministic financial snapshot builder for AI Context Injection (RAG-lite)."""
from typing import List
from credit_planner.db import DatabaseManager
from credit_planner.strategies import DebtCardInput, simulate_multi_card_payoff


def build_financial_context_snapshot(db: DatabaseManager) -> str:
    """Queries SQLite and synthesizes a concise, factual Markdown financial snapshot."""
    cards = db.get_cards()
    if not cards:
        return "No credit cards currently registered in the database."

    lines: List[str] = ["### User Financial Snapshot & Active Credit Cards:"]
    total_balance = 0.0
    total_min_payment = 0.0
    debt_inputs: List[DebtCardInput] = []

    for c in cards:
        statements = db.get_statements_for_card(c.id)
        if statements:
            latest = statements[0]
            bal = latest.statement_balance
            min_pay = latest.minimum_payment
            apr = latest.purchase_apr or c.current_apr
        else:
            bal = 0.0
            min_pay = 0.0
            apr = c.current_apr

        total_balance += bal
        total_min_payment += min_pay
        if bal > 0:
            debt_inputs.append(
                DebtCardInput(
                    id=c.id,
                    name=c.card_name or f"{c.issuer} (*{c.last4})",
                    balance=bal,
                    apr=apr,
                    min_payment=min_pay,
                )
            )

        report = db.get_progress_report(c.id)
        status_str = f"Status: {report.status.value}" if report else "Status: Untracked"

        lines.append(
            f"- **{c.card_name or c.issuer}** (ending in *{c.last4}): "
            f"Balance: ${bal:,.2f} | APR: {apr:.2f}% | Min Payment: ${min_pay:,.2f} | {status_str}"
        )

    lines.append(f"\n**Total Outstanding Debt**: ${total_balance:,.2f}")
    lines.append(f"**Total Minimum Payments Required**: ${total_min_payment:,.2f}")

    target = db.get_target(card_id=None)
    budget = target.monthly_budget if target and target.monthly_budget > 0 else total_min_payment + 100.0
    strategy_pref = target.strategy if target else "AVALANCHE"

    lines.append(f"**Monthly Payment Budget**: ${budget:,.2f}")
    lines.append(f"**Preferred Strategy**: {strategy_pref.capitalize()}")

    # Pre-calculated mathematical amortization numbers
    if len(debt_inputs) >= 1 and budget >= total_min_payment:
        try:
            comparison = simulate_multi_card_payoff(debt_inputs, budget)
            lines.append("\n**Calculated Payoff Metrics**:")
            lines.append(
                f"- Avalanche Payoff: {comparison.avalanche_result.months} months, "
                f"Total Interest: ${comparison.avalanche_result.total_interest:,.2f}"
            )
            lines.append(
                f"- Snowball Payoff: {comparison.snowball_result.months} months, "
                f"Total Interest: ${comparison.snowball_result.total_interest:,.2f}"
            )
            if comparison.interest_saved_by_avalanche > 0:
                lines.append(
                    f"- Avalanche Interest Savings over Snowball: ${comparison.interest_saved_by_avalanche:,.2f}"
                )
        except Exception:
            pass

    return "\n".join(lines)
