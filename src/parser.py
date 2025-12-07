"""
CSV Parser for financial transaction data.
Handles file reading, validation, and basic data quality checks.
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Expected CSV columns
REQUIRED_COLUMNS = {"date", "merchant", "amount"}
OPTIONAL_COLUMNS = {"category", "description", "notes"}


class ParserError(Exception):
    """Custom exception for parser-related errors."""
    pass


def validate_csv_structure(filepath: str) -> bool:
    """
    Validate that the CSV file has the required columns.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        True if valid, raises ParserError if invalid
        
    Raises:
        ParserError: If file doesn't exist or missing required columns
    """
    file_path = Path(filepath)
    
    # Check if file exists
    if not file_path.exists():
        raise ParserError(f"File not found: {filepath}")
    
    # Check if file is empty
    if file_path.stat().st_size == 0:
        raise ParserError(f"File is empty: {filepath}")
    
    # Check file extension
    if file_path.suffix.lower() not in ['.csv', '.txt']:
        logger.warning(f"Unexpected file extension: {file_path.suffix}. Proceeding anyway...")
    
    # Read header and validate columns
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Get the fieldnames (column headers)
            if reader.fieldnames is None:
                raise ParserError("CSV file has no header row")
            
            # Convert to set for comparison (case-insensitive)
            columns = {col.lower().strip() for col in reader.fieldnames}
            
            # Check for required columns
            missing = REQUIRED_COLUMNS - columns
            if missing:
                raise ParserError(
                    f"Missing required columns: {missing}. "
                    f"Found columns: {columns}"
                )
            
            logger.info(f"CSV validation passed. Found columns: {columns}")
            return True
            
    except UnicodeDecodeError:
        raise ParserError(
            f"File encoding error. Expected UTF-8 encoding. "
            f"Try saving the file with UTF-8 encoding."
        )
    except csv.Error as e:
        raise ParserError(f"CSV parsing error: {e}")


def parse_transactions_csv(filepath: str, skip_validation: bool = False) -> List[Dict]:
    """
    Parse transactions from a CSV file.
    
    Args:
        filepath: Path to the CSV file
        skip_validation: If True, skip structure validation (for testing)
        
    Returns:
        List of transaction dictionaries
        
    Raises:
        ParserError: If file cannot be parsed
        
    Example:
        >>> transactions = parse_transactions_csv("data/messy_transactions.csv")
        >>> len(transactions)
        100
    """
    # Validate structure first
    if not skip_validation:
        validate_csv_structure(filepath)
    
    transactions = []
    errors = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):  # start=2 because row 1 is header
                # Skip completely empty rows
                if all(not value or not value.strip() for value in row.values()):
                    logger.debug(f"Skipping empty row {row_num}")
                    continue
                
                # Normalize column names (lowercase, strip whitespace)
                normalized_row = {
                    key.lower().strip(): value.strip() if value else ""
                    for key, value in row.items()
                }
                
                # Check that row has required fields
                if not all(key in normalized_row for key in REQUIRED_COLUMNS):
                    error_msg = f"Row {row_num}: Missing required columns"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    continue
                
                # Extract transaction data
                transaction = {
                    "row_number": row_num,
                    "date": normalized_row.get("date", ""),
                    "merchant": normalized_row.get("merchant", ""),
                    "amount": normalized_row.get("amount", ""),
                }
                
                # Add optional fields if present
                if "category" in normalized_row:
                    transaction["category"] = normalized_row["category"]
                if "description" in normalized_row:
                    transaction["description"] = normalized_row["description"]
                if "notes" in normalized_row:
                    transaction["notes"] = normalized_row["notes"]
                
                transactions.append(transaction)
        
        logger.info(f"Successfully parsed {len(transactions)} transactions from {filepath}")
        
        if errors:
            logger.warning(f"Encountered {len(errors)} errors during parsing")
        
        return transactions
        
    except UnicodeDecodeError:
        raise ParserError(
            f"File encoding error. Expected UTF-8 encoding. "
            f"Try saving the file with UTF-8 encoding."
        )
    except Exception as e:
        raise ParserError(f"Unexpected error while parsing CSV: {e}")


def get_parse_statistics(transactions: List[Dict]) -> Dict:
    """
    Get statistics about parsed transactions.
    
    Args:
        transactions: List of parsed transaction dictionaries
        
    Returns:
        Dictionary with parsing statistics
    """
    if not transactions:
        return {
            "total_rows": 0,
            "empty_dates": 0,
            "empty_merchants": 0,
            "empty_amounts": 0,
        }
    
    stats = {
        "total_rows": len(transactions),
        "empty_dates": sum(1 for t in transactions if not t.get("date")),
        "empty_merchants": sum(1 for t in transactions if not t.get("merchant")),
        "empty_amounts": sum(1 for t in transactions if not t.get("amount")),
    }
    
    return stats


def write_transactions_csv(
    transactions: List[Dict],
    filepath: str,
    columns: Optional[List[str]] = None
) -> None:
    """
    Write transactions to a CSV file.
    
    Args:
        transactions: List of transaction dictionaries
        filepath: Output file path
        columns: List of column names to include (default: all columns)
        
    Example:
        >>> write_transactions_csv(
        ...     transactions,
        ...     "output/cleaned.csv",
        ...     columns=["date", "merchant", "amount", "category"]
        ... )
    """
    if not transactions:
        logger.warning("No transactions to write")
        return
    
    # Determine columns to write
    if columns is None:
        # Get all unique keys from all transactions
        all_keys = set()
        for t in transactions:
            all_keys.update(t.keys())
        columns = sorted(all_keys)
    
    # Create output directory if it doesn't exist
    output_path = Path(filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            
            for transaction in transactions:
                writer.writerow(transaction)
        
        logger.info(f"Successfully wrote {len(transactions)} transactions to {filepath}")
        
    except Exception as e:
        raise ParserError(f"Error writing CSV file: {e}")


if __name__ == "__main__":
    print("Testing parser functions...\n")
    
    # Test with messy transactions
    print("=" * 80)
    print("Test 1: Parse messy_transactions.csv")
    print("=" * 80)
    
    try:
        transactions = parse_transactions_csv("data/messy_transactions.csv")
        print(f"Successfully parsed {len(transactions)} transactions\n")
        
        # Show first 3 transactions
        print("First 3 transactions:")
        for i, t in enumerate(transactions[:3], 1):
            print(f"  {i}. Row {t['row_number']}: {t['date']:20s} | {t['merchant']:25s} | {t['amount']}")
        
        # Show statistics
        stats = get_parse_statistics(transactions)
        print(f"\nParsing Statistics:")
        print(f"  Total rows: {stats['total_rows']}")
        print(f"  Empty dates: {stats['empty_dates']}")
        print(f"  Empty merchants: {stats['empty_merchants']}")
        print(f"  Empty amounts: {stats['empty_amounts']}")
        
    except ParserError as e:
        print(f"Parser Error: {e}")
    
    # Test with edge cases
    print("\n" + "=" * 80)
    print("Test 2: Parse edge_cases.csv")
    print("=" * 80)
    
    try:
        edge_transactions = parse_transactions_csv("data/edge_cases.csv")
        print(f"✅ Successfully parsed {len(edge_transactions)} transactions\n")
        
        # Show statistics
        stats = get_parse_statistics(edge_transactions)
        print(f"Parsing Statistics:")
        print(f"  Total rows: {stats['total_rows']}")
        print(f"  Empty dates: {stats['empty_dates']}")
        print(f"  Empty merchants: {stats['empty_merchants']}")
        print(f"  Empty amounts: {stats['empty_amounts']}")
        
    except ParserError as e:
        print(f"Parser Error: {e}")
    
    # Test error handling
    print("\n" + "=" * 80)
    print("Test 3: Error Handling")
    print("=" * 80)
    
    # Test non-existent file
    try:
        parse_transactions_csv("data/nonexistent.csv")
    except ParserError as e:
        print(f"Correctly caught error: {e}")
    
    # Test write functionality
    print("\n" + "=" * 80)
    print("Test 4: Write CSV")
    print("=" * 80)
    
    try:
        # Create a small test dataset
        test_data = [
            {"date": "2023-01-01", "merchant": "Test Store", "amount": "100.00"},
            {"date": "2023-01-02", "merchant": "Another Store", "amount": "50.00"},
        ]
        
        write_transactions_csv(test_data, "output/test_write.csv")
        print("✅ Successfully wrote test CSV")
        
        # Verify by reading it back
        verify = parse_transactions_csv("output/test_write.csv")
        print(f"✅ Verified: Read back {len(verify)} transactions")
        
    except ParserError as e:
        print(f"Write Error: {e}")
    
    print("\n" + "=" * 80)
    print("All parser tests completed!")
    print("=" * 80)