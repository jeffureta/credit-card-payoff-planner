"""Mathematical debt amortization and payoff calculation engine."""
import math
from dataclasses import dataclass
from typing import List


@dataclass
class AmortizationRow:
    month: int
    starting_balance: float
    payment: float
    interest_paid: float
    principal_paid: float
    ending_balance: float
    cumulative_interest: float


@dataclass
class PayoffPlanResult:
    months: int
    total_payment: float
    total_interest: float
    total_principal: float
    schedule: List[AmortizationRow]


def calculate_monthly_interest(balance: float, annual_apr: float) -> float:
    monthly_rate = (annual_apr / 100.0) / 12.0
    return balance * monthly_rate


def amortize_card(
    balance: float,
    annual_apr: float,
    monthly_payment: float,
    max_months: int = 360,
) -> PayoffPlanResult:
    """Calculates month-by-month amortization for a credit card balance.
    
    Raises:
        ValueError: If monthly_payment cannot cover the first month's interest.
    """
    if balance <= 0:
        return PayoffPlanResult(months=0, total_payment=0.0, total_interest=0.0, total_principal=0.0, schedule=[])

    monthly_rate = (annual_apr / 100.0) / 12.0
    initial_interest = balance * monthly_rate

    if monthly_payment <= initial_interest:
        raise ValueError(
            f"Monthly payment (${monthly_payment:.2f}) cannot cover monthly interest "
            f"(${initial_interest:.2f}). Balance will grow indefinitely (negative amortization)."
        )

    current_balance = balance
    schedule: List[AmortizationRow] = []
    total_interest = 0.0
    total_principal = 0.0
    total_payment = 0.0

    for month in range(1, max_months + 1):
        interest = current_balance * monthly_rate
        total_interest += interest

        if current_balance + interest <= monthly_payment:
            # Final payoff payment
            actual_payment = current_balance + interest
            principal = current_balance
            ending_balance = 0.0
        else:
            actual_payment = monthly_payment
            principal = actual_payment - interest
            ending_balance = current_balance - principal

        total_principal += principal
        total_payment += actual_payment

        schedule.append(
            AmortizationRow(
                month=month,
                starting_balance=round(current_balance, 2),
                payment=round(actual_payment, 2),
                interest_paid=round(interest, 2),
                principal_paid=round(principal, 2),
                ending_balance=round(ending_balance, 2),
                cumulative_interest=round(total_interest, 2),
            )
        )

        current_balance = ending_balance
        if current_balance <= 0.001:
            break

    return PayoffPlanResult(
        months=len(schedule),
        total_payment=round(total_payment, 2),
        total_interest=round(total_interest, 2),
        total_principal=round(total_principal, 2),
        schedule=schedule,
    )


def solve_payment_for_target_months(balance: float, annual_apr: float, target_months: int) -> float:
    """Calculates the exact monthly payment required to pay off the balance in target_months."""
    if balance <= 0 or target_months <= 0:
        return 0.0

    monthly_rate = (annual_apr / 100.0) / 12.0
    if monthly_rate == 0:
        return round(balance / target_months, 2)

    # Standard annuity formula: P = (r * PV) / (1 - (1 + r)^(-n))
    payment = (monthly_rate * balance) / (1 - (1 + monthly_rate) ** (-target_months))
    # Round UP to nearest cent to ensure loan is fully satisfied by month target_months
    return math.ceil(payment * 100.0) / 100.0
