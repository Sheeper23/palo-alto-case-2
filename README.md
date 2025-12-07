# Smart Financial Parser

A CLI tool that ingests messy financial transaction data and produces clean, normalized reports.

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run with sample data and default settings
python main.py data/messy_transactions.csv
```

## Additional Options
```bash
# View help settings
python main.py -h

# Re-generate input data
python data/generate_input_data.py

# Run all tests
pytest tests/ -v
```

## Design Decisions
- **Pipeline**:
    - The program follows a pipeline architecture. This allows for a clear separation of concerns and efficient error handling at each step. This approach is also more maintanable and testable than a monolithic design.
    - The pipeline looks like this:
```
CLI Input -> Parser -> Normalizer -> Analyzer -> Report Output
```
- **Project Structure**: The project is split into the following directories:
    - `data`: Stores input data and the script used to generate it
    - `output`: Contains the file outputs from the program.
    - `src`: All logic used for the program except CLI integration.
    - `tests`: Contains all testing scripts.

- The entrypoint to the program is `main.py` stored in the main directory.

## Key Technical Decisions

### Terminal Output Library Choices
- `rich`: Used for clean terminal outputs where necessary. `rich` is popular and allows for robust tables, colors, and formatting without manual ANSI code handling.
- `logging` (standard library): More robust and maintainable than using print statements for logging.

### Test Data Generation

I chose to create synthetic transaction data using `data/generate_test_data.py`. This is because:
1. **Testing Control**: I could intentionally create specific edge cases that I thought of
2. **No External Dependencies**: No licensing or copyright concerns

The generator produces:
- `messy_transactions.csv`: 100 transactions with 10% edge cases for general testing
- `edge_cases.csv`: 30 transactions with 50% edge cases for stress testing

Edge cases include invalid leap years, unicode characters, empty fields, extreme values, and inconsistent formatting.

### Date Normalization
- **Library**: `python-dateutil`
- **Reasoning**: Handles 100+ date formats. Custom date
  parsers are prone to errors given how complex date analysis can get.
- **Additional Validation**: I added a reasonable year range check (1900-current year + 1)

### Merchant Normalization  
- **Library**: `rapidfuzz`
- **Reasoning**: Simple string matching fails on inputs like "UBER *TRIP" vs "Uber Eats", so fuzzy matching is necessary. Fuzzy matching with a 85% similarity threshold catches these variants. Creating a custom fuzzy matcher would be tedious and unnecessary given popular options.
- **Rejected Alternatives**: Regular expressions for merchants are hard to maintain and struggle with scaling, since new name variants must be accounted for manually.

### Amount Parsing
- **Library**: `decimal.Decimal` (standard library)
- **Reasoning**: Financial calculations require exact precision. Using float can cause floating point errors.
- **Symbol Stripping**: I used custom regular expression patterns to strip currency symbols while preserving negatives.

### CSV Parsing
- **Library**: Python's built-in `csv` module (via `DictReader`)
- **Reasoning**: A custom parser provides better error messages and row-by-row control compared to popular libraries like `pandas`. We can also skip malformed rows and continue processing instead of failing on the first error.
- **Validation**: Checks file existence, encoding (UTF-8), and required columns (date, merchant, amount) before parsing.
- **Robustness**: Skips empty rows, normalizes column names, and tracks row numbers for debugging, all while handling errors gracefully.

### Analysis & Reporting
- **Features**:
  - Spending breakdown by category with percentages
  - Top merchants analysis
  - Comprehensive statistics (average, min, max)
- **Dual Output**: Both `rich` console display and an option for plain text file export for flexibility.

### CLI Interface & Pipeline Orchestration
- **Library**: `argparse` (standard library)
- **Reasoning**: argparse provides robust CLI parsing with automatic help generation and validation.
- **Design Pattern**: Pipeline architecture (parse -> normalize -> analyze) with graceful error handling and logging. If normalization fails on some rows, we continue processing valid ones rather than crashing.
- **Error Handling**: 
  - Validates input file existence before processing
  - Shows detailed error statistics
  - Verbose mode for debugging without cluttering default output
- **Additional Output Choices**: The user can also choose to output the cleaned and normalized CSV data to a file for use elsewhere.

## Testing

Includes a comprehensive test suite using `pytest` to validate parser, normalizer, and analyzer modules:

- `test_parser.py`: CSV parsing, validation, error handling, edge cases
- `test_normalizer.py`: Date parsing, merchant categorization, amount normalization with fuzzy matching
- `test_analyzer.py`: Spending analysis, statistics calculation, report generation

All tests pass.

**Key Test Coverage:**
- Edge cases include invalid dates (2023-02-29), unicode characters (Café Résumé), and extreme values
- Tests error handling of empty files, missing columns, and malformed data

**Run Tests:**
```bash
# Run all tests
pytest tests/ -v
```

## Methodology and AI Usage

**ChatGPT** was consulted for:
- Generating merchants, their categories, and merchant name variants. I manually added a few more that I thought were necessary.
- Generating regular expressions for parsing out symbols in transaction amounts. I manually tested the expression against examples and found a bug with negatives, which I then fixed.
- Generating initial tests. After validating those tests, I added additional tests for specific important cases that were not covered.