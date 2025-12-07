"""
Normalization functions for financial transaction data.
Handles messy dates, merchant names, and amount formats.
"""

import re
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple
from dateutil import parser as date_parser
from rapidfuzz import fuzz

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Merchant category mappings (knowledge base for fuzzy matching)
MERCHANT_CATEGORIES = {
    "uber": ["uber", "uber trip", "uber eats", "uber technologies"],
    "amazon": ["amazon", "amzn", "amazon prime", "amazon mktplace"],
    "starbucks": ["starbucks", "sbux", "starbucks coffee"],
    "target": ["target", "tgt"],
    "mcdonalds": ["mcdonald", "mcd"],
    "gas_station": ["shell", "chevron", "bp", "exxon", "exxonmobil"],
    "grocery": ["whole foods", "trader joe", "safeway", "trader joes"],
    "restaurant": ["chipotle", "panera", "in-n-out", "in n out"],
    "utility": ["pg&e", "pge", "pacific gas", "comcast", "at&t", "att"],
    "entertainment": ["netflix", "spotify", "amc"],
}

# Fuzzy matching threshold (85% similarity)
FUZZY_MATCH_THRESHOLD = 85


def normalize_date(date_string: str) -> Optional[str]:
    """
    Normalize various date formats to ISO format (YYYY-MM-DD).
    
    Args:
        date_string: Date in any common format
        
    Returns:
        ISO formatted date string (YYYY-MM-DD) or None if invalid
        
    Examples:
        >>> normalize_date("2023-01-15")
        '2023-01-15'
        >>> normalize_date("Jan 15, 2023")
        '2023-01-15'
        >>> normalize_date("01/15/2023")
        '2023-01-15'
    """
    if not date_string or not isinstance(date_string, str):
        logger.warning(f"Empty or invalid date: {date_string}")
        return None
    
    # Strip whitespace
    date_string = date_string.strip()
    
    if not date_string:
        logger.warning("Empty date string after stripping")
        return None
    
    try:
        # Use dateutil parser for robust parsing
        # dayfirst=False assumes MM/DD/YYYY (US format) for ambiguous dates
        parsed_date = date_parser.parse(date_string, dayfirst=False)
        
        # Validate the date is reasonable (not too far in past/future)
        current_year = datetime.now().year
        if parsed_date.year < 1900 or parsed_date.year > current_year + 1:
            logger.warning(f"Date year out of reasonable range: {parsed_date.year}")
            return None
        
        # Return ISO format
        return parsed_date.strftime("%Y-%m-%d")
        
    except (ValueError, OverflowError) as e:
        logger.warning(f"Failed to parse date '{date_string}': {e}")
        return None


def normalize_merchant(merchant_name: str) -> Tuple[str, str]:
    """
    Normalize merchant name and categorize using fuzzy string matching.
    
    Args:
        merchant_name: Raw merchant name (e.g., "STARBUCKS #1234")
        
    Returns:
        Tuple of (normalized_name, category)
        
    Examples:
        >>> normalize_merchant("UBER *TRIP")
        ('Uber', 'uber')
        >>> normalize_merchant("STARBUCKS #1234")
        ('Starbucks', 'starbucks')
    """
    if not merchant_name or not isinstance(merchant_name, str):
        logger.warning(f"Empty or invalid merchant: {merchant_name}")
        return "Unknown", "other"
    
    # Clean the merchant name
    cleaned = merchant_name.strip()
    
    if not cleaned:
        logger.warning("Empty merchant after stripping")
        return "Unknown", "other"
    
    # Remove special characters and extra spaces for comparison
    # Keep the original for display, use cleaned version for matching
    comparison_name = re.sub(r'[^a-zA-Z0-9\s]', '', cleaned).lower()
    comparison_name = re.sub(r'\s+', ' ', comparison_name).strip()
    
    # Try to match against known merchants
    best_match_category = None
    best_match_score = 0
    best_match_name = None
    
    for category, keywords in MERCHANT_CATEGORIES.items():
        for keyword in keywords:
            # Use fuzzy matching to handle variations
            score = fuzz.partial_ratio(comparison_name, keyword.lower())
            
            if score > best_match_score and score >= FUZZY_MATCH_THRESHOLD:
                best_match_score = score
                best_match_category = category
                best_match_name = keyword.title()  # Capitalize for display
    
    if best_match_category and best_match_name:
        # Clean up the display name
        display_name = best_match_name
        return display_name, best_match_category
    else:
        # No match found - return cleaned original
        display_name = cleaned.title() if len(cleaned) < 50 else cleaned[:50] + "..."
        return display_name, "other"


def normalize_amount(amount_string: str) -> Optional[Decimal]:
    """
    Normalize various amount formats to Decimal for precision.
    
    Args:
        amount_string: Amount in various formats (e.g., "$45.50", "45.50 USD")
        
    Returns:
        Decimal value or None if invalid
        
    Examples:
        >>> normalize_amount("$45.50")
        Decimal('45.50')
        >>> normalize_amount("$ 45.50")
        Decimal('45.50')
        >>> normalize_amount("45.50 USD")
        Decimal('45.50')
        >>> normalize_amount("-$25.00")
        Decimal('-25.00')
    """
    if not amount_string or not isinstance(amount_string, str):
        logger.warning(f"Empty or invalid amount: {amount_string}")
        return None
    
    # Strip whitespace
    cleaned = amount_string.strip()
    
    if not cleaned:
        logger.warning("Empty amount after stripping")
        return None
    
    # Remove currency symbols and text
    # Keep: digits, decimal point, negative sign, comma (for thousands)
    # Remove: $, €, ¥, USD, EUR, etc.
    
    # First, check if negative (starts with -)
    is_negative = cleaned.startswith('-')
    
    # Remove common currency symbols and text
    cleaned = re.sub(r'[€¥£]', '', cleaned)  # Non-USD currency symbols
    cleaned = re.sub(r'\$', '', cleaned)      # Dollar sign
    cleaned = re.sub(r'USD|EUR|GBP|JPY', '', cleaned, flags=re.IGNORECASE)  # Currency codes
    
    # Remove extra spaces
    cleaned = cleaned.strip()
    
    # Handle negative sign (might be at beginning or after currency symbol)
    if '-' in cleaned:
        is_negative = True
        cleaned = cleaned.replace('-', '')
    
    # Remove commas (thousand separators)
    cleaned = cleaned.replace(',', '')
    
    # At this point, should only have digits and decimal point
    # Extract just the numeric part
    match = re.search(r'(\d+\.?\d*)', cleaned)
    
    if not match:
        logger.warning(f"No numeric value found in amount: {amount_string}")
        return None
    
    numeric_string = match.group(1)
    
    # Add negative sign back if needed
    if is_negative:
        numeric_string = '-' + numeric_string
    
    try:
        # Convert to Decimal for financial precision
        amount = Decimal(numeric_string)
        
        # Round to 2 decimal places (standard for currency)
        amount = amount.quantize(Decimal('0.01'))
        
        # Validate reasonable range (e.g., -$1M to $1M)
        if amount < Decimal('-1000000') or amount > Decimal('1000000'):
            logger.warning(f"Amount out of reasonable range: {amount}")
            return None
        
        return amount
        
    except (InvalidOperation, ValueError) as e:
        logger.warning(f"Failed to convert amount '{amount_string}': {e}")
        return None


def normalize_transaction(date: str, merchant: str, amount: str) -> dict:
    """
    Normalize a complete transaction record.
    
    Args:
        date: Raw date string
        merchant: Raw merchant name
        amount: Raw amount string
        
    Returns:
        Dictionary with normalized fields and validation status
    """
    normalized = {
        "raw_date": date,
        "raw_merchant": merchant,
        "raw_amount": amount,
        "normalized_date": None,
        "normalized_merchant": None,
        "category": None,
        "normalized_amount": None,
        "is_valid": True,
        "errors": []
    }
    
    # Normalize date
    normalized_date = normalize_date(date)
    if normalized_date is None:
        normalized["is_valid"] = False
        normalized["errors"].append(f"Invalid date: {date}")
    normalized["normalized_date"] = normalized_date
    
    # Normalize merchant
    merchant_name, category = normalize_merchant(merchant)
    normalized["normalized_merchant"] = merchant_name
    normalized["category"] = category
    
    # Normalize amount
    normalized_amount = normalize_amount(amount)
    if normalized_amount is None:
        normalized["is_valid"] = False
        normalized["errors"].append(f"Invalid amount: {amount}")
    normalized["normalized_amount"] = normalized_amount
    
    return normalized


def get_normalization_stats(transactions: list) -> dict:
    """
    Calculate statistics about normalization success rate.
    
    Args:
        transactions: List of normalized transaction dictionaries
        
    Returns:
        Dictionary with statistics
    """
    total = len(transactions)
    valid = sum(1 for t in transactions if t["is_valid"])
    invalid = total - valid
    
    date_errors = sum(1 for t in transactions if t["normalized_date"] is None)
    amount_errors = sum(1 for t in transactions if t["normalized_amount"] is None)
    
    categories = {}
    for t in transactions:
        cat = t.get("category", "other")
        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "total_transactions": total,
        "valid_transactions": valid,
        "invalid_transactions": invalid,
        "success_rate": (valid / total * 100) if total > 0 else 0,
        "date_errors": date_errors,
        "amount_errors": amount_errors,
        "categories": categories
    }


if __name__ == "__main__":
    # Quick testing
    print("Testing normalizer functions...\n")
    
    # Test dates
    test_dates = [
        "2023-01-15",
        "Jan 15, 2023",
        "01/15/2023",
        "15/01/2023",
        "Invalid Date",
        "",
    ]
    
    print("Date Normalization:")
    for date in test_dates:
        result = normalize_date(date)
        print(f"  {date:20s} → {result}")
    
    # Test merchants
    test_merchants = [
        "UBER *TRIP",
        "Uber Technologies",
        "STARBUCKS #1234",
        "Amazon.com",
        "",
    ]
    
    print("\nMerchant Normalization:")
    for merchant in test_merchants:
        name, category = normalize_merchant(merchant)
        print(f"  {merchant:25s} → {name:20s} ({category})")
    
    # Test amounts
    test_amounts = [
        "$45.50",
        "$ 45.50",
        "45.50 USD",
        "-$25.00",
        "€50.00",
        "",
    ]
    
    print("\nAmount Normalization:")
    for amount in test_amounts:
        result = normalize_amount(amount)
        print(f"  {amount:20s} → {result}")