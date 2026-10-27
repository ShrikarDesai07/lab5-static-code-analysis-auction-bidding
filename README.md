# Lab 5 — Static Code Analysis

**Student:** Shrikar Desai<br>
**SRN:** PES1UG24CS916<br>
**Course:** Software Engineering Lab (Lab 5)<br>
**Assigned Repository:** [`https://github.com/SETAPESU26/L5_65_auction-bidding`](https://github.com/SETAPESU26/L5_65_auction-bidding)<br>
**Personal Repository:** [https://github.com/ShrikarDesai07/lab5-static-code-analysis-auction-bidding](https://github.com/ShrikarDesai07/lab5-static-code-analysis-auction-bidding)

---

## Overview

In this lab, I worked on an online auction bidding program (`auction_system.py`). The program manages items with reserve prices and closing times, processes bids, calculates final prices with a 5% buyer's premium, identifies winning bidders, and renders HTML listings and bidder badges.

The objective was to run static code analysis tools on the initial codebase, identify security, maintainability, style, and correctness issues, refactor the code to resolve the findings, and verify that the program behaves properly.

## What I Implemented

1. **Security Hardening (Bandit):**
   - **XSS Prevention in Jinja2:** Enabled `autoescape=True` in `render_listing()` so untrusted HTML in auction titles is properly escaped instead of executing scripts.
   - **XSS Prevention in MarkupSafe:** Used `markupsafe.escape()` in `bidder_badge()` to sanitize bidder names before creating `Markup` objects.
   - **XML-RPC Protection:** Replaced standard `xmlrpc.client` with `defusedxml.xmlrpc.xmlrpc_client.ServerProxy` in `charge_winner()` to protect against XML entity expansion (Billion Laughs) attacks.

2. **Code Quality and Maintainability (Pylint):**
   - **Exception Handling:** Replaced generic `Exception` usage with a dedicated `AuctionError` class, eliminating broad exception catching and raising.
   - **Dynamic Properties:** Replaced imperative updates of `highest` and `leader` with `@property` methods derived from `self.bids`, ensuring consistent state and resolving undefined attribute warnings.
   - **Documentation & Standards:** Added module, class, and method docstrings, removed redundant Python 2 `(object)` inheritance, and ordered imports according to PEP 8.
   - **Naming & Compatibility:** Renamed methods and functions to standard `snake_case` while retaining `camelCase` aliases to keep existing interfaces working.

3. **Logic and Correctness Fixes:**
   - **Timestamp Parsing:** Fixed a bug where timestamps were compared as strings (`at > self.ends_at`), which caused morning bids such as `"2026-12-01 9:30"` to be incorrectly rejected before an `"18:00"` close. I parsed both values using `datetime.strptime()` for reliable temporal comparisons.
   - **Minimum Increment Enforcement:** Hooked up the previously unused `MIN_INCREMENT = 100` constant so subsequent bids must exceed the highest bid by at least 100, rejecting tied bids and sub-increment bids (such as +50).

4. **Automated Testing:**
   - Wrote a 12-test suite in `test_auction_system.py` covering auction lifecycle events, increment rules, seller bids, timestamp edge cases, and XSS sanitization.

## Tools Used

- **Pylint:** Checks code quality, variable lifecycle, docstring completeness, and overall structural design.
- **Bandit:** Scans the Python Abstract Syntax Tree (AST) for common security vulnerabilities (CWE mappings).
- **Flake8:** Enforces PEP 8 style guidelines, line length limits (≤ 79 characters), and syntax rules.
- **pytest:** Runs unit and regression tests against the refactored implementation.

## Setup

Run these commands in Windows PowerShell to set up the virtual environment:

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install project dependencies
python -m pip install -r requirements.txt
```

## Running the Program

To run the built-in auction demonstration script:

```powershell
python auction_system.py
```

## Running Tests and Analysis

Run the test suite and static analysis tools:

```powershell
# Run the automated test suite
pytest -v

# Run static analysis tools
python -m pylint auction_system.py
python -m bandit -r auction_system.py
python -m flake8 auction_system.py test_auction_system.py
```

## Results

The verified results on the final codebase match the reports:

| Tool / Check | Baseline (Before) | Final (After) | Target | Status |
|---|---|---|---|---|
| **Pylint** | 5.86 / 10 | **9.81 / 10** | > 9.5 / 10 | Passed |
| **Bandit** | 3 issues (2 High, 1 Med) | **0 issues** | 0 issues | Passed |
| **Flake8** | 19 violations | **0 violations** | 0 violations | Passed |
| **pytest** | 0 tests | **12 passed** | All pass | Passed |

## Files and Reports

- `auction_system.py`: The refactored and hardened auction program.
- `test_auction_system.py`: The unit and regression test suite.
- `issues.md`: The required table documenting identified issues, severity, line numbers, descriptions, and fixes.
- `reflection.md`: My answers to the four lab reflection questions regarding static analysis concepts, CI/CD, false positives, and trade-offs.
- `LAB5_REPORT.md`: My comprehensive lab report containing student details, metrics, issue analysis, and commit history.
- `reports/before/`: Preserved baseline reports before making changes (`pylint_report.txt`, `bandit_report.txt`, `flake8_report.txt`).
- `reports/after/`: Final static analysis reports reflecting the current source code.
