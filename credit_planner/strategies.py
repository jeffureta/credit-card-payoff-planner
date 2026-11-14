"""Multi-card debt payoff strategy simulations (Debt Avalanche vs. Debt Snowball)."""
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class DebtCardInput:
    id: int
    name: str
    balance: float
    apr: float
    min_payment: float


@dataclass
class StrategyExecutionResult:
    strategy_name: str
    months: int
    total_paid: float
    total_interest: float
    total_remaining_debt: float


@dataclass
class MultiCardStrategyComparison:
    avalanche_result: StrategyExecutionResult
    snowball_result: StrategyExecutionResult
    interest_saved_by_avalanche: float
    months_difference: int


def _simulate_strategy(
    cards: List[DebtCardInput],
    total_monthly_budget: float,
    strategy: str = "AVALANCHE",
    max_months: int = 360,
) -> StrategyExecutionResult:
    # Deep copy active balances
    balances = {c.id: c.balance for c in cards}
    aprs = {c.id: c.apr for c in cards}
    min_payments = {c.id: c.min_payment for c in cards}
    
    total_interest_paid = 0.0
    total_paid = 0.0

    for month in range(1, max_months + 1):
        # 1. Check if all cards are paid off
        active_card_ids = [c_id for c_id, bal in balances.items() if bal > 0.01]
        if not active_card_ids:
            return StrategyExecutionResult(
                strategy_name=strategy,
                months=month - 1,
                total_paid=round(total_paid, 2),
                total_interest=round(total_interest_paid, 2),
                total_remaining_debt=0.0,
            )

        # 2. Accrue monthly interest on each active balance
        month_interest = {}
        for c_id in active_card_ids:
            r = (aprs[c_id] / 100.0) / 12.0
            interest = balances[c_id] * r
            balances[c_id] += interest
            total_interest_paid += interest
            month_interest[c_id] = interest

        # 3. Allocate minimum payments first
        allocated_payments: Dict[int, float] = {}
        remaining_budget = total_monthly_budget

        for c_id in active_card_ids:
            # Pay min payment or full balance if less
            pay_amt = min(balances[c_id], min_payments[c_id])
            allocated_payments[c_id] = pay_amt
            remaining_budget -= pay_amt
            balances[c_id] -= pay_amt
            total_paid += pay_amt

        # 4. Determine priority target card for excess budget
        # Filter cards that still have a balance
        unpaid_card_ids = [c_id for c_id in active_card_ids if balances[c_id] > 0.01]

        if unpaid_card_ids and remaining_budget > 0:
            if strategy == "AVALANCHE":
                # Highest APR first
                unpaid_card_ids.sort(key=lambda c_id: aprs[c_id], reverse=True)
            else:  # SNOWBALL
                # Lowest remaining balance first
                unpaid_card_ids.sort(key=lambda c_id: balances[c_id])

            for target_id in unpaid_card_ids:
                extra_pay = min(balances[target_id], remaining_budget)
                balances[target_id] -= extra_pay
                remaining_budget -= extra_pay
                total_paid += extra_pay
                if remaining_budget <= 0.001:
                    break

    # If reached max_months
    remaining_debt = sum(b for b in balances.values() if b > 0)
    return StrategyExecutionResult(
        strategy_name=strategy,
        months=max_months,
        total_paid=round(total_paid, 2),
        total_interest=round(total_interest_paid, 2),
        total_remaining_debt=round(remaining_debt, 2),
    )


def simulate_multi_card_payoff(
    cards: List[DebtCardInput],
    total_monthly_budget: float,
) -> MultiCardStrategyComparison:
    total_min_required = sum(c.min_payment for c in cards)
    if total_monthly_budget < total_min_required:
        raise ValueError(
            f"Total monthly budget (${total_monthly_budget:.2f}) is less than minimum required payments "
            f"(${total_min_required:.2f}) across all cards. You risk default/late penalties."
        )

    avalanche = _simulate_strategy(cards, total_monthly_budget, strategy="AVALANCHE")
    snowball = _simulate_strategy(cards, total_monthly_budget, strategy="SNOWBALL")

    saved_interest = max(0.0, snowball.total_interest - avalanche.total_interest)
    months_diff = snowball.months - avalanche.months

    return MultiCardStrategyComparison(
        avalanche_result=avalanche,
        snowball_result=snowball,
        interest_saved_by_avalanche=round(saved_interest, 2),
        months_difference=months_diff,
    )
