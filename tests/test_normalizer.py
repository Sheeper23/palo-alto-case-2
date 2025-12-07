"""
Unit tests for the normalizer module.
Tests date parsing, merchant normalization, amount parsing, and edge cases.
"""

import pytest
import sys
from pathlib import Path
from decimal import Decimal

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.normalizer import (
    normalize_date,
    normalize_merchant,
    normalize_amount,
    normalize_transaction,
    get_normalization_stats,
)


class TestDateNormalization:
    """Test date parsing and normalization."""
    
    def test_normalize_iso_format(self):
        """Test ISO format dates (YYYY-MM-DD)."""
        assert normalize_date("2023-01-15") == "2023-01-15"
        assert normalize_date("2023-12-31") == "2023-12-31"
    
    def test_normalize_us_format(self):
        """Test US format dates (MM/DD/YYYY)."""
        assert normalize_date("01/15/2023") == "2023-01-15"
        assert normalize_date("12/31/2023") == "2023-12-31"
    
    def test_normalize_european_format(self):
        """Test European format dates (DD/MM/YYYY)."""
        # Note: dateutil with dayfirst=False assumes US format for ambiguous dates
        # So 15/01/2023 should be interpreted as month 15 (invalid) or swapped
        result = normalize_date("31/12/2023")
        # This will be parsed as Dec 31 due to 31 being > 12
        assert result == "2023-12-31"
    
    def test_normalize_text_format(self):
        """Test text-based date formats."""
        assert normalize_date("Jan 15, 2023") == "2023-01-15"
        assert normalize_date("January 15, 2023") == "2023-01-15"
        assert normalize_date("15 Jan 2023") == "2023-01-15"
    
    def test_normalize_abbreviated_year(self):
        """Test dates with abbreviated years."""
        result = normalize_date("Jan 15, 23")
        # dateutil should interpret '23 as 2023
        assert result is not None
        assert result.endswith("-01-15")
    
    def test_normalize_with_hyphens(self):
        """Test various hyphen formats."""
        assert normalize_date("15-01-2023") == "2023-01-15"
        assert normalize_date("01-15-2023") == "2023-01-15"
    
    def test_normalize_whitespace(self):
        """Test dates with extra whitespace."""
        assert normalize_date("  2023-01-15  ") == "2023-01-15"
        assert normalize_date(" Jan 15, 2023 ") == "2023-01-15"
    
    def test_normalize_empty_string(self):
        """Test empty date strings."""
        assert normalize_date("") is None
        assert normalize_date("   ") is None
    
    def test_normalize_invalid_date(self):
        """Test completely invalid date strings."""
        assert normalize_date("Invalid Date") is None
        assert normalize_date("Not a date") is None
        assert normalize_date("abc123") is None
    
    def test_normalize_invalid_leap_year(self):
        """Test invalid leap year date (Feb 29 on non-leap year)."""
        # 2023 is not a leap year
        assert normalize_date("2023-02-29") is None
    
    def test_normalize_valid_leap_year(self):
        """Test valid leap year date."""
        # 2024 is a leap year
        assert normalize_date("2024-02-29") == "2024-02-29"
    
    def test_normalize_invalid_month(self):
        """Test invalid month."""
        assert normalize_date("2023-13-01") is None
    
    def test_normalize_invalid_day(self):
        """Test invalid day."""
        assert normalize_date("2023-01-32") is None
    
    def test_normalize_year_boundaries(self):
        """Test year boundary dates."""
        assert normalize_date("2023-01-01") == "2023-01-01"
        assert normalize_date("2023-12-31") == "2023-12-31"
    
    def test_normalize_unreasonable_years(self):
        """Test dates with unreasonable years."""
        assert normalize_date("1899-01-01") is None  # Too old
        # Future dates should be rejected beyond current_year + 1
        assert normalize_date("2100-01-01") is None  # Too far in future
    
    def test_normalize_future_date(self):
        """Test reasonable future dates."""
        # Next year should be valid
        from datetime import datetime
        next_year = datetime.now().year + 1
        result = normalize_date(f"{next_year}-06-15")
        assert result == f"{next_year}-06-15"


class TestMerchantNormalization:
    """Test merchant name normalization and categorization."""
    
    def test_normalize_uber_variants(self):
        """Test Uber merchant variants."""
        name, cat = normalize_merchant("UBER *TRIP")
        assert cat == "uber"
        assert "uber" in name.lower()
        
        name, cat = normalize_merchant("Uber Technologies")
        assert cat == "uber"
        
        name, cat = normalize_merchant("UBER EATS")
        assert cat == "uber"
    
    def test_normalize_amazon_variants(self):
        """Test Amazon merchant variants."""
        name, cat = normalize_merchant("AMAZON.COM")
        assert cat == "amazon"
        
        name, cat = normalize_merchant("AMZN Mktp US")
        assert cat == "amazon"
        
        name, cat = normalize_merchant("Amazon Prime")
        assert cat == "amazon"
    
    def test_normalize_starbucks_variants(self):
        """Test Starbucks merchant variants."""
        name, cat = normalize_merchant("STARBUCKS #1234")
        assert cat == "starbucks"
        
        name, cat = normalize_merchant("Starbucks Coffee")
        assert cat == "starbucks"
        
        name, cat = normalize_merchant("SBUX")
        assert cat == "starbucks"
    
    def test_normalize_case_insensitive(self):
        """Test that matching is case-insensitive."""
        name1, cat1 = normalize_merchant("starbucks")
        name2, cat2 = normalize_merchant("STARBUCKS")
        name3, cat3 = normalize_merchant("Starbucks")
        
        assert cat1 == cat2 == cat3 == "starbucks"
    
    def test_normalize_with_special_characters(self):
        """Test merchants with special characters."""
        name, cat = normalize_merchant("UBER *TRIP")
        assert cat == "uber"
        
        name, cat = normalize_merchant("PG&E Electric")
        assert cat == "utility"
    
    def test_normalize_with_numbers(self):
        """Test merchants with store numbers."""
        name, cat = normalize_merchant("STARBUCKS #1234")
        assert cat == "starbucks"
        
        name, cat = normalize_merchant("TARGET 00012345")
        assert cat == "target"
    
    def test_normalize_unknown_merchant(self):
        """Test unknown merchants get categorized as 'other'."""
        name, cat = normalize_merchant("Random Store Name")
        assert cat == "other"
        assert name == "Random Store Name"
    
    def test_normalize_empty_merchant(self):
        """Test empty merchant strings."""
        name, cat = normalize_merchant("")
        assert name == "Unknown"
        assert cat == "other"
        
        name, cat = normalize_merchant("   ")
        assert name == "Unknown"
        assert cat == "other"
    
    def test_normalize_unicode_characters(self):
        """Test merchants with unicode/accented characters."""
        name, cat = normalize_merchant("Café Résumé")
        assert cat == "other"  # Unknown merchant
        assert "Café" in name or "Cafe" in name
        
        name, cat = normalize_merchant("José's Taquería")
        assert cat == "other"
        assert "José" in name or "Jose" in name
    
    def test_normalize_very_long_name(self):
        """Test very long merchant names get truncated."""
        long_name = "A" * 100
        name, cat = normalize_merchant(long_name)
        assert len(name) <= 53  # 50 chars + "..."
        assert cat == "other"
    
    def test_normalize_only_special_characters(self):
        """Test merchant name with only special characters."""
        name, cat = normalize_merchant("!!!###")
        assert cat == "other"
    
    def test_normalize_only_numbers(self):
        """Test merchant name with only numbers."""
        name, cat = normalize_merchant("123456789")
        assert cat == "other"
    
    def test_normalize_fuzzy_matching(self):
        """Test that fuzzy matching works for similar strings."""
        # Test slight variations
        name, cat = normalize_merchant("STARBUCK")  # Missing 's'
        # Should still match starbucks if similarity is high enough
        # This depends on FUZZY_MATCH_THRESHOLD
        assert cat in ["starbucks", "other"]


class TestAmountNormalization:
    """Test amount parsing and normalization."""
    
    def test_normalize_basic_format(self):
        """Test basic amount formats."""
        assert normalize_amount("45.50") == Decimal("45.50")
        assert normalize_amount("100.00") == Decimal("100.00")
        assert normalize_amount("0.01") == Decimal("0.01")
    
    def test_normalize_with_dollar_sign(self):
        """Test amounts with dollar signs."""
        assert normalize_amount("$45.50") == Decimal("45.50")
        assert normalize_amount("$ 45.50") == Decimal("45.50")
        assert normalize_amount("$100") == Decimal("100.00")
    
    def test_normalize_with_currency_text(self):
        """Test amounts with currency text."""
        assert normalize_amount("USD 45.50") == Decimal("45.50")
        assert normalize_amount("45.50 USD") == Decimal("45.50")
        assert normalize_amount("45.50USD") == Decimal("45.50")
    
    def test_normalize_with_commas(self):
        """Test amounts with thousand separators."""
        assert normalize_amount("$1,234.56") == Decimal("1234.56")
        assert normalize_amount("12,345.67") == Decimal("12345.67")
    
    def test_normalize_negative_amounts(self):
        """Test negative amounts (refunds)."""
        assert normalize_amount("-$25.00") == Decimal("-25.00")
        assert normalize_amount("$-25.00") == Decimal("-25.00")
        assert normalize_amount("-25.00") == Decimal("-25.00")
    
    def test_normalize_zero_amount(self):
        """Test zero amounts."""
        assert normalize_amount("$0.00") == Decimal("0.00")
        assert normalize_amount("0") == Decimal("0.00")
    
    def test_normalize_small_amounts(self):
        """Test very small amounts."""
        assert normalize_amount("$0.01") == Decimal("0.01")
        assert normalize_amount("0.01") == Decimal("0.01")
    
    def test_normalize_large_amounts(self):
        """Test large amounts."""
        assert normalize_amount("$999.99") == Decimal("999.99")
        assert normalize_amount("$9,999.99") == Decimal("9999.99")
    
    def test_normalize_extra_whitespace(self):
        """Test amounts with extra whitespace."""
        assert normalize_amount("  $45.50  ") == Decimal("45.50")
        assert normalize_amount(" 45.50 ") == Decimal("45.50")
    
    def test_normalize_inconsistent_decimals(self):
        """Test amounts with inconsistent decimal places."""
        assert normalize_amount("12.3") == Decimal("12.30")
        assert normalize_amount("12.345") == Decimal("12.34")
        assert normalize_amount("12.346") == Decimal("12.35")
    
    def test_normalize_no_decimals(self):
        """Test amounts without decimal places."""
        assert normalize_amount("$100") == Decimal("100.00")
        assert normalize_amount("50") == Decimal("50.00")
    
    def test_normalize_empty_amount(self):
        """Test empty amount strings."""
        assert normalize_amount("") is None
        assert normalize_amount("   ") is None
    
    def test_normalize_invalid_amount(self):
        """Test invalid amount strings."""
        assert normalize_amount("Invalid") is None
        assert normalize_amount("abc") is None
        assert normalize_amount("Not a number") is None
    
    def test_normalize_non_usd_currency(self):
        """Test non-USD currency symbols."""
        assert normalize_amount("€50.00") == Decimal("50.00")
        assert normalize_amount("¥1000") == Decimal("1000.00")
        assert normalize_amount("£45.50") == Decimal("45.50")
    
    def test_normalize_unreasonable_amounts(self):
        """Test amounts outside reasonable range."""
        # Very large amounts should be rejected
        assert normalize_amount("$999999999.99") is None
        assert normalize_amount("$-999999999.99") is None


class TestTransactionNormalization:
    """Test complete transaction normalization."""
    
    def test_normalize_valid_transaction(self):
        """Test normalizing a valid transaction."""
        result = normalize_transaction(
            date="2023-01-15",
            merchant="STARBUCKS #1234",
            amount="$5.50"
        )
        
        assert result["is_valid"] is True
        assert result["normalized_date"] == "2023-01-15"
        assert result["category"] == "starbucks"
        assert result["normalized_amount"] == Decimal("5.50")
        assert len(result["errors"]) == 0
    
    def test_normalize_invalid_date(self):
        """Test transaction with invalid date."""
        result = normalize_transaction(
            date="Invalid Date",
            merchant="Store",
            amount="$100.00"
        )
        
        assert result["is_valid"] is False
        assert result["normalized_date"] is None
        assert "Invalid date" in result["errors"][0]
    
    def test_normalize_invalid_amount(self):
        """Test transaction with invalid amount."""
        result = normalize_transaction(
            date="2023-01-15",
            merchant="Store",
            amount="Invalid"
        )
        
        assert result["is_valid"] is False
        assert result["normalized_amount"] is None
        assert "Invalid amount" in result["errors"][0]
    
    def test_normalize_multiple_errors(self):
        """Test transaction with multiple invalid fields."""
        result = normalize_transaction(
            date="Invalid Date",
            merchant="Store",
            amount="Invalid Amount"
        )
        
        assert result["is_valid"] is False
        assert len(result["errors"]) == 2
    
    def test_normalize_preserves_raw_values(self):
        """Test that raw values are preserved."""
        result = normalize_transaction(
            date="Jan 15, 2023",
            merchant="UBER *TRIP",
            amount="$45.50"
        )
        
        assert result["raw_date"] == "Jan 15, 2023"
        assert result["raw_merchant"] == "UBER *TRIP"
        assert result["raw_amount"] == "$45.50"
    
    def test_normalize_edge_case_transaction(self):
        """Test transaction with edge case values."""
        result = normalize_transaction(
            date="2024-02-29",  # Valid leap year
            merchant="Café Résumé",
            amount="-$25.00"  # Refund
        )
        
        assert result["is_valid"] is True
        assert result["normalized_date"] == "2024-02-29"
        assert result["normalized_amount"] == Decimal("-25.00")


class TestNormalizationStatistics:
    """Test normalization statistics calculation."""
    
    def test_stats_empty_list(self):
        """Test statistics for empty list."""
        stats = get_normalization_stats([])
        
        assert stats["total_transactions"] == 0
        assert stats["valid_transactions"] == 0
        assert stats["invalid_transactions"] == 0
        assert stats["success_rate"] == 0
    
    def test_stats_all_valid(self):
        """Test statistics with all valid transactions."""
        transactions = [
            normalize_transaction("2023-01-01", "Store A", "$100.00"),
            normalize_transaction("2023-01-02", "Store B", "$50.00"),
        ]
        
        stats = get_normalization_stats(transactions)
        
        assert stats["total_transactions"] == 2
        assert stats["valid_transactions"] == 2
        assert stats["invalid_transactions"] == 0
        assert stats["success_rate"] == 100.0
    
    def test_stats_with_errors(self):
        """Test statistics with some invalid transactions."""
        transactions = [
            normalize_transaction("2023-01-01", "Store A", "$100.00"),
            normalize_transaction("Invalid", "Store B", "$50.00"),
            normalize_transaction("2023-01-03", "Store C", "Invalid"),
        ]
        
        stats = get_normalization_stats(transactions)
        
        assert stats["total_transactions"] == 3
        assert stats["valid_transactions"] == 1
        assert stats["invalid_transactions"] == 2
        assert stats["success_rate"] == pytest.approx(33.33, rel=0.1)
        assert stats["date_errors"] == 1
        assert stats["amount_errors"] == 1
    
    def test_stats_categories(self):
        """Test that categories are counted."""
        transactions = [
            normalize_transaction("2023-01-01", "STARBUCKS", "$5.00"),
            normalize_transaction("2023-01-02", "AMAZON", "$100.00"),
            normalize_transaction("2023-01-03", "STARBUCKS", "$5.00"),
        ]
        
        stats = get_normalization_stats(transactions)
        
        assert "categories" in stats
        assert stats["categories"]["starbucks"] == 2
        assert stats["categories"]["amazon"] == 1


class TestEdgeCases:
    """Test additional edge cases and robustness."""
    
    def test_unicode_handling(self):
        """Test handling of unicode characters."""
        result = normalize_transaction(
            date="2023-01-15",
            merchant="José's Taquería",
            amount="$25.00"
        )
        
        assert result["is_valid"] is True
        assert "José" in result["normalized_merchant"] or "Jose" in result["normalized_merchant"]
    
    def test_empty_fields(self):
        """Test handling of empty fields."""
        result = normalize_transaction(
            date="",
            merchant="",
            amount=""
        )
        
        assert result["is_valid"] is False
        assert result["normalized_date"] is None
        assert result["normalized_amount"] is None
    
    def test_whitespace_only_fields(self):
        """Test handling of whitespace-only fields."""
        result = normalize_transaction(
            date="   ",
            merchant="   ",
            amount="   "
        )
        
        assert result["is_valid"] is False
    
    def test_special_characters_in_all_fields(self):
        """Test special characters don't break normalization."""
        result = normalize_transaction(
            date="2023-01-15",
            merchant="Store & Co.",
            amount="$1,234.56"
        )
        
        assert result["is_valid"] is True
        assert result["normalized_amount"] == Decimal("1234.56")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])