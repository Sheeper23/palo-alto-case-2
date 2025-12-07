"""
Unit tests for the CSV parser module.
Tests file validation, parsing logic, error handling, and edge cases.
"""

import pytest
import csv
from pathlib import Path

from src.parser import (
    parse_transactions_csv,
    validate_csv_structure,
    get_parse_statistics,
    write_transactions_csv,
    ParserError
)


class TestCSVValidation:
    """Test CSV file validation and structure checks."""
    
    def test_validate_nonexistent_file(self):
        """Test that validation fails for non-existent files."""
        with pytest.raises(ParserError, match="File not found"):
            validate_csv_structure("nonexistent_file.csv")
    
    def test_validate_empty_file(self, tmp_path):
        """Test that validation fails for empty files."""
        empty_file = tmp_path / "empty.csv"
        empty_file.touch()
        
        with pytest.raises(ParserError, match="File is empty"):
            validate_csv_structure(str(empty_file))
    
    def test_validate_missing_columns(self, tmp_path):
        """Test that validation fails when required columns are missing."""
        csv_file = tmp_path / "missing_columns.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "merchant"])  # Missing 'amount'
            writer.writerow(["2023-01-01", "Store"])
        
        with pytest.raises(ParserError, match="Missing required columns"):
            validate_csv_structure(str(csv_file))
    
    def test_validate_valid_csv(self, tmp_path):
        """Test that validation passes for properly formatted CSV."""
        csv_file = tmp_path / "valid.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "merchant", "amount"])
            writer.writerow(["2023-01-01", "Store", "100.00"])
        
        assert validate_csv_structure(str(csv_file)) is True
    
    def test_validate_case_insensitive_columns(self, tmp_path):
        """Test that column validation is case-insensitive."""
        csv_file = tmp_path / "case_test.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "MERCHANT", "Amount"])  # Mixed case
            writer.writerow(["2023-01-01", "Store", "100.00"])
        
        assert validate_csv_structure(str(csv_file)) is True
    
    def test_validate_extra_columns(self, tmp_path):
        """Test that validation passes with extra optional columns."""
        csv_file = tmp_path / "extra_columns.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "merchant", "amount", "category", "notes"])
            writer.writerow(["2023-01-01", "Store", "100.00", "Shopping", "Test"])
        
        assert validate_csv_structure(str(csv_file)) is True


class TestCSVParsing:
    """Test CSV parsing functionality."""
    
    def test_parse_basic_transactions(self, tmp_path):
        """Test parsing a simple, well-formatted CSV."""
        csv_file = tmp_path / "basic.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "merchant", "amount"])
            writer.writerow(["2023-01-01", "Store A", "100.00"])
            writer.writerow(["2023-01-02", "Store B", "50.00"])
        
        transactions = parse_transactions_csv(str(csv_file))
        
        assert len(transactions) == 2
        assert transactions[0]["date"] == "2023-01-01"
        assert transactions[0]["merchant"] == "Store A"
        assert transactions[0]["amount"] == "100.00"
        assert transactions[0]["row_number"] == 2
    
    def test_parse_with_whitespace(self, tmp_path):
        """Test that parser strips whitespace from values."""
        csv_file = tmp_path / "whitespace.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["  date  ", " merchant ", " amount  "])
            writer.writerow(["  2023-01-01  ", " Store  ", "  100.00  "])
        
        transactions = parse_transactions_csv(str(csv_file))
        
        assert len(transactions) == 1
        assert transactions[0]["date"] == "2023-01-01"
        assert transactions[0]["merchant"] == "Store"
        assert transactions[0]["amount"] == "100.00"
    
    def test_parse_skips_empty_rows(self, tmp_path):
        """Test that parser skips completely empty rows."""
        csv_file = tmp_path / "empty_rows.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "merchant", "amount"])
            writer.writerow(["2023-01-01", "Store A", "100.00"])
            writer.writerow(["", "", ""])  # Empty row
            writer.writerow(["2023-01-02", "Store B", "50.00"])
        
        transactions = parse_transactions_csv(str(csv_file))
        
        assert len(transactions) == 2
        assert transactions[0]["date"] == "2023-01-01"
        assert transactions[1]["date"] == "2023-01-02"
    
    def test_parse_preserves_row_numbers(self, tmp_path):
        """Test that row numbers are correctly tracked."""
        csv_file = tmp_path / "row_numbers.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "merchant", "amount"])
            writer.writerow(["2023-01-01", "Store A", "100.00"])  # Row 2
            writer.writerow(["", "", ""])  # Row 3 (skipped)
            writer.writerow(["2023-01-02", "Store B", "50.00"])   # Row 4
        
        transactions = parse_transactions_csv(str(csv_file))
        
        assert len(transactions) == 2
        assert transactions[0]["row_number"] == 2
        assert transactions[1]["row_number"] == 4
    
    def test_parse_with_optional_columns(self, tmp_path):
        """Test that optional columns are preserved if present."""
        csv_file = tmp_path / "optional.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "merchant", "amount", "category", "notes"])
            writer.writerow(["2023-01-01", "Store", "100.00", "Shopping", "Test note"])
        
        transactions = parse_transactions_csv(str(csv_file))
        
        assert len(transactions) == 1
        assert transactions[0]["category"] == "Shopping"
        assert transactions[0]["notes"] == "Test note"
    
    def test_parse_messy_data(self, tmp_path):
        """Test parsing with various messy formats (integration test)."""
        csv_file = tmp_path / "messy.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "merchant", "amount"])
            writer.writerow(["2023-01-01", "UBER *TRIP", "$50.00"])
            writer.writerow(["Jan 15, 2023", "Starbucks #1234", "$ 5.50"])
            writer.writerow(["01/20/2023", "AMAZON.COM", "USD 125.99"])
        
        transactions = parse_transactions_csv(str(csv_file))
        
        assert len(transactions) == 3
        # Parser should preserve raw values (normalization happens later)
        assert transactions[0]["merchant"] == "UBER *TRIP"
        assert transactions[1]["amount"] == "$ 5.50"


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_parse_unicode_characters(self, tmp_path):
        """Test parsing with unicode/accented characters."""
        csv_file = tmp_path / "unicode.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "merchant", "amount"])
            writer.writerow(["2023-01-01", "Café Résumé", "25.00"])
            writer.writerow(["2023-01-02", "José's Taquería", "15.50"])
        
        transactions = parse_transactions_csv(str(csv_file))
        
        assert len(transactions) == 2
        assert transactions[0]["merchant"] == "Café Résumé"
        assert transactions[1]["merchant"] == "José's Taquería"
    
    def test_parse_empty_values(self, tmp_path):
        """Test parsing rows with empty values in required fields."""
        csv_file = tmp_path / "empty_values.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "merchant", "amount"])
            writer.writerow(["2023-01-01", "", "100.00"])  # Empty merchant
            writer.writerow(["", "Store", "50.00"])         # Empty date
            writer.writerow(["2023-01-03", "Store", ""])    # Empty amount
        
        transactions = parse_transactions_csv(str(csv_file))
        
        # Parser should include rows with empty values (normalizer will handle validation)
        assert len(transactions) == 3
        assert transactions[0]["merchant"] == ""
        assert transactions[1]["date"] == ""
        assert transactions[2]["amount"] == ""
    
    def test_parse_special_characters(self, tmp_path):
        """Test parsing with special characters."""
        csv_file = tmp_path / "special.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "merchant", "amount"])
            writer.writerow(["2023-01-01", "Store & Co.", "-$25.00"])
            writer.writerow(["2023-01-02", "Bob's Place", "$1,234.56"])
        
        transactions = parse_transactions_csv(str(csv_file))
        
        assert len(transactions) == 2
        assert transactions[0]["merchant"] == "Store & Co."
        assert transactions[0]["amount"] == "-$25.00"


class TestParseStatistics:
    """Test parsing statistics calculation."""
    
    def test_statistics_empty_list(self):
        """Test statistics for empty transaction list."""
        stats = get_parse_statistics([])
        
        assert stats["total_rows"] == 0
        assert stats["empty_dates"] == 0
        assert stats["empty_merchants"] == 0
        assert stats["empty_amounts"] == 0
    
    def test_statistics_all_valid(self):
        """Test statistics for all valid transactions."""
        transactions = [
            {"date": "2023-01-01", "merchant": "Store A", "amount": "100.00"},
            {"date": "2023-01-02", "merchant": "Store B", "amount": "50.00"},
        ]
        
        stats = get_parse_statistics(transactions)
        
        assert stats["total_rows"] == 2
        assert stats["empty_dates"] == 0
        assert stats["empty_merchants"] == 0
        assert stats["empty_amounts"] == 0
    
    def test_statistics_with_empty_fields(self):
        """Test statistics counting empty fields."""
        transactions = [
            {"date": "", "merchant": "Store A", "amount": "100.00"},
            {"date": "2023-01-02", "merchant": "", "amount": "50.00"},
            {"date": "2023-01-03", "merchant": "Store C", "amount": ""},
        ]
        
        stats = get_parse_statistics(transactions)
        
        assert stats["total_rows"] == 3
        assert stats["empty_dates"] == 1
        assert stats["empty_merchants"] == 1
        assert stats["empty_amounts"] == 1


class TestWriteTransactions:
    """Test writing transactions to CSV."""
    
    def test_write_basic_transactions(self, tmp_path):
        """Test writing transactions to a CSV file."""
        csv_file = tmp_path / "output.csv"
        
        transactions = [
            {"date": "2023-01-01", "merchant": "Store A", "amount": "100.00"},
            {"date": "2023-01-02", "merchant": "Store B", "amount": "50.00"},
        ]
        
        write_transactions_csv(transactions, str(csv_file))
        
        assert csv_file.exists()
        
        # Verify by reading back
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]["date"] == "2023-01-01"
        assert rows[1]["merchant"] == "Store B"
    
    def test_write_with_specific_columns(self, tmp_path):
        """Test writing only specific columns."""
        csv_file = tmp_path / "output.csv"
        
        transactions = [
            {"date": "2023-01-01", "merchant": "Store A", "amount": "100.00", "extra": "ignore"},
        ]
        
        write_transactions_csv(
            transactions,
            str(csv_file),
            columns=["date", "merchant", "amount"]
        )
        
        # Verify columns
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert "extra" not in rows[0]
        assert "date" in rows[0]
        assert "merchant" in rows[0]
        assert "amount" in rows[0]
    
    def test_write_empty_list(self, tmp_path):
        """Test that writing empty list doesn't create file."""
        csv_file = tmp_path / "output.csv"
        
        write_transactions_csv([], str(csv_file))
        
        # Should not create file for empty list
        assert not csv_file.exists()
    
    def test_write_creates_directory(self, tmp_path):
        """Test that write creates output directory if needed."""
        csv_file = tmp_path / "subdir" / "output.csv"
        
        transactions = [
            {"date": "2023-01-01", "merchant": "Store A", "amount": "100.00"},
        ]
        
        write_transactions_csv(transactions, str(csv_file))
        
        assert csv_file.exists()
        assert csv_file.parent.exists()


class TestRealWorldData:
    """Integration tests with real messy data."""
    
    def test_parse_messy_transactions(self):
        """Test parsing the generated messy_transactions.csv file."""
        if not Path("data/messy_transactions.csv").exists():
            pytest.skip("messy_transactions.csv not found")
        
        transactions = parse_transactions_csv("data/messy_transactions.csv")
        
        # Should have parsed 100 transactions
        assert len(transactions) > 0
        
        # All transactions should have required fields
        for t in transactions:
            assert "date" in t
            assert "merchant" in t
            assert "amount" in t
            assert "row_number" in t
    
    def test_parse_edge_cases(self):
        """Test parsing the edge_cases.csv file."""
        if not Path("data/edge_cases.csv").exists():
            pytest.skip("edge_cases.csv not found")
        
        transactions = parse_transactions_csv("data/edge_cases.csv")
        
        # Should handle edge cases without crashing
        assert len(transactions) > 0
        
        # Check statistics for empty values
        stats = get_parse_statistics(transactions)
        assert stats["total_rows"] > 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])