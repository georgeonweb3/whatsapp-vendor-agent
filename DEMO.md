# DEMO - Real Conversation Transcript

Verified run on 2026-11-07 in this workspace.
Command:
```bash
printf "How much is Ankara Gown?\nDo you deliver to Lekki?\nIs Senator Set available?\nI want to buy Ankara Gown\nHow do I pay?\nHow much is iPhone 15?\nquit\n" | python3 simulator.py
```

Tests before demo:
```
Ran 15 tests in 0.003s - OK
test_catalog_loaded, test_price_lookup_ankara, test_price_lookup_sneakers_keyword,
test_delivery_lekki, test_delivery_general, test_stock_available, test_stock_sold_out,
test_unknown_product, test_greeting, test_order_flow, test_order_with_zone_includes_delivery,
test_payment_intent, test_fallback, test_format_naira, test_intent_detection - all ok
```

Webhook server verified separately:
- `GET /health` -> `{"status": "ok", "vendor": "Adaeze Styles", "products": 8}`
- `GET /webhook?hub.mode=subscribe&hub.verify_token=adaeze-verify-token&hub.challenge=CHALLENGE123` -> `CHALLENGE123`
- `POST /webhook` with Meta format message "How much is Ankara Gown?" -> `{"status": "received", "replies": [{"to": "2348011112222", "text": "Ankara Gown na N35,000. ..."}]}`

---

## Transcript (actual output, customer prompts in order)

**Bot (on start):**
> Hello! Welcome to Adaeze Styles o! How far?
> We dey for Balogun Market, Lagos Island, open Mon-Sat 8am-7pm.
> Wetin you dey find today? Here be our hot items:
> - Ankara Gown: N35,000 (available)
> - Men's Senator Set: N45,000 (available)
> - Unisex Sneakers: N28,000 (available)
> - Asoebi Lace - 5 Yards: N65,000 (available)
> - Ladies Leather Handbag: N22,000 (SOLD OUT)
> - Men's Jalabia: N18,000 (available)
> - Auto Gele Head Tie: N12,000 (available)
> - Kids Traditional Wear Set: N20,000 (available)
> Just type the name, e.g. 'How much is Ankara Gown?'

**You:** How much is Ankara Gown?
**Bot:** Ankara Gown na N35,000. Premium Ankara gown, ready to wear, lined. For stock, e dey available. Options: S, M, L, XL. You wan make I create order for you? Just say 'I want to buy Ankara Gown' plus your area.

**You:** Do you deliver to Lekki?
**Bot:** Yes, we deliver to Lekki! Delivery fee na N2,500. Delivery na 1-2 working days within Lagos, 2-4 days outside Lagos. Orders above N100,000 get FREE delivery.

**You:** Is Senator Set available? *(scripted as "Is Senator Set available?" - stock intent, product via keyword "senator")*
**Bot:** Yes, Men's Senator Set dey available. We get 8 left for stock. Sizes/types available: M, L, XL, XXL. Price na N45,000. You wan order am?

**You:** I want to buy Ankara Gown
**Bot:**
> No wahala, I don arrange am for you!
>
> Order Summary - Adaeze Styles
> Item: Ankara Gown x1 - N35,000
> Delivery: tell me your area and I go calculate am (e.g. Lekki, Ikeja, Abuja).
> Total: N35,000
> Order Ref: ORD-1001-9847B2
> Pay here (safe & instant): https://paystack.com/pay/adaeze-styles/ORD-1001-9847B2?amount=35000
>
> After payment, send me your name and address here, I go confirm and dispatch sharp sharp.
> [Vendor note: Do NOT release item on screenshot alone. Confirm payment inside your Paystack dashboard for this Order Ref first - this na how we block fake alert.]

**You:** How do I pay?
**Bot:** Payment na through Paystack, safe and instant. When you order, I go give you a personal payment link like https://paystack.com/pay/adaeze-styles/ORD-xxxx. We confirm for our dashboard before dispatch, so no fake alert wahala. Tell me wetin you wan buy, I go generate your link now.

**You:** How much is iPhone 15?
**Bot:** I no see that item for our list o. Maybe na different name? Here be wetin we get: [full catalog list as above]

**You:** quit
**Bot:** Thank you o! Come back anytime. Bye bye!

---

Note: order ref is generated per run, so the exact suffix will differ on your run. Prices, delivery fee, payment link pattern, and sold-out handling are deterministic from catalog.json.
