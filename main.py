"""
Smart Financial Parser - CLI Interface
Parse, normalize, and analyze messy financial transaction data.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.parser import parse_transactions_csv, write_transactions_csv, ParserError
from src.normalizer import normalize_transaction, get_normalization_stats
from src.analyzer import analyze_transactions

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors by default
    format='%(levelname)s: %(message)s'
)

console = Console()


def print_banner():
    """Print application banner."""
    banner = """
[bold cyan]Smart Financial Parser[/bold cyan]
Parse, normalize, and analyze messy financial data
    """
    console.print(Panel(banner, border_style="cyan"))


def validate_input_file(filepath: str) -> bool:
    """
    Validate that input file exists and is readable.
    
    Args:
        filepath: Path to input CSV file
        
    Returns:
        True if valid, False otherwise
    """
    path = Path(filepath)
    
    if not path.exists():
        console.print(f"[red]Error: File not found: {filepath}[/red]")
        return False
    
    if not path.is_file():
        console.print(f"[red]Error: Not a file: {filepath}[/red]")
        return False
    
    if path.suffix.lower() not in ['.csv', '.txt']:
        console.print(f"[yellow]Warning: Unexpected file extension: {path.suffix}[/yellow]")
        console.print("[yellow]   Expected .csv or .txt file[/yellow]")
    
    return True


def process_transactions(
    input_file: str,
    output_file: Optional[str] = None,
    report_file: Optional[str] = None,
    verbose: bool = False
) -> int:
    """
    Main processing pipeline: parse → normalize → analyze.
    
    Args:
        input_file: Path to input CSV file
        output_file: Optional path to write cleaned CSV
        report_file: Optional path to write analysis report
        verbose: Enable verbose logging
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Enable verbose logging if requested
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    
    try:
        # Parse CSV
        console.print("\n[bold]Parsing CSV file...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Reading transactions...", total=None)
            transactions = parse_transactions_csv(input_file)
            progress.update(task, completed=True)
        
        console.print(f"[green]Parsed {len(transactions)} transactions[/green]")
        
        if len(transactions) == 0:
            console.print("[yellow]No transactions found in file[/yellow]")
            return 1
        
        # Normalize transactions
        console.print("\n[bold]Normalizing data...[/bold]")
        
        normalized_results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Normalizing transactions...", total=len(transactions))
            
            for t in transactions:
                result = normalize_transaction(
                    t.get('date', ''),
                    t.get('merchant', ''),
                    t.get('amount', '')
                )
                result['row_number'] = t.get('row_number')
                normalized_results.append(result)
                progress.advance(task)
        
        # Get normalization statistics
        stats = get_normalization_stats(normalized_results)
        
        console.print(
            f"[green]Normalized {stats['valid_transactions']}/{stats['total_transactions']} "
            f"transactions ({stats['success_rate']:.1f}% success rate)[/green]"
        )
        
        if stats['date_errors'] > 0:
            console.print(f"[yellow]{stats['date_errors']} date parsing errors[/yellow]")
        if stats['amount_errors'] > 0:
            console.print(f"[yellow]{stats['amount_errors']} amount parsing errors[/yellow]")
        
        # Create output directory if needed
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        if report_file:
            report_path = Path(report_file)
            report_path.parent.mkdir(parents=True, exist_ok=True)

        # Write cleaned output (if requested)
        if output_file:
            console.print(f"\n[bold]Writing cleaned data...[/bold]")
            
            cleaned_transactions = []
            for result in normalized_results:
                if result['is_valid']:
                    cleaned_transactions.append({
                        'date': result['normalized_date'],
                        'merchant': result['normalized_merchant'],
                        'amount': str(result['normalized_amount']),
                        'category': result['category'],
                    })
            
            write_transactions_csv(
                cleaned_transactions,
                output_file,
                columns=['date', 'merchant', 'amount', 'category']
            )
            
            console.print(f"[green]Wrote {len(cleaned_transactions)} cleaned transactions to {output_file}[/green]")
        
        # Generate analysis report
        console.print(f"\n[bold]Analyzing spending patterns...[/bold]")
        
        analyzer = analyze_transactions(normalized_results, output_file=report_file)
        
        # Show validation summary if there were errors
        if stats['invalid_transactions'] > 0:
            console.print("\n[yellow]Validation Summary:[/yellow]")
            console.print(f"   {stats['invalid_transactions']} transactions had errors and were excluded from analysis")
            
            if verbose:
                console.print("\n[dim]Invalid transactions:[/dim]")
                invalid_count = 0
                for result in normalized_results:
                    if not result['is_valid']:
                        console.print(f"[dim]   Row {result['row_number']}: {', '.join(result['errors'])}[/dim]")
                        invalid_count += 1
                        if invalid_count >= 10:  # Limit to first 10 invalid transactions
                            remaining = stats['invalid_transactions'] - 10
                            if remaining > 0:
                                console.print(f"[dim]   ... and {remaining} more[/dim]")
                            break
        
        console.print("\n[bold green]Processing complete![/bold green]\n")
        return 0
        
    except ParserError as e:
        console.print(f"\n[red]Parser Error: {e}[/red]")
        return 1
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        if verbose:
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        return 1


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Parse, normalize, and analyze messy financial transaction data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - analyze transactions
  python main.py data/messy_transactions.csv

  # Save cleaned output
  python main.py data/messy_transactions.csv --output cleaned.csv

  # Generate analysis report
  python main.py data/messy_transactions.csv --report spending_report.txt

  # Full pipeline with all outputs
  python main.py data/messy_transactions.csv --output cleaned.csv --report report.txt

  # Verbose mode for debugging
  python main.py data/messy_transactions.csv --verbose
        """
    )
    
    # Required arguments
    parser.add_argument(
        'input',
        help='Path to input CSV file (must have columns: date, merchant, amount)'
    )
    
    # Optional arguments
    parser.add_argument(
        '-o', '--output',
        help='Path to write cleaned/normalized CSV output',
        metavar='FILE'
    )
    
    parser.add_argument(
        '-r', '--report',
        help='Path to write analysis report (plain text)',
        metavar='FILE'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output (show detailed logging)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Smart Financial Parser v1.0.0'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Validate input file
    if not validate_input_file(args.input):
        return 1
    
    # Process transactions
    exit_code = process_transactions(
        input_file=args.input,
        output_file=f"output/{args.output}" if args.output else None,
        report_file=f"output/{args.report}" if args.report else None,
        verbose=args.verbose
    )
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())