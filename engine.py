"""WhatsApp Vendor Agent - Core Engine
Python stdlib only. No pip deps. Runs on Termux, laptop, VPS.
Owner product for George Agbe - sellable to Nigerian SMEs.
"""
import json
import os
import re
import hashlib

DEFAULT_CATALOG = os.path.join(os.path.dirname(__file__), "catalog.json")

def format_naira(amount):
    return f"N{amount:,}"

class VendorAgent:
    def __init__(self, catalog_path=None, catalog=None):
        if catalog is not None:
            self.catalog = catalog
        else:
            path = catalog_path or DEFAULT_CATALOG
            with open(path, "r", encoding="utf-8") as f:
                self.catalog = json.load(f)
        self.vendor = self.catalog.get("vendor", {})
        self.products = self.catalog.get("products", [])
        self.delivery_zones = self.catalog.get("delivery_zones", {})
        self.free_delivery_above = self.catalog.get("free_delivery_above", 0)
        self._order_counter = 1000

    # ---------- product lookup ----------
    def find_product(self, text):
        if not text:
            return None
        t = text.lower()
        # exact keyword match first - longest keyword wins
        best = None
        best_len = 0
        for p in self.products:
            for kw in p.get("keywords", []):
                if kw.lower() in t and len(kw) > best_len:
                    best = p
                    best_len = len(kw)
            # name match
            name_low = p["name"].lower()
            # token overlap
            if name_low in t:
                if len(name_low) > best_len:
                    best = p
                    best_len = len(name_low)
        if best:
            return best
        # token overlap fallback
        tokens = set(re.findall(r"[a-z]+", t))
        scored = []
        for p in self.products:
            words = set(re.findall(r"[a-z]+", p["name"].lower()))
            for kw in p.get("keywords", []):
                words.update(re.findall(r"[a-z]+", kw.lower()))
            overlap = len(tokens & words)
            if overlap:
                scored.append((overlap, p))
        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            # require at least 1 meaningful overlap and avoid generic words
            generic = {"the", "a", "is", "it", "for", "me", "i", "want", "buy"}
            if scored[0][0] >= 1 and not tokens.issubset(generic):
                # check if overlapping word is not just generic product word alone ambiguous?
                return scored[0][1]
        return None

    def find_zone(self, text):
        if not text:
            return None
        t = text.lower()
        for zone in self.delivery_zones:
            if zone.lower() in t:
                return zone
        return None

    def list_products_text(self):
        lines = []
        for p in self.products:
            stock_note = "available" if p["stock"] > 0 else "SOLD OUT"
            lines.append(f"- {p['name']}: {format_naira(p['price'])} ({stock_note})")
        return "\n".join(lines)

    # ---------- intent ----------
    def detect_intent(self, text):
        t = (text or "").lower().strip()
        if not t:
            return "fallback"
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "how far", "abeg"]
        # greeting only if short or starts with greeting and no product intent words
        if any(t == g or t.startswith(g + " ") or t.startswith(g + ",") for g in greetings) and len(t.split()) <= 4:
            return "greeting"
        if any(w in t for w in ["pay", "payment", "account number", "transfer", "how do i pay", "paystack"]):
            # if also ordering, payment takes precedence when explicit pay question
            if "how" in t or "pay" in t:
                return "payment"
        if any(w in t for w in ["deliver", "delivery", "shipping", "ship to", "can you deliver", "do you deliver", "delivery fee", "delivery cost"]):
            return "delivery"
        if any(w in t for w in ["in stock", "available", "do you have", "is it available", "still have", "any left", "stock"]):
            return "stock"
        if any(w in t for w in ["how much", "price", "cost", "how much is", "wetin be price", "price for"]):
            return "price"
        if any(w in t for w in ["i want to buy", "want to buy", "i want", "i will buy", "order", "buy ", "take it", "i need", "to order", "place order"]):
            # if price words also present, price wins - handled above
            return "order"
        # if contains how much even without exact phrase
        if "how much" in t:
            return "price"
        # fallback: if product found, assume price inquiry is common in Nigerian commerce
        if self.find_product(t):
            return "price"
        return "fallback"

    # ---------- payment / order ----------
    def make_order_ref(self, product_id, qty=1):
        self._order_counter += 1
        raw = f"{product_id}-{qty}-{self._order_counter}"
        digest = hashlib.md5(raw.encode()).hexdigest()[:6].upper()
        return f"ORD-{self._order_counter}-{digest}"

    def create_payment_link(self, amount, order_ref):
        slug = self.vendor.get("paystack_slug") or self.vendor.get("slug", "vendor")
        # Placeholder pattern as requested - vendor replaces slug with real Paystack slug
        return f"https://paystack.com/pay/{slug}/{order_ref}?amount={amount}"

    def create_order(self, product, qty=1, zone=None):
        qty = max(1, int(qty))
        subtotal = product["price"] * qty
        delivery_fee = 0
        zone_name = None
        if zone:
            # find canonical zone
            for z, fee in self.delivery_zones.items():
                if z.lower() == str(zone).lower():
                    zone_name = z
                    delivery_fee = fee
                    break
        if self.free_delivery_above and subtotal >= self.free_delivery_above:
            delivery_fee = 0
        total = subtotal + delivery_fee
        ref = self.make_order_ref(product["id"], qty)
        link = self.create_payment_link(total, ref)
        lines = [
            f"Order Summary - {self.vendor.get('name','Our Store')}",
            f"Item: {product['name']} x{qty} - {format_naira(subtotal)}",
        ]
        if zone_name:
            lines.append(f"Delivery to {zone_name}: {format_naira(delivery_fee) if delivery_fee else 'FREE'}")
        else:
            lines.append("Delivery: tell me your area and I go calculate am (e.g. Lekki, Ikeja, Abuja).")
        lines.append(f"Total: {format_naira(total)}")
        lines.append(f"Order Ref: {ref}")
        lines.append(f"Pay here (safe & instant): {link}")
        lines.append("")
        lines.append("After payment, send me your name and address here, I go confirm and dispatch sharp sharp.")
        lines.append("[Vendor note: Do NOT release item on screenshot alone. Confirm payment inside your Paystack dashboard for this Order Ref first - this na how we block fake alert.]")
        return {
            "order_ref": ref,
            "product": product,
            "qty": qty,
            "zone": zone_name,
            "subtotal": subtotal,
            "delivery_fee": delivery_fee,
            "total": total,
            "payment_link": link,
            "summary": "\n".join(lines),
        }

    def parse_qty(self, text):
        m = re.search(r"\b(\d+)\s*(pcs|pieces|piece|x)?\b", (text or "").lower())
        # avoid picking price numbers or sizes - only if near buy/want or explicit qty pattern
        # Simple: look for "2 pcs", "quantity 2", "x2", "2 pieces"
        m2 = re.search(r"(?:qty|quantity|x|pieces?|pcs)\s*(\d+)|(\d+)\s*(?:pcs|pieces)", (text or "").lower())
        if m2:
            return int(m2.group(1) or m2.group(2))
        # "i want 2" pattern
        m3 = re.search(r"want\s+(\d+)\b|need\s+(\d+)\b|buy\s+(\d+)\b", (text or "").lower())
        if m3:
            return int(m3.group(1) or m3.group(2) or m3.group(3))
        return 1

    # ---------- main respond ----------
    def respond(self, text, customer_name=""):
        t = (text or "").strip()
        intent = self.detect_intent(t)
        product = self.find_product(t)
        zone = self.find_zone(t)
        vendor_name = self.vendor.get("name", "our store")
        greet_name = f" {customer_name}" if customer_name else ""

        if intent == "greeting":
            return (
                f"Hello{greet_name}! Welcome to {vendor_name} o! How far?\n"
                f"We dey for {self.vendor.get('location','Lagos')}, open {self.vendor.get('hours','Mon-Sat')}.\n"
                f"Wetin you dey find today? Here be our hot items:\n{self.list_products_text()}\n"
                f"Just type the name, e.g. 'How much is Ankara Gown?'"
            )

        if intent == "delivery":
            if zone:
                fee = self.delivery_zones[zone]
                extra = ""
                if product:
                    order = self.create_order(product, qty=1, zone=zone)
                    extra = f"\nFor {product['name']} to {zone}, total go be {format_naira(order['total'])}."
                return (
                    f"Yes, we deliver to {zone}! Delivery fee na {format_naira(fee)}."
                    f"{extra}\nDelivery na 1-2 working days within Lagos, 2-4 days outside Lagos. "
                    f"Orders above {format_naira(self.free_delivery_above)} get FREE delivery."
                )
            fees = "\n".join([f"- {z}: {format_naira(f)}" for z, f in sorted(self.delivery_zones.items())])
            return (
                f"Yes o, we deliver nationwide!\nDelivery fees:\n{fees}\n"
                f"Free delivery for orders above {format_naira(self.free_delivery_above)}.\n"
                f"Tell me your area and the item you want, I go give you total sharp sharp."
            )

        if intent == "stock":
            if product:
                if product["stock"] > 0:
                    variants = ", ".join(product.get("variants", []))
                    var_text = f" Sizes/types available: {variants}." if variants else ""
                    return f"Yes, {product['name']} dey available. We get {product['stock']} left for stock.{var_text} Price na {format_naira(product['price'])}. You wan order am?"
                else:
                    return f"Ah, sorry o, {product['name']} don finish for now (sold out). No worry, check other fine items:\n{self.list_products_text()}\nI fit notify you when e restock if you want."
            return f"Tell me the item name make I check stock for you. Our items:\n{self.list_products_text()}"

        if intent == "price":
            if product:
                variants = ", ".join(product.get("variants", []))
                stock_note = "e dey available" if product["stock"] > 0 else "but e don finish"
                return (
                    f"{product['name']} na {format_naira(product['price'])}. {product.get('description','')} "
                    f"For stock, {stock_note}."
                    + (f" Options: {variants}." if variants else "")
                    + f"\nYou wan make I create order for you? Just say 'I want to buy {product['name']}' plus your area."
                )
            return f"I no see that item for our list o. Maybe na different name? Here be wetin we get:\n{self.list_products_text()}"

        if intent == "order":
            if product:
                if product["stock"] <= 0:
                    return f"Sorry o, {product['name']} don sold out. I no fit create order for am now. Check these ones wey dey:\n{self.list_products_text()}"
                qty = self.parse_qty(t)
                order = self.create_order(product, qty=qty, zone=zone)
                return f"No wahala, I don arrange am for you!\n\n{order['summary']}"
            return f"You wan order, nice one! Which item? Here be our list:\n{self.list_products_text()}\nReply with the name, e.g. 'I want to buy Sneakers'"

        if intent == "payment":
            if product:
                qty = self.parse_qty(t)
                order = self.create_order(product, qty=qty, zone=zone)
                return f"Payment easy o. Use this secure link, no need to send transfer screenshot wey fit be fake alert:\n{order['summary']}"
            return (
                f"Payment na through Paystack, safe and instant.\n"
                f"When you order, I go give you a personal payment link like https://paystack.com/pay/{self.vendor.get('paystack_slug','vendor')}/ORD-xxxx\n"
                f"We confirm for our dashboard before dispatch, so no fake alert wahala.\n"
                f"Tell me wetin you wan buy, I go generate your link now."
            )

        # fallback
        if product:
            # product mentioned but intent unclear - treat as price
            return self.respond(f"how much is {product['name']}", customer_name)
        return (
            f"No vex, I no fully understand that one. I be assistant for {vendor_name}.\n"
            f"I fit help you with price, stock, delivery and ordering.\n"
            f"Try: 'How much is Ankara Gown?' or 'Do you deliver to Lekki?' or 'I want to buy Senator Set'\n"
            f"Our products:\n{self.list_products_text()}"
        )

# convenience for tests / CLI
def load_agent(catalog_path=None):
    return VendorAgent(catalog_path=catalog_path)

if __name__ == "__main__":
    agent = load_agent()
    print(agent.respond("Hello"))
    print("---")
    print(agent.respond("How much is Ankara Gown?"))
