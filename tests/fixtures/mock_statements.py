"""Synthetic mock statements for test fixtures. Zero PII or real credentials."""

SAMPLE_HSBC_UK_TEXT = """
HSBC UK Bank plc
Credit Card Statement
Statement Date: 15 October 2026
Payment Due Date: 10 November 2026
Account Number: **** **** **** 4321

Summary of your account:
Previous Balance: £4,200.00
Payments Received: £500.00
New Transactions: £800.50
New Statement Balance: £4,500.50
Minimum Payment Due: £120.00

Interest Rates:
Standard Purchase Rate (APR): 24.99% per annum (1.87% monthly)
Cash Advance Rate: 29.99%
"""

SAMPLE_HSBC_US_TEXT = """
HSBC Bank USA, N.A.
Cardmember Service: 1-800-975-4722
hsbcusa.com

Statement Period: Sep 16, 2026 to Oct 15, 2026
Payment Due Date: 11/10/2026
Account Ending In: 8812

Account Summary:
New Balance: $3,250.75
Minimum Payment Due: $95.00

Interest Charge Calculation:
Purchases: Annual Percentage Rate (APR) 22.49%
"""

SAMPLE_CHASE_GENERIC_TEXT = """
JPMorgan Chase Bank, N.A.
www.chase.com | Customer Service: 1-800-432-3117
CHASE SAPPHIRE PREFERRED

Statement Date: 10/18/2026
Payment Due Date: 11/15/2026
Account Number: **** **** **** 9012

ACCOUNT SUMMARY:
Previous Balance: $1,450.00
New Balance: $2,150.00
Minimum Payment Due: $65.00

Interest Charges:
Purchases APR: 27.24% variable
"""

SAMPLE_GENERIC_CARD_TEXT = """
First National Community Credit Card
Statement Closing Date: 2026-10-20
Payment Due Date: 2026-11-16
Card ending in 5544

Balance Summary:
Current Balance Due: $1,800.25
Minimum Payment: $50.00
Annual Percentage Rate: 19.99% APR
"""

SAMPLE_UNRECOGNIZED_NO_BALANCE = """
Welcome to your quarterly newsletter!
Here are our top credit tips for the winter season.
No statement details enclosed.
"""
