"""Unit and regression tests for the auction system."""

from datetime import datetime, timedelta
from markupsafe import Markup
import pytest
from auction_system import (
    Auction,
    AuctionError,
    MIN_INCREMENT,
    create_auction,
    bid,
    top_bidders,
    render_listing,
    bidder_badge,
    export_bids,
    seconds_left,
)


def test_auction_initialization():
    """Test that an auction initializes with correct attributes."""
    auc = Auction(
        "TEST1", "Painting", "artist_alice", 1000, "2026-12-31 23:59"
    )
    assert auc.item_id == "TEST1"
    assert auc.title == "Painting"
    assert auc.seller == "artist_alice"
    assert auc.reserve_price == 1000
    assert auc.ends_at == "2026-12-31 23:59"
    assert auc.bids == []
    assert auc.highest == 0
    assert auc.leader is None
    assert auc.winner() is None


def test_valid_bids_and_winner():
    """Test that higher bids update the highest bid and leader correctly."""
    auc = Auction("TEST2", "Sculpture", "artist_bob", 500, "2026-12-31 23:59")
    assert auc.place_bid("bidder1", 600, "2026-12-01 10:00") is True
    assert auc.highest == 600
    assert auc.leader == "bidder1"
    assert auc.winner() == "bidder1"

    # Lower or equal bid rejected
    assert auc.place_bid("bidder2", 600, "2026-12-01 10:05") is False
    assert auc.place_bid("bidder3", 500, "2026-12-01 10:10") is False
    assert auc.winner() == "bidder1"

    # Higher bid succeeds (>= 600 + 100)
    assert auc.place_bid("bidder2", 750, "2026-12-01 10:15") is True
    assert auc.highest == 750
    assert auc.leader == "bidder2"
    assert auc.winner() == "bidder2"


def test_min_increment_enforcement():
    """Test that bids below MIN_INCREMENT are rejected."""
    auc = Auction("TEST_INC", "Vase", "seller_s", 1000, "2026-12-31 23:59")
    assert MIN_INCREMENT == 100

    # Initial bid
    assert auc.place_bid("bidder1", 1000, "2026-12-01 10:00") is True

    # Same amount rejected
    assert auc.place_bid("bidder2", 1000, "2026-12-01 10:05") is False

    # +50 increment rejected (< MIN_INCREMENT)
    assert auc.place_bid("bidder3", 1050, "2026-12-01 10:10") is False

    # Exactly +100 increment accepted (== MIN_INCREMENT)
    assert auc.place_bid("bidder4", 1100, "2026-12-01 10:15") is True
    assert auc.highest == 1100

    # Non-positive bids rejected
    assert auc.place_bid("bidder5", 0, "2026-12-01 10:20") is False
    assert auc.place_bid("bidder6", -50, "2026-12-01 10:25") is False


def test_seller_self_bidding_behavior():
    """Test that seller self-bidding is permitted by current rules."""
    auc = Auction("TEST_SELLER", "Rug", "seller_sam", 500, "2026-12-31 23:59")
    assert auc.place_bid("seller_sam", 600, "2026-12-01 10:00") is True
    assert auc.leader == "seller_sam"


def test_reserve_price_informational():
    """Test that reserve price is tracked and bids below reserve succeed."""
    auc = Auction("TEST_RES", "Coin", "seller_c", 5000, "2026-12-31 23:59")
    assert auc.reserve_price == 5000
    assert auc.place_bid("collector", 3000, "2026-12-01 10:00") is True
    assert auc.highest == 3000
    assert auc.winner() == "collector"
    assert auc.final_price() == pytest.approx(3150.0)


def test_time_comparison_edge_cases():
    """Test date comparison including single-digit hour timestamps."""
    auc = Auction("TEST3", "Clock", "seller_tim", 200, "2026-12-01 18:00")

    # Morning bid (9:30) is before 18:00
    assert auc.place_bid("bidder_early", 300, "2026-12-01 9:30") is True

    # Bid after close raises AuctionError
    with pytest.raises(AuctionError, match="Auction closed"):
        auc.place_bid("bidder_late", 500, "2026-12-02 09:00")


def test_final_price_calculation():
    """Test final price computation including 5% buyer's premium."""
    auc = Auction("TEST4", "Book", "seller_dan", 100, "2026-12-31 23:59")
    auc.place_bid("reader", 200, "2026-12-01 12:00")
    assert auc.final_price() == pytest.approx(210.0)


def test_top_bidders_uniqueness_and_limit():
    """Test top bidders ordering, uniqueness, and limit."""
    create_auction("LOT_MULTI", "Vase", "seller_val", 100, "2026-12-31 23:59")
    bid("LOT_MULTI", "alice", 150, "2026-12-01 10:00")
    bid("LOT_MULTI", "bob", 300, "2026-12-01 10:05")
    bid("LOT_MULTI", "alice", 450, "2026-12-01 10:10")
    bid("LOT_MULTI", "charlie", 600, "2026-12-01 10:15")

    top2 = top_bidders("LOT_MULTI", n=2)
    assert top2 == ["charlie", "alice"]

    top3 = top_bidders("LOT_MULTI", n=3)
    assert top3 == ["charlie", "alice", "bob"]


def test_render_listing_xss_protection():
    """Test that render_listing escapes malicious HTML/JS in titles."""
    xss_title = "<script>alert('xss')</script>Antique"
    create_auction("LOT_XSS", xss_title, "seller_x", 100, "2026-12-31 23:59")
    html = render_listing("LOT_XSS")
    assert "<script>" not in html
    assert "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;Antique" in html


def test_bidder_badge_xss_protection():
    """Test that bidder_badge properly escapes malicious bidder names."""
    badge = bidder_badge("<img src=x onerror=alert(1)>")
    assert isinstance(badge, Markup)
    raw_str = str(badge)
    assert "<img" not in raw_str
    assert "&lt;img src=x onerror=alert(1)&gt;" in raw_str


def test_export_bids_json():
    """Test JSON serialization of bids."""
    create_auction("LOT_JSON", "Coin", "seller_c", 50, "2026-12-31 23:59")
    bid("LOT_JSON", "numismatist", 75, "2026-12-01 10:00")
    exported = export_bids("LOT_JSON")
    assert '"bidder": "numismatist"' in exported
    assert '"amount": 75' in exported


def test_seconds_left():
    """Test seconds_left calculation against ends_at time."""
    future = datetime.now() + timedelta(hours=2)
    ends_str = future.strftime("%Y-%m-%d %H:%M")
    create_auction("LOT_SEC", "Watch", "seller_w", 50, ends_str)
    remaining = seconds_left("LOT_SEC")
    assert 7000 < remaining <= 7200
