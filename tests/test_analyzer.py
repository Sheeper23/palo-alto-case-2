"""
Unit tests for the analyzer module.
Tests spending analysis, statistics calculation, and report generation.
"""

import pytest
import sys
from pathlib import Path
from decimal import Decimal

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzer import (
    SpendingAnalyzer,
    analyze_transactions
)


class TestSpendingAnalyzer:
    """Test the SpendingAnalyzer class."""
    
    @pytest.fixture
    def sample_transactions(self):
        """Create sample normalized transactions for testing."""
        return [
            {
                "normalized_date": "2023-01-01",
                "normalized_merchant": "Starbucks",
                "category": "starbucks",
                "normalized_amount": Decimal("5.50"),
                "is_valid": True
            },
            {
                "normalized_date": "2023-01-02",
                "normalized_merchant": "Amazon",
                "category": "amazon",
                "normalized_amount": Decimal("100.00"),
                "is_valid": True
            },
            {
                "normalized_date": "2023-01-03",
                "normalized_merchant": "Starbucks",
                "category": "starbucks",
                "normalized_amount": Decimal("6.00"),
                "is_valid": True
            },
            {
                "normalized_date": "2023-01-04",
                "normalized_merchant": "Uber",
                "category": "uber",
                "normalized_amount": Decimal("25.00"),
                "is_valid": True
            },
        ]
    
    @pytest.fixture
    def transactions_with_invalid(self):
        """Create transactions with some invalid entries."""
        return [
            {
                "normalized_date": "2023-01-01",
                "normalized_merchant": "Starbucks",
                "category": "starbucks",
                "normalized_amount": Decimal("5.50"),
                "is_valid": True
            },
            {
                "normalized_date": None,
                "normalized_merchant": "Unknown",
                "category": "other",
                "normalized_amount": None,
                "is_valid": False
            },
            {
                "normalized_date": "2023-01-02",
                "normalized_merchant": "Amazon",
                "category": "amazon",
                "normalized_amount": Decimal("100.00"),
                "is_valid": True
            },
        ]
    
    def test_analyzer_initialization(self, sample_transactions):
        """Test analyzer initialization."""
        analyzer = SpendingAnalyzer(sample_transactions)
        
        assert len(analyzer.transactions) == 4
        assert len(analyzer.valid_transactions) == 4
        assert len(analyzer.invalid_transactions) == 0
    
    def test_analyzer_separates_valid_invalid(self, transactions_with_invalid):
        """Test that analyzer separates valid and invalid transactions."""
        analyzer = SpendingAnalyzer(transactions_with_invalid)
        
        assert len(analyzer.transactions) == 3
        assert len(analyzer.valid_transactions) == 2
        assert len(analyzer.invalid_transactions) == 1


class TestTotalSpending:
    """Test total spending calculation."""
    
    def test_total_spending_basic(self):
        """Test basic total spending calculation."""
        transactions = [
            {"normalized_amount": Decimal("10.00"), "is_valid": True},
            {"normalized_amount": Decimal("20.00"), "is_valid": True},
            {"normalized_amount": Decimal("30.00"), "is_valid": True},
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        total = analyzer.get_total_spending()
        
        assert total == Decimal("60.00")
    
    def test_total_spending_ignores_invalid(self):
        """Test that invalid transactions are excluded from total."""
        transactions = [
            {"normalized_amount": Decimal("10.00"), "is_valid": True},
            {"normalized_amount": Decimal("20.00"), "is_valid": False},
            {"normalized_amount": Decimal("30.00"), "is_valid": True},
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        total = analyzer.get_total_spending()
        
        assert total == Decimal("40.00")
    
    def test_total_spending_empty_list(self):
        """Test total spending with empty transaction list."""
        analyzer = SpendingAnalyzer([])
        total = analyzer.get_total_spending()
        
        assert total == Decimal("0")
    
    def test_total_spending_with_negatives(self):
        """Test total spending with negative amounts (refunds)."""
        transactions = [
            {"normalized_amount": Decimal("100.00"), "is_valid": True},
            {"normalized_amount": Decimal("-25.00"), "is_valid": True},
            {"normalized_amount": Decimal("50.00"), "is_valid": True},
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        total = analyzer.get_total_spending()
        
        assert total == Decimal("125.00")
    
    def test_total_spending_handles_none_amounts(self):
        """Test that None amounts are skipped gracefully."""
        transactions = [
            {"normalized_amount": Decimal("10.00"), "is_valid": True},
            {"normalized_amount": None, "is_valid": True},
            {"normalized_amount": Decimal("20.00"), "is_valid": True},
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        total = analyzer.get_total_spending()
        
        assert total == Decimal("30.00")


class TestCategoryAnalysis:
    """Test spending by category analysis."""
    
    def test_spending_by_category(self):
        """Test category spending aggregation."""
        transactions = [
            {"category": "starbucks", "normalized_amount": Decimal("5.00"), "is_valid": True},
            {"category": "starbucks", "normalized_amount": Decimal("6.00"), "is_valid": True},
            {"category": "amazon", "normalized_amount": Decimal("100.00"), "is_valid": True},
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        by_category = analyzer.get_spending_by_category()
        
        assert by_category["starbucks"] == Decimal("11.00")
        assert by_category["amazon"] == Decimal("100.00")
    
    def test_top_categories(self):
        """Test getting top spending categories."""
        transactions = [
            {"category": "amazon", "normalized_amount": Decimal("100.00"), "is_valid": True},
            {"category": "starbucks", "normalized_amount": Decimal("50.00"), "is_valid": True},
            {"category": "uber", "normalized_amount": Decimal("25.00"), "is_valid": True},
            {"category": "target", "normalized_amount": Decimal("75.00"), "is_valid": True},
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        top = analyzer.get_top_categories(n=3)
        
        assert len(top) == 3
        # Should be sorted by amount descending
        assert top[0][0] == "amazon"
        assert top[0][1] == Decimal("100.00")
        assert top[1][0] == "target"
        assert top[2][0] == "starbucks"
    
    def test_top_categories_includes_counts(self):
        """Test that top categories include transaction counts."""
        transactions = [
            {"category": "starbucks", "normalized_amount": Decimal("5.00"), "is_valid": True},
            {"category": "starbucks", "normalized_amount": Decimal("5.00"), "is_valid": True},
            {"category": "amazon", "normalized_amount": Decimal("100.00"), "is_valid": True},
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        top = analyzer.get_top_categories(n=2)
        
        # Amazon should be first (highest amount)
        assert top[0][0] == "amazon"
        assert top[0][2] == 1  # 1 transaction
        
        # Starbucks should be second
        assert top[1][0] == "starbucks"
        assert top[1][2] == 2  # 2 transactions
    
    def test_top_categories_limits_results(self):
        """Test that top categories respects the limit."""
        transactions = [
            {"category": f"cat{i}", "normalized_amount": Decimal("10.00"), "is_valid": True}
            for i in range(10)
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        top = analyzer.get_top_categories(n=5)
        
        assert len(top) == 5


class TestMerchantAnalysis:
    """Test merchant spending analysis."""
    
    def test_top_merchants(self):
        """Test getting top merchants by spending."""
        transactions = [
            {"normalized_merchant": "Amazon", "normalized_amount": Decimal("100.00"), "is_valid": True},
            {"normalized_merchant": "Starbucks", "normalized_amount": Decimal("50.00"), "is_valid": True},
            {"normalized_merchant": "Uber", "normalized_amount": Decimal("75.00"), "is_valid": True},
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        top = analyzer.get_top_merchants(n=2)
        
        assert len(top) == 2
        assert top[0][0] == "Amazon"
        assert top[0][1] == Decimal("100.00")
        assert top[1][0] == "Uber"
    
    def test_top_merchants_aggregates_same_merchant(self):
        """Test that same merchant transactions are aggregated."""
        transactions = [
            {"normalized_merchant": "Starbucks", "normalized_amount": Decimal("5.00"), "is_valid": True},
            {"normalized_merchant": "Starbucks", "normalized_amount": Decimal("6.00"), "is_valid": True},
            {"normalized_merchant": "Amazon", "normalized_amount": Decimal("100.00"), "is_valid": True},
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        top = analyzer.get_top_merchants(n=2)
        
        # Amazon should be first
        assert top[0][0] == "Amazon"
        assert top[0][1] == Decimal("100.00")
        assert top[0][2] == 1
        
        # Starbucks should be second with aggregated amount
        assert top[1][0] == "Starbucks"
        assert top[1][1] == Decimal("11.00")
        assert top[1][2] == 2
    
    def test_top_merchants_handles_unknown(self):
        """Test handling of unknown merchants."""
        transactions = [
            {"normalized_merchant": "Unknown", "normalized_amount": Decimal("10.00"), "is_valid": True},
            {"normalized_amount": Decimal("20.00"), "is_valid": True},  # Missing merchant key
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        top = analyzer.get_top_merchants(n=2)
        
        assert len(top) == 1
        assert top[0][0] == "Unknown"
        assert top[0][1] == Decimal("30.00")


class TestStatistics:
    """Test comprehensive statistics calculation."""
    
    def test_statistics_basic(self):
        """Test basic statistics calculation."""
        transactions = [
            {"normalized_amount": Decimal("10.00"), "normalized_merchant": "A", "category": "cat1", "is_valid": True},
            {"normalized_amount": Decimal("20.00"), "normalized_merchant": "B", "category": "cat1", "is_valid": True},
            {"normalized_amount": Decimal("30.00"), "normalized_merchant": "C", "category": "cat2", "is_valid": True},
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        stats = analyzer.get_statistics()
        
        assert stats["total_transactions"] == 3
        assert stats["valid_transactions"] == 3
        assert stats["invalid_transactions"] == 0
        assert stats["total_spending"] == Decimal("60.00")
        assert stats["average_transaction"] == Decimal("20.00")
        assert stats["largest_transaction"] == Decimal("30.00")
        assert stats["smallest_transaction"] == Decimal("10.00")
        assert stats["unique_merchants"] == 3
        assert stats["unique_categories"] == 2
    
    def test_statistics_with_invalid_transactions(self):
        """Test statistics with invalid transactions."""
        transactions = [
            {"normalized_amount": Decimal("10.00"), "normalized_merchant": "A", "category": "cat1", "is_valid": True},
            {"normalized_amount": None, "normalized_merchant": "B", "category": "cat1", "is_valid": False},
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        stats = analyzer.get_statistics()
        
        assert stats["total_transactions"] == 2
        assert stats["valid_transactions"] == 1
        assert stats["invalid_transactions"] == 1
        assert stats["total_spending"] == Decimal("10.00")
    
    def test_statistics_empty_transactions(self):
        """Test statistics with no transactions."""
        analyzer = SpendingAnalyzer([])
        stats = analyzer.get_statistics()
        
        assert stats["total_transactions"] == 0
        assert stats["valid_transactions"] == 0
        assert stats["invalid_transactions"] == 0
        assert stats["total_spending"] == Decimal("0")
        assert stats["average_transaction"] == Decimal("0")
        assert stats["largest_transaction"] == Decimal("0")
        assert stats["smallest_transaction"] == Decimal("0")
    
    def test_statistics_with_negative_amounts(self):
        """Test statistics handles negative amounts (refunds)."""
        transactions = [
            {"normalized_amount": Decimal("100.00"), "normalized_merchant": "A", "category": "cat1", "is_valid": True},
            {"normalized_amount": Decimal("-25.00"), "normalized_merchant": "B", "category": "cat2", "is_valid": True},
            {"normalized_amount": Decimal("50.00"), "normalized_merchant": "C", "category": "cat1", "is_valid": True},
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        stats = analyzer.get_statistics()
        
        assert stats["total_spending"] == Decimal("125.00")
        assert stats["smallest_transaction"] == Decimal("-25.00")
        assert stats["largest_transaction"] == Decimal("100.00")


class TestReportGeneration:
    """Test report generation."""
    
    def test_generate_text_report(self):
        """Test generating plain text report."""
        transactions = [
            {
                "normalized_date": "2023-01-01",
                "normalized_merchant": "Starbucks",
                "category": "starbucks",
                "normalized_amount": Decimal("5.50"),
                "is_valid": True
            },
            {
                "normalized_date": "2023-01-02",
                "normalized_merchant": "Amazon",
                "category": "amazon",
                "normalized_amount": Decimal("100.00"),
                "is_valid": True
            },
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        report = analyzer.generate_text_report()
        
        # Check that report contains expected sections
        assert "FINANCIAL TRANSACTION ANALYSIS REPORT" in report
        assert "OVERVIEW" in report
        assert "TOP SPENDING CATEGORIES" in report
        assert "TOP MERCHANTS" in report
        
        # Check that it contains data
        assert "Total Transactions" in report
        assert "$105.50" in report  # Total spending
    
    def test_text_report_empty_transactions(self):
        """Test text report with no transactions."""
        analyzer = SpendingAnalyzer([])
        report = analyzer.generate_text_report()
        
        assert "FINANCIAL TRANSACTION ANALYSIS REPORT" in report
        assert "$0.00" in report


class TestAnalyzeTransactionsFunction:
    """Test the analyze_transactions function."""
    
    def test_analyze_transactions_returns_analyzer(self):
        """Test that analyze_transactions returns an analyzer."""
        transactions = [
            {"normalized_amount": Decimal("10.00"), "normalized_merchant": "A", "category": "cat1", "is_valid": True},
        ]
        
        analyzer = analyze_transactions(transactions)
        
        assert isinstance(analyzer, SpendingAnalyzer)
        assert len(analyzer.transactions) == 1
    
    def test_analyze_transactions_saves_report(self, tmp_path):
        """Test that analyze_transactions can save report to file."""
        transactions = [
            {"normalized_amount": Decimal("10.00"), "normalized_merchant": "A", "category": "cat1", "is_valid": True},
        ]
        
        output_file = tmp_path / "report.txt"
        analyzer = analyze_transactions(transactions, output_file=str(output_file))
        
        assert output_file.exists()
        
        # Verify file contents
        with open(output_file, 'r') as f:
            content = f.read()
        
        assert "FINANCIAL TRANSACTION ANALYSIS REPORT" in content
        assert "Total Transactions" in content


class TestEdgeCases:
    """Test edge cases and robustness."""
    
    def test_all_transactions_invalid(self):
        """Test analyzer with all invalid transactions."""
        transactions = [
            {"normalized_amount": None, "is_valid": False},
            {"normalized_amount": None, "is_valid": False},
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        stats = analyzer.get_statistics()
        
        assert stats["valid_transactions"] == 0
        assert stats["invalid_transactions"] == 2
        assert stats["total_spending"] == Decimal("0")
    
    def test_missing_keys_handled_gracefully(self):
        """Test that missing dictionary keys don't break analyzer."""
        transactions = [
            {"normalized_amount": Decimal("10.00"), "is_valid": True},
            # Missing category and merchant keys
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        
        # Should not crash
        stats = analyzer.get_statistics()
        by_category = analyzer.get_spending_by_category()
        top_merchants = analyzer.get_top_merchants(n=1)
        
        assert stats["total_spending"] == Decimal("10.00")
    
    def test_decimal_precision_maintained(self):
        """Test that decimal precision is maintained throughout."""
        transactions = [
            {"normalized_amount": Decimal("0.01"), "is_valid": True},
            {"normalized_amount": Decimal("0.02"), "is_valid": True},
        ]
        
        analyzer = SpendingAnalyzer(transactions)
        total = analyzer.get_total_spending()
        
        assert total == Decimal("0.03")
        assert isinstance(total, Decimal)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])