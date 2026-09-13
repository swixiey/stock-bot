#!/usr/bin/env python3
"""
Checks a single Shopify product variant's stock status and sends an
ntfy.sh push notification the moment it transitions from out-of-stock
to in-stock. Meant to be run on a schedule (see .github/workflows/check_stock.yml).

Configured below for:
    Windsor Store - "Turn Up The Tease Ruffle Halter Mini Dress"
    Colorway: RED, Size: S
    Variant ID: 42978350759987
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import requests

# ---- Configuration --------------------------------------------------------

PRODUCT_JSON_URL = (
    "https://www.windsorstore.com/products/"
    "turn-up-the-tease-ruffle-halter-mini-dress-05103000064060.js"
)
PRODUCT_PAGE_URL = (
    "https://www.windsorstore.com/products/"
    "turn-up-the-tease-ruffle-halter-mini-dress-05103000064060"
    "?variant=42978350759987"
)
VARIANT_ID = 42978350891059  # RED / S
VARIANT_LABEL = "Red, Size Small"

# ntfy.sh topic to publish to. Anyone who knows the topic name can read
# your notifications, so pick something long and unguessable rather than
# "dress-alert". Set it via the NTFY_TOPIC environment variable / GitHub
# Actions secret -- do not hardcode your real topic here if this repo is public.
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")

STATE_FILE = Path(__file__).parent / "state.json"

# ---- Logic -----------------------------------------------------------------


def fetch_variant_availability() -> Optional[bool]:
    """Return True/False if stock status was determined, None if the check failed."""
    try:
        resp = requests.get(
            PRODUCT_JSON_URL,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0 (compatible; StockWatcher/1.0)"},
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001 - we want to log and continue either way
        print(f"Fetch/parse failed: {exc}", file=sys.stderr)
        return None

    for variant in data.get("variants", []):
        if variant.get("id") == VARIANT_ID:
            return bool(variant.get("available"))

    print(f"Variant {VARIANT_ID} not found in product JSON", file=sys.stderr)
    return None


def load_last_state() -> bool:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text()).get("in_stock", False)
        except Exception:
            return False
    return False


def save_state(in_stock: bool) -> None:
    STATE_FILE.write_text(json.dumps({"in_stock": in_stock}))


def notify() -> None:
    if not NTFY_TOPIC:
        print("NTFY_TOPIC is not set -- skipping notification.", file=sys.stderr)
        return
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=f"{VARIANT_LABEL} is back in stock! {PRODUCT_PAGE_URL}".encode("utf-8"),
            headers={
                "Title": "Windsor dress back in stock!",
                "Priority": "high",
                "Tags": "shopping,tada",
                "Click": PRODUCT_PAGE_URL,
            },
            timeout=15,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"ntfy notification failed: {exc}", file=sys.stderr)


def main() -> None:
    available = fetch_variant_availability()
    if available is None:
        # Inconclusive check (site down, layout changed, etc.) -- don't touch
        # saved state, just log it so the workflow run shows what happened.
        print("Could not determine stock status this run.")
        return

    was_in_stock = load_last_state()
    print(f"{VARIANT_LABEL}: available={available} (was {was_in_stock})")

    if available and not was_in_stock:
        print("Transitioned to IN STOCK -- sending notification.")
        notify()
    elif not available and was_in_stock:
        print("Transitioned back to out of stock.")

    save_state(available)


if __name__ == "__main__":
    main()
