# WhatsApp Vendor Agent - for Nigerian SMEs

**Sellable product built for George Agbe, Lagos.**
Price to vendors: **N20,000 setup + N10,000/month**

Your customers already buy on WhatsApp. This bot replies in under 5 seconds, 24/7, so you stop losing sales when you are busy, asleep, or in traffic.

## What it does
- Answers price questions instantly from your real catalog
- Answers delivery fees by area (Lekki, Ikeja, Abuja, etc.)
- Checks stock and says sold out honestly
- Creates an order summary with a Paystack payment link
- Blocks fake-alert wahala: vendor is told to confirm in Paystack dashboard, not by screenshot
- Talks in friendly Nigerian commerce style, light Pidgin, clear English

## Quick start (10 minutes)

No pip install. Python stdlib only. Works on Termux, laptop, any VPS.

```bash
cd whatsapp-vendor-agent
# 1. Try the demo chat
python3 simulator.py

# 2. Run tests
python3 -m unittest tests.test_engine -v

# 3. Run the webhook server (for WhatsApp Business API)
python3 server.py 8000
curl http://localhost:8000/health
```

### Scripted demo (no typing)
```bash
printf "How much is Ankara Gown?\nI want to buy Ankara Gown\nquit\n" | python3 simulator.py
```

## How a vendor onboards

1. **Give us your price list** - name, price, stock, sizes. A photo of your notebook, Excel, or voice note is fine. We convert it to `catalog.json` in 30 mins.
2. **Give us delivery areas + fees** - e.g. Yaba N1,200, Lekki N2,500, Abuja N5,000, plus free delivery above a amount.
3. **Give us your Paystack slug** - from paystack.com, e.g. `adaeze-styles`. If you have no Paystack yet, we help you create it (needs BVN + bank account, vendor does this herself for security).
4. **We test with you** - you chat the bot as a customer for 10 mins, we fix prices/wording.
5. **Go live** - we connect the bot to your WhatsApp Business number via Meta WhatsApp Business API (official route). You keep your number and your phone.
6. **You get a 1-page cheat sheet** - how to confirm payment in Paystack, how to update stock (send us "sneakers stock 5" and we update, or edit catalog.json).

Edit your own catalog: copy `catalog.example.json` to `catalog.json` and fill it.

Catalog format:
```json
{
  "vendor": {"name": "Adaeze Styles", "slug": "adaeze-styles", "paystack_slug": "adaeze-styles", "location": "Balogun Market, Lagos Island", "hours": "Mon-Sat 8am-7pm"},
  "delivery_zones": {"Lekki": 2500, "Ikeja": 1500, "Abuja": 5000},
  "free_delivery_above": 100000,
  "products": [{"id": "ankara-gown", "name": "Ankara Gown", "price": 35000, "stock": 12, "variants": ["S","M","L"], "keywords": ["ankara","gown"], "description": "Premium Ankara gown"}]
}
```

## Connecting to real WhatsApp (production notes)

This MVP does **not** need any credential to demo or test.

For live use:
1. Vendor creates a Meta app + WhatsApp Business API number (or uses an existing BSP like 360dialog / Twilio).
2. Set webhook URL to `https://your-server/webhook` and verify token to the value in env `WHATSAPP_VERIFY_TOKEN`.
3. In `server.py`, `extract_messages()` already parses Meta format. To send the reply back live, add a POST to Graph API with the vendor's own token - intentionally left out of this demo so no token is ever collected in chat or code. The server already returns `{"replies": [...]}` in its JSON response for testing and logs the reply.
4. Host `server.py` on a small VPS, Render, Railway, or Termux + Cloudflare Tunnel for testing.

## Files
- `engine.py` - core brain, intent + replies + orders
- `simulator.py` - terminal chat demo
- `server.py` - webhook server (GET verify, POST messages, GET /health)
- `catalog.json` - demo vendor Adaeze Styles, 8 products
- `catalog.example.json` - template for a new vendor
- `tests/test_engine.py` - 15 unittest tests
- `SALES_KIT.md` - how George sells the first 10
- `DEMO.md` - real conversation transcript from a tested run

## Pricing for vendors (what George charges)
- Setup: N20,000 one-time (catalog setup, testing, training)
- Monthly: N10,000/month (hosting, support, stock updates, tweaks)
- First 3 pilot vendors: offer N10,000 setup discount in exchange for a testimonial + referral, **only if George approves per vendor**.

## Safety
- Never ask a vendor for their Paystack secret key in chat.
- Payment link is a placeholder pattern `https://paystack.com/pay/<slug>/<order-ref>?amount=<total>` until the vendor's real Paystack page is configured.
- Vendor rule is built into every order: do not dispatch on screenshot, confirm in dashboard first.
