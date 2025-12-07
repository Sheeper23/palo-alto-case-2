"""
Utility functions and constants shared across modules.
"""

from typing import Dict

# Category display names (for reporting)
CATEGORY_DISPLAY_NAMES: Dict[str, str] = {
    "uber": "Transportation (Uber)",
    "amazon": "Shopping (Amazon)",
    "starbucks": "Coffee & Cafes",
    "target": "Shopping (Target)",
    "mcdonalds": "Fast Food",
    "gas_station": "Gas & Fuel",
    "grocery": "Groceries",
    "restaurant": "Restaurants",
    "utility": "Utilities",
    "entertainment": "Entertainment",
    "other": "Other/Uncategorized",
}


def format_currency(amount, symbol: str = "$") -> str:
    """
    Format a decimal amount as currency.
    
    Args:
        amount: Decimal or float amount
        symbol: Currency symbol
        
    Returns:
        Formatted currency string
        
    Example:
        >>> from decimal import Decimal
        >>> format_currency(Decimal("1234.56"))
        '$1,234.56'
    """
    if amount is None:
        return "N/A"
    
    # Handle negative amounts
    if amount < 0:
        return f"-{symbol}{abs(amount):,.2f}"
    return f"{symbol}{amount:,.2f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format a decimal as a percentage.
    
    Args:
        value: Decimal value (e.g., 0.856 for 85.6%)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
        
    Example:
        >>> format_percentage(0.856)
        '85.6%'
    """
    return f"{value * 100:.{decimals}f}%"


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def print_section_header(title: str, width: int = 80) -> None:
    """Print a formatted section header."""
    print()
    print("=" * width)
    print(f"{title:^{width}}")
    print("=" * width)


def print_subsection_header(title: str, width: int = 80) -> None:
    """Print a formatted subsection header."""
    print()
    print(f"{title}")
    print("-" * width)


if __name__ == "__main__":
    # Quick testing
    from decimal import Decimal
    
    print("Testing utility functions...\n")
    
    # Test currency formatting
    print("Currency Formatting:")
    print(f"  {format_currency(Decimal('1234.56'))}")
    print(f"  {format_currency(Decimal('-25.00'))}")
    print(f"  {format_currency(Decimal('0.01'))}")
    print(f"  {format_currency(None)}")
    
    # Test percentage formatting
    print("\nPercentage Formatting:")
    print(f"  {format_percentage(0.856)}")
    print(f"  {format_percentage(0.05, decimals=2)}")
    
    # Test string truncation
    print("\nString Truncation:")
    print(f"  {truncate_string('This is a very long merchant name that needs truncation', 30)}")
    
    # Test headers
    print_section_header("Main Section")
    print_subsection_header("Subsection Title")