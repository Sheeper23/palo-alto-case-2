"""
Synthetic Data Generator for Smart Financial Parser
Generates intentionally messy transaction data to test normalization logic.
"""

import csv
import random
from datetime import datetime, timedelta
from typing import List, Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


# Messy date format generators
def generate_messy_date() -> str:
    """Generate a random date in various inconsistent formats."""
    # Random date in 2023
    base = datetime(2023, 1, 1)
    days_offset = random.randint(0, 364)
    date = base + timedelta(days=days_offset)
    
    # Various date formats (intentionally inconsistent)
    formats = [
        date.strftime("%Y-%m-%d"),              # ISO: 2023-01-15
        date.strftime("%m/%d/%Y"),              # US: 01/15/2023
        date.strftime("%d/%m/%Y"),              # European: 15/01/2023
        date.strftime("%b %d, %Y"),             # Jan 15, 2023
        date.strftime("%B %d, %Y"),             # January 15, 2023
        date.strftime("%d-%m-%Y"),              # 15-01-2023
        date.strftime("%m-%d-%Y"),              # 01-15-2023
        f"{date.strftime('%b')} {date.day}{'st' if date.day == 1 else 'nd' if date.day == 2 else 'rd' if date.day == 3 else 'th'}, {str(date.year)[2:]}",  # Jan 15th, 23
    ]
    
    return random.choice(formats)


def generate_edge_case_date() -> str:
    """Generate edge case dates for testing."""
    edge_cases = [
        "2023-02-29",           # Invalid leap year date (2023 is not leap year)
        "2024-02-29",           # Valid leap year date
        "12/31/2023",           # Year boundary
        "01/01/2023",           # Year start
        "2023-13-01",           # Invalid month
        "2023-01-32",           # Invalid day
        "",                      # Empty string
        "Invalid Date",          # Completely invalid
        "2025-06-15",           # Future date
    ]
    return random.choice(edge_cases)


# Messy merchant name generators
MERCHANT_VARIANTS = {
    "uber": [
        "UBER *TRIP",
        "Uber Technologies",
        "UBER EATS",
        "uber",
        "Uber Eats",
        "UBER *EATS",
        "Uber Trip",
    ],
    "amazon": [
        "AMAZON.COM",
        "Amazon Prime",
        "AMZN Mktp US",
        "Amazon",
        "AMZ*Amazon.com",
        "AMAZON MKTPLACE",
        "amazon.com",
    ],
    "starbucks": [
        "STARBUCKS #1234",
        "Starbucks",
        "SBUX",
        "Starbucks Coffee",
        "STARBUCKS STORE 5678",
        "Starbucks Corp",
    ],
    "target": [
        "TARGET 00012345",
        "Target",
        "TARGET.COM",
        "TGT*",
        "Target Store",
    ],
    "mcdonalds": [
        "McDonald's #12345",
        "MCDONALD'S",
        "McDonalds",
        "MCD",
        "McDonald's Restaurant",
    ],
    "gas_station": [
        "SHELL OIL 12345",
        "Shell",
        "CHEVRON 67890",
        "BP Gas Station",
        "EXXONMOBIL",
    ],
    "grocery": [
        "WHOLE FOODS MKT",
        "Whole Foods",
        "TRADER JOE'S #123",
        "Trader Joes",
        "SAFEWAY #456",
    ],
    "restaurant": [
        "CHIPOTLE 1234",
        "Chipotle Mexican Grill",
        "PANERA BREAD #567",
        "In-N-Out Burger",
    ],
    "utility": [
        "PG&E Electric",
        "PACIFIC GAS & ELECTRIC",
        "COMCAST CABLE",
        "Comcast",
        "AT&T Wireless",
    ],
    "entertainment": [
        "NETFLIX.COM",
        "Netflix",
        "SPOTIFY USA",
        "Spotify Premium",
        "AMC THEATRES",
    ],
}


def generate_messy_merchant() -> tuple:
    """Generate merchant name with its category."""
    category = random.choice(list(MERCHANT_VARIANTS.keys()))
    merchant = random.choice(MERCHANT_VARIANTS[category])
    return merchant, category


def generate_edge_case_merchant() -> tuple:
    """Generate edge case merchants for testing."""
    edge_cases = [
        ("Café Résumé", "restaurant"),          # Unicode characters
        ("José's Taquería", "restaurant"),      # Accented characters
        ("", "unknown"),                         # Empty string
        ("A" * 100, "unknown"),                  # Very long name
        ("123456789", "unknown"),                # Just numbers
        ("!!!###", "unknown"),                   # Special characters only
    ]
    return random.choice(edge_cases)


# Messy amount generators
def generate_messy_amount() -> str:
    """Generate amounts with inconsistent formatting."""
    amount = round(random.uniform(5.00, 500.00), 2)
    
    # Various amount formats
    formats = [
        f"${amount:.2f}",           # $45.50
        f"$ {amount:.2f}",          # $ 45.50
        f"{amount:.2f}",            # 45.50
        f"USD {amount:.2f}",        # USD 45.50
        f"{amount:.2f} USD",        # 45.50 USD
        f"${amount:,.2f}",          # $1,234.56 (with comma)
        f"  ${amount:.2f}  ",       # With extra spaces
    ]
    
    return random.choice(formats)


def generate_edge_case_amount() -> str:
    """Generate edge case amounts for testing."""
    edge_cases = [
        "-$25.00",          # Negative (refund)
        "$0.00",            # Zero
        "$0.01",            # Very small
        "$999999.99",       # Very large
        "",                 # Empty string
        "Invalid",          # Non-numeric
        "€50.00",           # Different currency symbol
        "¥1000",            # Yen symbol
        "$12.345",          # Too many decimal places
        "12.3",             # Inconsistent decimals
    ]
    return random.choice(edge_cases)


def generate_transactions(num_transactions: int = 100, edge_case_ratio: float = 0.1) -> List[Dict]:
    """
    Generate a list of messy transactions.
    
    Args:
        num_transactions: Total number of transactions to generate
        edge_case_ratio: Proportion of transactions that should be edge cases (0-1)
    
    Returns:
        List of transaction dictionaries
    """
    transactions = []
    num_edge_cases = int(num_transactions * edge_case_ratio)
    num_normal = num_transactions - num_edge_cases
    
    # Generate normal messy transactions
    for _ in range(num_normal):
        merchant, category = generate_messy_merchant()
        transactions.append({
            "date": generate_messy_date(),
            "merchant": merchant,
            "amount": generate_messy_amount(),
            "category": category,
        })
    
    # Generate edge case transactions
    for _ in range(num_edge_cases):
        # Randomly decide which fields should have edge cases
        use_edge_date = random.random() < 0.5
        use_edge_merchant = random.random() < 0.5
        use_edge_amount = random.random() < 0.5
        
        # Get normal or edge case values
        date = generate_edge_case_date() if use_edge_date else generate_messy_date()
        merchant, category = generate_edge_case_merchant() if use_edge_merchant else generate_messy_merchant()
        amount = generate_edge_case_amount() if use_edge_amount else generate_messy_amount()
        
        transactions.append({
            "date": date,
            "merchant": merchant,
            "amount": amount,
            "category": category,
        })
    
    # Shuffle to mix edge cases throughout
    random.shuffle(transactions)
    return transactions


def write_transactions_csv(transactions: List[Dict], filename: str, include_category: bool = False):
    """
    Write transactions to CSV file.
    
    Args:
        transactions: List of transaction dictionaries
        filename: Output CSV filename
        include_category: If True, include ground truth category (for testing)
    """
    fieldnames = ["date", "merchant", "amount"]
    if include_category:
        fieldnames.append("category")
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for transaction in transactions:
            row = {
                "date": transaction["date"],
                "merchant": transaction["merchant"],
                "amount": transaction["amount"],
            }
            if include_category:
                row["category"] = transaction["category"]
            
            writer.writerow(row)


def main():
    """Generate sample datasets."""
    import os
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set seed for reproducibility
    random.seed(42)
    
    # Print banner
    banner = """
[bold cyan]Synthetic Transaction Data Generator[/bold cyan]
Generates intentionally messy financial data for testing
    """
    console.print(Panel(banner, border_style="cyan"))
    
    console.print(f"\n[dim]Output directory: {script_dir}[/dim]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        # Generate main messy transactions file
        task1 = progress.add_task("[cyan]Generating messy_transactions.csv...", total=None)
        transactions = generate_transactions(num_transactions=100, edge_case_ratio=0.1)
        output_path = os.path.join(script_dir, "messy_transactions.csv")
        write_transactions_csv(transactions, output_path, include_category=False)
        progress.update(task1, completed=True)
        console.print(f"[green]Generated {output_path}[/green] (100 transactions, 10% edge cases)")
        
        # Generate edge cases file
        task2 = progress.add_task("[cyan]Generating edge_cases.csv...", total=None)
        edge_transactions = generate_transactions(num_transactions=30, edge_case_ratio=0.5)
        output_path = os.path.join(script_dir, "edge_cases.csv")
        write_transactions_csv(edge_transactions, output_path, include_category=False)
        progress.update(task2, completed=True)
        console.print(f"[green]Generated {output_path}[/green] (30 transactions, 50% edge cases)\n")
    
    # Show sample transactions in a nice table
    console.print("[bold]Sample transactions from messy_transactions.csv:[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Date", width=20)
    table.add_column("Merchant", width=25)
    table.add_column("Amount", justify="right", width=15)
    
    for i, t in enumerate(transactions[:5], 1):
        table.add_row(
            str(i),
            t['date'],
            t['merchant'],
            t['amount']
        )
    
    console.print(table)


if __name__ == "__main__":
    main()