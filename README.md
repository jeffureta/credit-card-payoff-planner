# Universal Credit Card Statement Parser & Budget Payoff Planner

A privacy-preserving, local-first Python CLI application designed to:
1. **Parse Credit Card PDF Statements** from any issuer (HSBC, Chase, Amex, Citi, Discover, Capital One, or any credit card with standard statement keys).
2. **Track Multi-Card Progress** in a local SQLite database (`cards`, `statements`, `payment_targets`, and variance logs).
3. **Model Month-by-Month Payoffs** with compound interest math, negative amortization protection, and target completion solvers.
4. **Compare Payoff Strategies** (Debt Avalanche vs. Debt Snowball) across multiple accounts to maximize interest savings or cash flow velocity.
5. **Advise via Free Local AI Assistant** running offline on your Mac (via `ollama` with `phi3.5`), grounded in your live portfolio snapshot via Deterministic Context Injection (RAG-lite).

---

## Privacy & Security by Design

- **100% Local Execution**: PDF statements and databases are processed strictly on your machine.
- **Git Protection Gate**: Built-in `.gitignore` and `scripts/git_safety_check.sh` prevent any PDF, statement, or SQLite database file from ever being staged or committed to GitHub.
- **Zero Hallucination Math**: Financial compounding is executed by deterministic Python math algorithms—the AI assistant reads verified numbers rather than inventing calculations.

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/jeffureta/credit-card-payoff-planner.git
   cd credit-card-payoff-planner
   ```

2. **Set up virtual environment & install dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

3. **(Optional) Local AI Setup via Ollama**:
   Ensure [Ollama](https://ollama.ai) is running with `phi3.5`:
   ```bash
   ollama run phi3.5
   ```
   *Note: If Ollama is offline and no Gemini API key is provided, the CLI automatically uses the built-in deterministic financial explanation engine.*

---

## CLI Usage Guide

### 1. Parse a Statement PDF
Auto-detects the issuer, extracts statement balance, minimum payment, payment due date, and purchase APR, and prompts to save into your local database:
```bash
credit-planner parse /path/to/statement.pdf
```

### 2. View All Tracked Cards
Lists registered cards, APRs, latest statement balances, and statement dates:
```bash
credit-planner cards
```

### 3. Generate a Card Payoff Amortization Schedule
Simulate paying a fixed monthly budget or solve for target months:
```bash
# Calculate payoff for a $350/mo budget
credit-planner plan --card-id 1 --budget 350

# Calculate required monthly payment to be debt-free in 12 months
credit-planner plan --card-id 1 --target-months 12
```

### 4. Multi-Card Strategy Simulation (Avalanche vs. Snowball)
Compare Debt Avalanche (highest APR first) against Debt Snowball (lowest balance first):
```bash
credit-planner strategy --budget 600
```

### 5. Check Progress & Target Variance
See whether you are **Ahead (🟢)**, **On Target (🟡)**, or **Behind (🔴)**:
```bash
credit-planner status
```

### 6. Free AI Financial Advisor
Ask questions about your plan with real-time memory of your portfolio:
```bash
# Single-shot question
credit-planner chat "Which card should I pay off first and how much will I save?"

# Interactive chat session
credit-planner chat
```

---

## Running Automated Tests

Run the test suite using `pytest`:
```bash
python3 -m pytest tests/ -v
```

Run pre-commit privacy check:
```bash
bash scripts/git_safety_check.sh
```
