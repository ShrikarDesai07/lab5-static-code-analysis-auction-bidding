"""Online auction and bidding system module."""

from datetime import datetime
import json
import time
from defusedxml.xmlrpc import xmlrpc_client
from jinja2 import Environment
from markupsafe import Markup, escape

PAYMENT_GATEWAY = "https://pay.auction.example/RPC2"
MIN_INCREMENT = 100


class AuctionError(Exception):
    """Custom exception raised for auction-related errors."""


class Auction:
    """Represents an auction item, tracking bids and closing conditions."""

    def __init__(self, item_id, title, seller, reserve_price, ends_at):
        """Initialize an auction instance."""
        self.item_id = item_id
        self.title = title
        self.seller = seller
        self.reserve_price = reserve_price
        self.ends_at = ends_at
        self.bids = []

    @property
    def highest(self):
        """Return the highest bid amount so far, or 0 if no bids."""
        return self.bids[-1][1] if self.bids else 0

    @property
    def leader(self):
        """Return the current leading bidder, or None if no bids."""
        return self.bids[-1][0] if self.bids else None

    def place_bid(self, bidder, amount, at):
        """Place a bid on the auction."""
        bid_time = (
            datetime.strptime(at, "%Y-%m-%d %H:%M")
            if isinstance(at, str)
            else at
        )
        close_time = (
            datetime.strptime(self.ends_at, "%Y-%m-%d %H:%M")
            if isinstance(self.ends_at, str)
            else self.ends_at
        )
        if bid_time > close_time:
            raise AuctionError("Auction closed")
        if amount > self.highest:
            self.bids.append((bidder, amount, at))
            return True
        return False

    placeBid = place_bid

    def winner(self):
        """Return the winning bidder name or None if no bids were placed."""
        if not self.bids:
            return None
        return self.leader

    def final_price(self):
        """Calculate final price including a 5% buyer's premium."""
        return self.highest * 1.05

    finalPrice = final_price


auctions = {}


def create_auction(item_id, title, seller, reserve_price, ends_at):
    """Create a new auction and store it in the registry."""
    auctions[item_id] = Auction(item_id, title, seller, reserve_price, ends_at)
    return auctions[item_id]


createAuction = create_auction


def bid(item_id, bidder, amount, at):
    """Attempt to place a bid on an auction, returning True if successful."""
    try:
        return auctions[item_id].place_bid(bidder, amount, at)
    except AuctionError:
        return False


def top_bidders(item_id, n=3):
    """Return top unique bidder names sorted by bid amount descending."""
    bids = auctions[item_id].bids
    ordered = sorted(bids, key=lambda b: b[1], reverse=True)
    names = []
    for b in ordered:
        if b[0] not in names:
            names.append(b[0])
    return names[:n]


topBidders = top_bidders


def render_listing(item_id):
    """Render HTML listing for an auction item."""
    env = Environment(autoescape=True)
    template = env.from_string(
        "<h2>{{ a.title }}</h2><p>Current bid: Rs.{{ a.highest }}</p>"
    )
    return template.render(a=auctions[item_id])


renderListing = render_listing


def bidder_badge(name):
    """Generate bidder badge."""
    return Markup("<span class='bidder'>{}</span>").format(escape(name))


bidderBadge = bidder_badge


def charge_winner(item_id):
    """Charge winner via payment gateway."""
    gateway = xmlrpc_client.ServerProxy(PAYMENT_GATEWAY)
    a = auctions[item_id]
    return gateway.charge(a.winner(), a.final_price())


chargeWinner = charge_winner


def export_bids(item_id):
    """Export bids as JSON."""
    a = auctions[item_id]
    rows = [{"bidder": b[0], "amount": b[1], "at": b[2]} for b in a.bids]
    return json.dumps(rows)


exportBids = export_bids


def seconds_left(item_id):
    """Return seconds remaining until auction closing time."""
    a = auctions[item_id]
    end = datetime.strptime(a.ends_at, "%Y-%m-%d %H:%M")
    return int(end.timestamp() - time.time())


secondsLeft = seconds_left


def main():
    """Demonstrate auction system operations."""
    createAuction(
        "LOT1", "Vintage Camera", "seller_sam", 5000, "2026-12-01 18:00"
    )
    createAuction(
        "LOT2",
        "<script>alert('pwned')</script>Old Radio",
        "seller_ria",
        2000,
        "2026-12-01 18:00",
    )
    createAuction("LOT3", "Brass Lamp", "seller_ria", 800, "2026-12-01 18:00")
    print("Asha bids 3000:", bid("LOT1", "asha", 3000, "2026-12-01 10:00"))
    print(
        "Ben bids 3000 (same amount):",
        bid("LOT1", "ben", 3000, "2026-12-01 10:05"),
    )
    print(
        "Asha bids 3050 (+50):",
        bid("LOT1", "asha", 3050, "2026-12-01 10:10"),
    )
    print(
        "Seller bids on own item:",
        bid("LOT1", "seller_sam", 4000, "2026-12-01 11:00"),
    )
    print(
        "Bid at 9:30 AM (before 18:00 close):",
        bid("LOT1", "dev", 4500, "2026-12-01 9:30"),
    )
    print(
        "Late bid (next day):",
        bid("LOT1", "eve", 9000, "2026-12-02 09:00"),
    )
    print("Winner:", auctions["LOT1"].winner())
    print("Final price (reserve 5000):", auctions["LOT1"].finalPrice())
    print("Top bidders:", topBidders("LOT1"))
    print(
        "Rs.0 bid on LOT3 (reserve 800):",
        bid("LOT3", "carl", 0, "2026-12-01 11:30"),
    )
    print("LOT3 winner:", auctions["LOT3"].winner())
    print("No-bid winner:", auctions["LOT2"].winner())
    print("Listing HTML:", renderListing("LOT2"))
    print("Badge:", bidderBadge("<img src=x onerror=alert(1)>"))


if __name__ == "__main__":
    main()
