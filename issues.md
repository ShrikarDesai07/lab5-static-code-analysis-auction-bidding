# Static Code Analysis — Issues Identified and Resolved

**Student Name:** Shrikar Desai  
**SRN:** PES1UG24CS916  
**Repository:** `https://github.com/SETAPESU26/L5_65_auction-bidding`  
**File Analyzed:** `auction_system.py`

---

## Issue Table

| Issue | Type | Line(s) | Description | Fix Approach |
|---|---|---|---|---|
| **Insecure XML-RPC Client** | Security (High) | 5 | Standard library `xmlrpc.client` parses untrusted XML without entity expansion limits, vulnerable to XML entity attacks (Billion Laughs / CWE-20, Bandit B411). | Replaced `xmlrpc.client` with `defusedxml.xmlrpc.xmlrpc_client.ServerProxy` to securely parse XML payloads with safe entity expansion controls. |
| **Jinja2 Template Injection / XSS** | Security (High) | 65 | `Environment(autoescape=False)` disables automatic HTML escaping in Jinja2 templates, allowing unsanitized auction titles (e.g. `<script>alert('pwned')</script>`) to execute arbitrary script in the client browser (CWE-94, Bandit B701). | Enabled `autoescape=True` in `Environment(autoescape=True)` so all dynamic fields are sanitized with HTML entity encoding. |
| **Unsanitized Bidder Badge / Stored XSS** | Security (Medium) | 70 | Direct string concatenation `Markup("<span class='bidder'>" + name + "</span>")` marks untrusted input as safe HTML without escaping, permitting script injection via bidder names (CWE-79, Bandit B704). | Sanitized input using `markupsafe.escape(name)` and format strings: `Markup("<span class='bidder'>{}</span>").format(escape(name))`. |
| **Overly Broad Exception Handling** | Code Quality / Bug | 23, 50 | In `placeBid`, generic `Exception("Auction closed")` was raised (Pylint W0719), and in `bid`, `except Exception:` caught all exceptions indiscriminately (Pylint W0718), masking unexpected programming errors. | Created a domain-specific `AuctionError(Exception)` class. Raised `AuctionError` in `place_bid` and caught only `except AuctionError:` in `bid`. |
| **Lexicographical Date String Comparison Defect** | Correctness Bug | 22 | Timestamp comparison `if at > self.ends_at:` used plain ASCII string comparison. Morning timestamps with single-digit hours (e.g. `"9:30"`) evaluated lexicographically greater than `"18:00"`, erroneously rejecting valid bids before closing. | Converted timestamp strings to `datetime` objects using `datetime.strptime(..., "%Y-%m-%d %H:%M")` before executing temporal comparisons. |
| **Unenforced Minimum Increment & Tied Bids** | Correctness Bug / Logic Defect | 9, 24 | `MIN_INCREMENT = 100` was defined but never used in `placeBid`. Bids increasing by only 50 or tied amounts (`amount >= self.highest`) were erroneously accepted, allowing out-of-order and sub-increment bids to lead. | Enforced `amount >= self.highest + MIN_INCREMENT` for subsequent bids and `amount > 0` for initial bids. Tied and sub-increment bids (e.g. +50) are correctly rejected. |
| **Instance Attribute Defined Outside `__init__`** | Maintainability / Bug | 27 | `self.leader` was dynamically instantiated only inside `placeBid` upon receiving a valid bid, leaving the attribute nonexistent on auctions with zero bids (Pylint W0201). | Refactored `highest` and `leader` into dynamic `@property` getters derived directly from `self.bids`, ensuring consistent state and removing redundant instance attributes. |
| **PEP 8 Style and Naming Violations** | Code Style | 11, 21, 37, 43, 53, 64, 69, 72, 83, 90 | Module, class, and functions lacked docstrings (C0114, C0115, C0116). Function names used camelCase rather than snake_case (C0103). Multiple lines exceeded 79 characters (E501). | Implemented snake_case function names with camelCase aliases for backward compatibility, added docstrings to all definitions, and wrapped long lines to conform to PEP 8 standards. |
