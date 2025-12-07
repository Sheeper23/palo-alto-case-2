"""
Analyzer for financial transaction data.
Generates spending reports and insights from normalized transactions.
"""

import logging
from collections import defaultdict
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Handle imports for both module and standalone execution
try:
    from .utils import CATEGORY_DISPLAY_NAMES, format_currency
except ImportError:
    from utils import CATEGORY_DISPLAY_NAMES, format_currency

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rich console for output
console = Console()


class SpendingAnalyzer:
    """Analyze spending patterns from normalized transaction data."""
    
    def __init__(self, transactions: List[Dict]):
        """
        Initialize analyzer with normalized transactions.
        
        Args:
            transactions: List of normalized transaction dictionaries
        """
        self.transactions = transactions
        self.valid_transactions = [t for t in transactions if t.get('is_valid', True)]
        self.invalid_transactions = [t for t in transactions if not t.get('is_valid', True)]
        
    def get_total_spending(self) -> Decimal:
        """Calculate total spending across all valid transactions."""
        total = Decimal('0')
        for t in self.valid_transactions:
            amount = t.get('normalized_amount')
            if amount is not None:
                total += amount
        return total
    
    def get_spending_by_category(self) -> Dict[str, Decimal]:
        """
        Calculate spending grouped by category.
        
        Returns:
            Dictionary mapping category to total amount
        """
        category_totals = defaultdict(lambda: Decimal('0'))
        
        for t in self.valid_transactions:
            category = t.get('category', 'other')
            amount = t.get('normalized_amount')
            
            if amount is not None:
                category_totals[category] += amount
        
        return dict(category_totals)
    
    def get_top_categories(self, n: int = 5) -> List[Tuple[str, Decimal, int]]:
        """
        Get top N spending categories.
        
        Args:
            n: Number of top categories to return
            
        Returns:
            List of tuples: (category, total_amount, transaction_count)
        """
        category_totals = self.get_spending_by_category()
        
        # Count transactions per category
        category_counts = defaultdict(int)
        for t in self.valid_transactions:
            category = t.get('category', 'other')
            category_counts[category] += 1
        
        # Combine and sort
        category_data = [
            (cat, amount, category_counts[cat])
            for cat, amount in category_totals.items()
        ]
        
        # Sort by amount (descending)
        category_data.sort(key=lambda x: x[1], reverse=True)
        
        return category_data[:n]
    
    def get_top_merchants(self, n: int = 10) -> List[Tuple[str, Decimal, int]]:
        """
        Get top N merchants by spending.
        
        Args:
            n: Number of top merchants to return
            
        Returns:
            List of tuples: (merchant, total_amount, transaction_count)
        """
        merchant_totals = defaultdict(lambda: Decimal('0'))
        merchant_counts = defaultdict(int)
        
        for t in self.valid_transactions:
            merchant = t.get('normalized_merchant', 'Unknown')
            amount = t.get('normalized_amount')
            
            if amount is not None:
                merchant_totals[merchant] += amount
                merchant_counts[merchant] += 1
        
        # Combine and sort
        merchant_data = [
            (merchant, amount, merchant_counts[merchant])
            for merchant, amount in merchant_totals.items()
        ]
        
        # Sort by amount (descending)
        merchant_data.sort(key=lambda x: x[1], reverse=True)
        
        return merchant_data[:n]
    
    def get_statistics(self) -> Dict:
        """
        Calculate comprehensive statistics.
        
        Returns:
            Dictionary with various statistics
        """
        if not self.valid_transactions:
            return {
                "total_transactions": 0,
                "valid_transactions": 0,
                "invalid_transactions": len(self.invalid_transactions),
                "total_spending": Decimal('0'),
                "average_transaction": Decimal('0'),
                "largest_transaction": Decimal('0'),
                "smallest_transaction": Decimal('0'),
                "unique_merchants": 0,
                "unique_categories": 0,
            }
        
        amounts = [
            t['normalized_amount']
            for t in self.valid_transactions
            if t.get('normalized_amount') is not None
        ]
        
        total_spending = sum(amounts)
        
        return {
            "total_transactions": len(self.transactions),
            "valid_transactions": len(self.valid_transactions),
            "invalid_transactions": len(self.invalid_transactions),
            "total_spending": total_spending,
            "average_transaction": total_spending / len(amounts) if amounts else Decimal('0'),
            "largest_transaction": max(amounts) if amounts else Decimal('0'),
            "smallest_transaction": min(amounts) if amounts else Decimal('0'),
            "unique_merchants": len(set(
                t.get('normalized_merchant', 'Unknown')
                for t in self.valid_transactions
            )),
            "unique_categories": len(set(
                t.get('category', 'other')
                for t in self.valid_transactions
            )),
        }
    
    def print_summary(self) -> None:
        """Print a formatted summary report using rich."""
        console.print()
        console.print(Panel.fit(
            "[bold cyan]Financial Transaction Analysis Report[/bold cyan]",
            border_style="cyan"
        ))
        
        stats = self.get_statistics()
        
        # Overview Statistics
        console.print("\n[bold]Overview[/bold]")
        overview_table = Table(show_header=False, box=None, padding=(0, 2))
        overview_table.add_column("Metric", style="cyan")
        overview_table.add_column("Value", style="green", justify="right")
        
        overview_table.add_row("Total Transactions", str(stats['total_transactions']))
        valid_pct = (stats['valid_transactions']/stats['total_transactions']*100) if stats['total_transactions'] > 0 else 0
        overview_table.add_row("Valid Transactions", f"{stats['valid_transactions']} ({valid_pct:.1f}%)")
        overview_table.add_row("Invalid Transactions", str(stats['invalid_transactions']))
        overview_table.add_row("Total Spending", format_currency(stats['total_spending']))
        overview_table.add_row("Average Transaction", format_currency(stats['average_transaction']))
        overview_table.add_row("Largest Transaction", format_currency(stats['largest_transaction']))
        overview_table.add_row("Smallest Transaction", format_currency(stats['smallest_transaction']))
        overview_table.add_row("Unique Merchants", str(stats['unique_merchants']))
        overview_table.add_row("Unique Categories", str(stats['unique_categories']))
        
        console.print(overview_table)
        
        # Top Categories
        console.print("\n[bold]Top Spending Categories[/bold]")
        category_table = Table(show_header=True, box=None)
        category_table.add_column("Rank", style="dim", width=6)
        category_table.add_column("Category", style="cyan")
        category_table.add_column("Amount", style="green", justify="right")
        category_table.add_column("Transactions", style="yellow", justify="right")
        category_table.add_column("% of Total", style="magenta", justify="right")
        
        top_categories = self.get_top_categories(n=5)
        total = stats['total_spending']
        
        for rank, (category, amount, count) in enumerate(top_categories, 1):
            display_name = CATEGORY_DISPLAY_NAMES.get(category, category.title())
            percentage = (amount / total * 100) if total > 0 else 0
            
            category_table.add_row(
                f"#{rank}",
                display_name,
                format_currency(amount),
                str(count),
                f"{percentage:.1f}%"
            )
        
        console.print(category_table)
        
        # Top Merchants
        console.print("\n[bold]Top Merchants[/bold]")
        merchant_table = Table(show_header=True, box=None)
        merchant_table.add_column("Rank", style="dim", width=6)
        merchant_table.add_column("Merchant", style="cyan")
        merchant_table.add_column("Amount", style="green", justify="right")
        merchant_table.add_column("Transactions", style="yellow", justify="right")
        
        top_merchants = self.get_top_merchants(n=5)
        
        for rank, (merchant, amount, count) in enumerate(top_merchants, 1):
            merchant_table.add_row(
                f"#{rank}",
                merchant,
                format_currency(amount),
                str(count)
            )
        
        console.print(merchant_table)
        
        console.print()
    
    def generate_text_report(self) -> str:
        """
        Generate a plain text report (for file output).
        
        Returns:
            Formatted text report as string
        """
        stats = self.get_statistics()
        report_lines = []
        
        report_lines.append("=" * 80)
        report_lines.append("FINANCIAL TRANSACTION ANALYSIS REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Overview
        report_lines.append("OVERVIEW")
        report_lines.append("-" * 80)
        report_lines.append(f"Total Transactions:    {stats['total_transactions']}")
        valid_pct = (stats['valid_transactions']/stats['total_transactions']*100) if stats['total_transactions'] > 0 else 0
        report_lines.append(f"Valid Transactions:    {stats['valid_transactions']} ({valid_pct:.1f}%)")
        report_lines.append(f"Invalid Transactions:  {stats['invalid_transactions']}")
        report_lines.append(f"Total Spending:        {format_currency(stats['total_spending'])}")
        report_lines.append(f"Average Transaction:   {format_currency(stats['average_transaction'])}")
        report_lines.append(f"Largest Transaction:   {format_currency(stats['largest_transaction'])}")
        report_lines.append(f"Smallest Transaction:  {format_currency(stats['smallest_transaction'])}")
        report_lines.append(f"Unique Merchants:      {stats['unique_merchants']}")
        report_lines.append(f"Unique Categories:     {stats['unique_categories']}")
        report_lines.append("")
        
        # Top Categories
        report_lines.append("TOP SPENDING CATEGORIES")
        report_lines.append("-" * 80)
        top_categories = self.get_top_categories(n=5)
        total = stats['total_spending']
        
        for rank, (category, amount, count) in enumerate(top_categories, 1):
            display_name = CATEGORY_DISPLAY_NAMES.get(category, category.title())
            percentage = (amount / total * 100) if total > 0 else 0
            report_lines.append(
                f"{rank}. {display_name:30s} {format_currency(amount):>15s} "
                f"({count:3d} transactions, {percentage:5.1f}%)"
            )
        report_lines.append("")
        
        # Top Merchants
        report_lines.append("TOP MERCHANTS")
        report_lines.append("-" * 80)
        top_merchants = self.get_top_merchants(n=10)
        
        for rank, (merchant, amount, count) in enumerate(top_merchants, 1):
            report_lines.append(
                f"{rank:2d}. {merchant:30s} {format_currency(amount):>15s} "
                f"({count:3d} transactions)"
            )
        report_lines.append("")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)


def analyze_transactions(transactions: List[Dict], output_file: Optional[str] = None) -> SpendingAnalyzer:
    """
    Analyze transactions and optionally save report to file.
    
    Args:
        transactions: List of normalized transaction dictionaries
        output_file: Optional path to save text report
        
    Returns:
        SpendingAnalyzer instance
    """
    analyzer = SpendingAnalyzer(transactions)
    
    # Print to console
    analyzer.print_summary()
    
    # Save to file if requested
    if output_file:
        report = analyzer.generate_text_report()
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        console.print(f"[green]Report saved to {output_file}[/green]\n")
    
    return analyzer


if __name__ == "__main__":
    # Quick testing
    import os
    from parser import parse_transactions_csv
    from normalizer import normalize_transaction
    
    console.print("\n[bold cyan]Testing Analyzer Module[/bold cyan]\n")
    
    # Get correct path to data (go up one directory)
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'messy_transactions.csv')
    output_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'spending_report.txt')
    
    # Parse and normalize test data
    transactions = parse_transactions_csv(data_path)
    normalized = []
    
    for t in transactions:
        result = normalize_transaction(t['date'], t['merchant'], t['amount'])
        result['row_number'] = t['row_number']
        normalized.append(result)
    
    # Analyze
    analyzer = analyze_transactions(normalized, output_file=output_path)
    
    console.print("[green]Analysis complete![/green]\n")