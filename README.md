# Windsor Dress Stock Bot

Checks the Windsor Store product page for **"Turn Up The Tease Ruffle Halter
Mini Dress"**, colorway **Red**, size **Small** (variant `42978350759987`),
and sends you a free push notification the moment it comes back in stock.
Runs entirely on GitHub's free Actions runners — no server, no Claude
session, no ongoing cost.

Product page: https://www.windsorstore.com/products/turn-up-the-tease-ruffle-halter-mini-dress-05103000064060?variant=42978350759987

## How it works

- `check_stock.py` fetches the store's own product JSON
  (`.../<handle>.js`, a standard Shopify endpoint) and reads the
  `available` flag for the one variant ID we care about.
- It compares that to the last known state in `state.json`. Only on the
  transition from *out of stock* → *in stock* does it fire a notification
  (so you get pinged once, not every 15 minutes forever).
- `.github/workflows/check_stock.yml` runs that script on a schedule via
  GitHub Actions and commits the updated `state.json` back to the repo.
- Notifications go out via [ntfy.sh](https://ntfy.sh) — a free, no-signup
  push notification service. You just subscribe to a topic name (like a
  private channel) and the script publishes to it.

## Setup (about 5 minutes)

1. **Create a GitHub repo** and push these files to it (or use GitHub's
   web UI: "Add file" → "Upload files" and drop in this folder's contents,
   keeping the `.github/workflows/` path).
   - Private or public both work. Public repos get unlimited free Actions
     minutes; private repos get a generous free monthly quota that this
     tiny job won't come close to using.

2. **Pick a private ntfy topic name.** This is just a string — e.g.
   `misho-windsor-dress-7f3k2` — think of it like a password: anyone who
   knows it can see your notifications, so don't use something guessable
   like `dress-alert`.

3. **Subscribe to that topic** so you actually see the alert:
   - Install the ntfy app ([iOS](https://apps.apple.com/us/app/ntfy/id1625396347) /
     [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy)),
     open it, and add your topic name, **or**
   - Just visit `https://ntfy.sh/<your-topic-name>` in a browser tab and
     leave it open — you'll see a browser notification too.

4. **Add the topic as a repo secret** so it's not sitting in plain text in
   your workflow file:
   - Repo → Settings → Secrets and variables → Actions → New repository
     secret
   - Name: `NTFY_TOPIC`
   - Value: the topic name you picked in step 2

5. **Enable Actions** if GitHub prompts you to, and that's it — the
   workflow starts running automatically every 15 minutes. You can also
   go to the Actions tab → "Check Windsor dress stock" → "Run workflow" to
   trigger an immediate check at any time.

## Testing it actually works

The Red/Small variant is currently sold out, so you won't see a real
notification until it restocks. To confirm the notification pipeline
itself works, run this once locally (or temporarily edit `VARIANT_ID` in
`check_stock.py` to `42978350891059`, which is Red/**Large** and *is*
currently in stock):

```bash
pip install -r requirements.txt
NTFY_TOPIC=your-topic-name python check_stock.py
```

You should get a push within a few seconds. Revert the variant ID
afterwards (or just delete `state.json` so the real run isn't skipped as
"no change").

## Adjusting things later

- **Different variant/color:** change `VARIANT_ID` and `VARIANT_LABEL` in
  `check_stock.py`. You can find other variant IDs in the product's
  `.js` JSON (open `PRODUCT_JSON_URL` from the script in a browser).
- **Check frequency:** edit the `cron` line in
  `.github/workflows/check_stock.yml`. GitHub's practical floor is about
  every 5 minutes, though it may run scheduled jobs a bit late during
  busy periods — this isn't guaranteed to the minute.
- **Repeat notifications while in stock:** currently it only notifies once
  per restock (on the transition). If you'd rather be reminded every run
  while it's in stock, remove the `not was_in_stock` condition in
  `check_stock.py`.
