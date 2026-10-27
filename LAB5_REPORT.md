# Laboratory Report: Static Code Analysis (Lab 5)

---

## 1. Student Details and Repository Information

- **Student Name:** Shrikar Desai
- **SRN:** PES1UG24CS916
- **Department:** Computer Science and Engineering
- **Institution:** PES University
- **Assigned Repository:** [`https://github.com/SETAPESU26/L5_65_auction-bidding`](https://github.com/SETAPESU26/L5_65_auction-bidding)
- **Local Working Directory:** `C:\Users\shrik\se\L5_65_auction-bidding`
- **Assigned Script:** `auction_system.py`

---

## 2. Objective and Overview of Static Code Analysis

### Objective
To enhance Python code quality, security posture, and stylistic consistency by applying industry-standard static analysis tools (**Pylint**, **Bandit**, and **Flake8**) to systematically detect, analyze, and rectify vulnerabilities, design flaws, logic bugs, and formatting violations in the assigned auction bidding application.

### Understanding Static Code Analysis
Static code analysis is the process of examining software source code without executing it. It parses the source text into Abstract Syntax Trees (AST), control-flow graphs, and symbol tables to inspect structural semantics, enforce coding standards (e.g., PEP 8), track variable scopes, and detect common algorithmic antipatterns or security vulnerabilities.

Static analysis offers distinct advantages:
- **Comprehensive Code Coverage:** Scrutinizes all code paths, including obscure error handlers and rarely traversed exception recovery paths that dynamic test suites frequently miss.
- **Early Defect Detection ("Shift-Left"):** Identifies flaws during authoring and pre-commit review cycles before testing or production deployment.
- **Zero Runtime Side Effects:** Operates safely without database connections, mocked payment gateways, or network access.

---

## 3. Static Analysis Tools Used

| Tool | Primary Purpose | Scope & Detection Focus |
|---|---|---|
| **Pylint (v3.3.9)** | Code Quality & Logical Review | Enforces structural conventions, docstring coverage, refactoring suggestions, variable lifecycle management, broad exception detection, and computes an overall code quality score out of 10.0. |
| **Bandit (v1.8.6)** | Security Vulnerability Scanner | Analyzes AST nodes for security risks mapped to Common Weakness Enumerations (CWE), including XSS, injection flaws, unsafe deserialization, insecure XML parsing, and hardcoded credentials. |
| **Flake8 (v7.3.0)** | Style Guide & Syntax Enforcement | Combines `pycodestyle`, `pyflakes`, and `mccabe` to enforce strict PEP 8 formatting rules, line length restrictions (≤ 79 characters), blank-line spacing, and syntax verification. |

---

## 4. Baseline (BEFORE) Findings Summary

Prior to making any modifications to `auction_system.py`, baseline reports were executed and recorded:

- **Pylint Initial Score:** **5.86 / 10**
  - Missing module, class, and function docstrings (`C0114`, `C0115`, `C0116`).
  - Useless `(object)` inheritance in Python 3 (`R0205`).
  - Too many instance attributes: 8/7 (`R0902`).
  - Function/method names violating snake_case naming style (`C0103`).
  - Attribute `leader` defined outside `__init__` (`W0201`).
  - Raising generic `Exception` (`W0719`) and catching broad `Exception` (`W0718`).
  - Unnecessary `else` blocks after `return` and `continue` (`R1705`, `R1724`).
  - Wrong import ordering (`C0411`).
  - Line length exceeding limits (`C0301`).

- **Bandit Initial Findings:** **3 Issues Detected** (2 High Severity, 1 Medium Severity)
  - `B411 (High Severity / High Confidence, CWE-20)`: Use of standard `xmlrpc.client` vulnerable to XML entity expansion and billion laughs attacks.
  - `B701 (High Severity / High Confidence, CWE-94)`: Jinja2 template environment initialized with `autoescape=False`, permitting cross-site scripting (XSS).
  - `B704 (Medium Severity / High Confidence, CWE-79)`: Concatenation of unsanitized `name` variable directly into `markupsafe.Markup`, leading to stored XSS.

- **Flake8 Initial Findings:** **19 PEP 8 Violations**
  - 11 occurrences of `E302`: Expected 2 blank lines before top-level class/functions, found 1.
  - 1 occurrence of `E305`: Expected 2 blank lines after class/function definition, found 1.
  - 7 occurrences of `E501`: Line length exceeding 79 characters.

- **Functional & Domain Defects (Not flagged by static tools):**
  - In `placeBid`, timestamp comparison `if at > self.ends_at:` used plain ASCII string comparison. Morning timestamps with single-digit hours (e.g. `"2026-12-01 9:30"`) evaluated lexicographically greater than `"2026-12-01 18:00"` because character `'9' > '1'`, erroneously rejecting legitimate bids submitted before closing time.
  - `MIN_INCREMENT = 100` was defined at line 9 but never used in `placeBid`. Bids increasing by only 50 or tied amounts (`amount >= self.highest`) were accepted, allowing sub-increment and tied bids to take the lead.

---

## 5. Comprehensive Issue Table

| Issue | Type | Tool & Warning Code | Original Line(s) | Description | Fix Approach | Verification Result |
|---|---|---|---|---|---|---|
| **Insecure XML-RPC Client** | Security (High) | Bandit `B411` (CWE-20) | Line 5 | Standard library `xmlrpc.client` is vulnerable to XML entity expansion attacks (Billion Laughs) and untrusted DTD processing. | Replaced import with `defusedxml.xmlrpc.xmlrpc_client.ServerProxy` to safely parse XML payloads with entity expansion protection. | Bandit reports 0 security issues. Payment proxy executes securely. |
| **Jinja2 Autoescape Disabled (XSS)** | Security (High) | Bandit `B701` (CWE-94) | Line 65 | `Environment(autoescape=False)` allowed raw HTML/JavaScript in auction titles to render unescaped in browsers. | Updated environment initialization to `Environment(autoescape=True)`. | `<script>` tags properly converted to `&lt;script&gt;`. Bandit B701 eliminated. |
| **MarkupSafe Unescaped Concatenation (XSS)** | Security (Medium) | Bandit `B704` (CWE-79) | Line 70 | Direct string concatenation into `Markup("<span class='bidder'>" + name + "</span>")` marked malicious bidder names as trusted HTML. | Used `markupsafe.escape` and format strings: `Markup("<span class='bidder'>{}</span>").format(escape(name))`. | Malicious tags (e.g. `<img onerror=alert(1)>`) properly sanitized to entity references. Bandit B704 eliminated. |
| **Broad Exception Handling & Raising** | Correctness & Reliability | Pylint `W0718` & `W0719` | Lines 23, 50 | Raising generic `Exception("Auction closed")` and catching `except Exception:` blindly caught all unexpected errors, masking syntax/runtime defects. | Declared a domain-specific `AuctionError(Exception)` class. Raised `AuctionError` in `place_bid` and caught specifically `except AuctionError:` in `bid`. | Pylint W0718 and W0719 resolved. Unintended exceptions surface cleanly. |
| **Lexicographical Date Comparison Defect** | Logic & Correctness Bug | Manual Audit / Inspection | Line 22 | Timestamp evaluation `if at > self.ends_at:` performed string comparison instead of date arithmetic, incorrectly rejecting morning bids. | Parsed timestamp strings into `datetime` objects using `datetime.strptime(..., "%Y-%m-%d %H:%M")` before comparison. | 9:30 AM bids before 18:00 close evaluate correctly to `True`. Unit tests pass. |
| **Unenforced Minimum Increment & Tied Bids** | Correctness Bug / Logic Defect | Domain Logic / Manual Audit | Lines 9, 24 | `MIN_INCREMENT = 100` was defined but never referenced in `placeBid`. Bids increasing by only 50 or tied amounts (`amount >= self.highest`) were accepted. | Enforced `amount >= self.highest + MIN_INCREMENT` for subsequent bids and `amount > 0` for initial bids. | Sub-increment bids (+50) and tied bids return `False`. Dedicated unit tests pass. |
| **Dynamic Attribute Defined Outside `__init__`** | Maintainability / Code Quality | Pylint `W0201` & `R0902` | Line 27 | `self.leader` was only set inside `placeBid` upon receiving a bid, leaving the attribute undefined on auctions with zero bids. | Converted `highest` and `leader` into dynamic `@property` getters derived directly from `self.bids`. | Eliminates `W0201`, keeps state synchronized with `self.bids`, and lowers instance attribute count. |
| **PEP 8 Naming and Formatting Violations** | Code Style & Quality | Pylint `C0103`, Flake8 `E501`, `E302`, `E305` | Multiple | Function names in camelCase, missing docstrings, lines > 79 characters, and insufficient blank lines. | Renamed functions to snake_case with backward-compatible aliases, added module/class/function docstrings, and wrapped long lines. | Flake8 reports 0 errors. Pylint score jumps to 9.81/10. |

---

## 6. Before and After Metrics Comparison

### Pylint Score and Findings
- **Baseline Score:** `5.86 / 10`
- **Final Score:** **`9.81 / 10`**
- **Improvement:** **+3.95 points**
- **Findings Comparison:**
  - Resolved: `C0114`, `C0115`, `C0116` (Docstrings added)
  - Resolved: `R0205` (Removed redundant `(object)` inheritance)
  - Resolved: `R0902` (Reduced instance attributes from 8 to 6 via properties)
  - Resolved: `W0201` (Eliminated dynamic attribute outside `__init__`)
  - Resolved: `W0718`, `W0719` (Replaced generic exceptions with `AuctionError`)
  - Resolved: `R1705`, `R1724` (Removed redundant `else` after `return`/`continue`)
  - Resolved: `C0411` (Standardized import ordering: standard lib first, then third party)
  - Resolved: `C0103` (Implemented PEP 8 snake_case methods with legacy aliases)
  - Retained Intentionally: `R0913` / `R0917` (Preserved public constructor signature `Auction(item_id, title, seller, reserve_price, ends_at)` to maintain API compatibility).

### Bandit Security Findings
- **Baseline Issues:** 3 issues (2 High, 1 Medium)
- **Final Issues:** **0 issues (No issues identified)**
- **Severity Breakdown:**
  - High: 2 -> 0
  - Medium: 1 -> 0
  - Low: 0 -> 0

### Flake8 PEP 8 Violations
- **Baseline Violations:** 19 violations (`E302`, `E305`, `E501`)
- **Final Violations:** **0 violations (Completely clean output)**

---

## 7. Domain Rules & Architecture Audit

### 1. Minimum Increment Rule (`MIN_INCREMENT = 100`)
- **Audit Findings:** The constant `MIN_INCREMENT = 100` was present at line 9 of the original codebase, and line 94 of the demo specifically placed a bid with `(+50)`: `bid("LOT1", "asha", 3050, "2026-12-01 10:10")`. In the original code, this sub-increment bid was accepted because `MIN_INCREMENT` was never referenced.
- **Resolution:** Updated `place_bid` so that once an initial bid is established (`highest > 0`), any subsequent bid must satisfy `amount >= self.highest + MIN_INCREMENT`. Consequently, Asha's +50 bid (3050 over 3000) is correctly rejected (`False`).

### 2. Seller Self-Bidding Rule
- **Audit Findings:** Review of `Lab_5_Static_Code_Analysis_Student_handout (1).pdf` and `README.md` confirmed that seller self-bidding is **not prohibited** by the assignment requirements or specifications. In `main()`, the demo explicitly tests `print("Seller bids on own item:", bid("LOT1", "seller_sam", 4000, "2026-12-01 11:00"))`.
- **Engineering Decision:** To avoid inventing unrequested business rules that would alter the program's intended behavior, seller self-bidding remains permitted. A dedicated unit test (`test_seller_self_bidding_behavior`) verifies this behavior.

### 3. Reserve Price Handling
- **Audit Findings:** `README.md` states: *"An Auction class tracks reserve prices and closing times; the program accepts bids, picks the winner and final price (with a buyer's premium)..."*. In both the original code and the demo, bids below the reserve price (e.g. Asha bidding 3000 on LOT1 with a reserve of 5000) are accepted as valid auction bids, and `winner()` returns the highest bidder (`dev`).
- **Engineering Decision:** The reserve price is tracked as an informational property on the `Auction` entity. `winner()` returns the leading bidder (`self.leader`), and `final_price()` computes the 5% buyer's premium on `self.highest`. This preserves the interface contract and aligns with the expected output of `main()`.

---

## 8. Testing and Verification

A comprehensive automated test suite in `test_auction_system.py` was executed using `pytest`. All 12 unit and regression tests passed:

```text
============================= test session starts =============================
platform win32 -- Python 3.9.13, pytest-8.4.2, pluggy-1.6.0
rootdir: C:\Users\shrik\se\L5_65_auction-bidding
collected 12 items

test_auction_system.py::test_auction_initialization PASSED               [  8%]
test_auction_system.py::test_valid_bids_and_winner PASSED                [ 16%]
test_auction_system.py::test_min_increment_enforcement PASSED            [ 25%]
test_auction_system.py::test_seller_self_bidding_behavior PASSED         [ 33%]
test_auction_system.py::test_reserve_price_informational PASSED          [ 41%]
test_auction_system.py::test_time_comparison_edge_cases PASSED           [ 50%]
test_auction_system.py::test_final_price_calculation PASSED              [ 58%]
test_auction_system.py::test_top_bidders_uniqueness_and_limit PASSED     [ 66%]
test_auction_system.py::test_render_listing_xss_protection PASSED        [ 75%]
test_auction_system.py::test_bidder_badge_xss_protection PASSED          [ 83%]
test_auction_system.py::test_export_bids_json PASSED                     [ 91%]
test_auction_system.py::test_seconds_left PASSED                         [100%]

============================= 12 passed in 2.34s ==============================
```

### Manual Built-in Demo Output Verification
Running `python auction_system.py` produces the verified output:
```text
Asha bids 3000: True
Ben bids 3000 (same amount): False
Asha bids 3050 (+50): False
Seller bids on own item: True
Bid at 9:30 AM (before 18:00 close): True
Late bid (next day): False
Winner: dev
Final price (reserve 5000): 4725.0
Top bidders: ['dev', 'seller_sam', 'asha']
Rs.0 bid on LOT3 (reserve 800): False
LOT3 winner: None
No-bid winner: None
Listing HTML: <h2>&lt;script&gt;alert(&#39;pwned&#39;)&lt;/script&gt;Old Radio</h2><p>Current bid: Rs.0</p>
Badge: <span class='bidder'>&lt;img src=x onerror=alert(1)&gt;</span>
```

---

## 9. Answers to Lab Reflection Questions

### Reflection Question 1
**What is static code analysis, and how does it fundamentally differ from dynamic testing?**  
Static code analysis analyzes program source code, syntax trees, and control flow without executing the software. In contrast, dynamic testing runs the compiled program against discrete test cases to observe runtime outputs. Static analysis achieves full structural code path coverage (including rare failure recovery code), pinpoints the exact line number and root cause of antipatterns, and provides instantaneous feedback early in the development lifecycle before code is deployed.

### Reflection Question 2
**How do Pylint, Bandit, and Flake8 complement each other in a continuous integration / development pipeline?**  
Each tool inspects code at a distinct architectural layer:
- **Flake8** provides ultra-fast syntax and PEP 8 style checking, making it ideal for pre-commit git hooks and instant IDE linting.
- **Pylint** performs deep semantic evaluation, catching variable scoping issues, architectural smells, inheritance defects, and calculating an overall maintainability score.
- **Bandit** focuses exclusively on security AST traversal, detecting vulnerabilities such as XSS, injection flaws, and unsafe parsers mapped to Common Weakness Enumerations (CWE).  
Together, they form a multi-tiered quality and security defense in CI/CD pipelines.

### Reflection Question 3
**What is a "false positive" in static analysis, and how should an engineering team handle tool recommendations without blindly suppressing warnings?**  
A false positive occurs when an analysis tool flags an issue that poses no genuine defect or security vulnerability in the specific application context. Blindly suppressing warnings with comments like `# noqa` or `# nosec` creates dangerous blind spots that mask real bugs. Engineering teams should investigate the underlying cause, attempt clean refactoring first, document the architectural justification when a warning is intentionally retained (e.g., maintaining a public constructor API), and tune configuration files centrally to match team standards.

### Reflection Question 4
**What trade-offs did you observe between code readability, security hardening, and execution performance during refactoring?**  
1. **Security vs. Execution Overhead:** Automatic HTML escaping and defensive XML parsing introduce small computational overhead per render/request, but this overhead is necessary to eliminate catastrophic XSS and XML entity denial-of-service vulnerabilities.
2. **Correctness vs. Simplicity:** Parsing date strings with `datetime.strptime` requires more CPU cycles than naive ASCII string comparisons, but it resolves severe temporal logic defects.
3. **Maintainability via Derived State:** Replacing mutable instance variables with `@property` methods introduces function call overhead, but establishes a single source of truth that permanently prevents state desynchronization bugs.

---

## 10. Git Commit History

The three local commits corresponding to the three tool domains remain intact and unaltered:

1. **Commit 1:** `e963852`
   - **Message:** `fix: address Pylint code quality findings`
   - **Summary:** Added module/class/function docstrings, removed `(object)` base class, refactored `highest` and `leader` to `@property`, created `AuctionError` to eliminate `W0718`/`W0719`, fixed date string comparison defect, and implemented snake_case names with backward-compatible aliases.

2. **Commit 2:** `7dd9363`
   - **Message:** `fix: resolve Bandit security findings`
   - **Summary:** Enabled `autoescape=True` in Jinja2 environment (mitigating `B701` / CWE-94), sanitized bidder badge inputs using `markupsafe.escape` (mitigating `B704` / CWE-79), and replaced standard `xmlrpc.client` with `defusedxml.xmlrpc.xmlrpc_client.ServerProxy` (mitigating `B411` / CWE-20).

3. **Commit 3:** `95c610a`
   - **Message:** `style: resolve Flake8 formatting issues`
   - **Summary:** Formatted line lengths to strictly conform to PEP 8 limits (≤ 79 characters), adjusted top-level blank line separations (`E302`, `E305`), and ensured clean Flake8 verification across all files.

*(Note: In accordance with explicit lab safety instructions, no commits have been pushed remotely.)*

---

## 11. Remaining Warnings and Limitations

- **Pylint `R0913 (too-many-arguments)` & `R0917 (too-many-positional-arguments)`:**  
  `Auction.__init__` accepts 5 positional attributes (`item_id`, `title`, `seller`, `reserve_price`, `ends_at`) plus `self`, totaling 6 arguments against Pylint's default threshold of 5. This constructor signature was intentionally preserved to guarantee backward compatibility with existing callers and public interfaces. Pylint's final score of **9.81 / 10** comfortably exceeds the assignment threshold of **9.5 / 10**.
- **Remote Publishing Status:**  
  All changes, test suites, and reports are held strictly on the local `main` branch awaiting final user approval.
