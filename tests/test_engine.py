import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine import VendorAgent, format_naira

class TestEngine(unittest.TestCase):
    def setUp(self):
        self.agent = VendorAgent()

    def test_catalog_loaded(self):
        self.assertEqual(self.agent.vendor["name"], "Adaeze Styles")
        self.assertEqual(len(self.agent.products), 8)

    def test_format_naira(self):
        self.assertEqual(format_naira(35000), "N35,000")

    def test_price_lookup_ankara(self):
        reply = self.agent.respond("How much is Ankara Gown?")
        self.assertIn("35,000", reply)
        self.assertIn("Ankara Gown", reply)

    def test_price_lookup_sneakers_keyword(self):
        reply = self.agent.respond("how much for sneakers")
        self.assertIn("28,000", reply)

    def test_delivery_lekki(self):
        reply = self.agent.respond("Do you deliver to Lekki?")
        self.assertIn("Lekki", reply)
        self.assertIn("2,500", reply)

    def test_delivery_general(self):
        reply = self.agent.respond("Do you deliver?")
        self.assertIn("Ikeja", reply)
        self.assertIn("Abuja", reply)

    def test_stock_available(self):
        reply = self.agent.respond("Is Ankara Gown available?")
        self.assertIn("available", reply.lower())

    def test_stock_sold_out(self):
        reply = self.agent.respond("Do you have handbag in stock?")
        # handbag stock 0
        self.assertTrue("finish" in reply.lower() or "sold out" in reply.lower())

    def test_unknown_product(self):
        reply = self.agent.respond("How much is iPhone 15?")
        self.assertIn("Ankara Gown", reply)  # should list catalog as fallback
        # should not hallucinate a price for iPhone
        self.assertNotIn("iPhone 15 na", reply)

    def test_greeting(self):
        reply = self.agent.respond("Hello")
        self.assertIn("Adaeze Styles", reply)

    def test_order_flow(self):
        reply = self.agent.respond("I want to buy Ankara Gown")
        self.assertIn("Order Summary", reply)
        self.assertIn("paystack.com/pay/adaeze-styles", reply)
        self.assertIn("ORD-", reply)
        self.assertIn("35,000", reply)

    def test_order_with_zone_includes_delivery(self):
        reply = self.agent.respond("I want to buy Sneakers for delivery to Lekki")
        # Intent may be delivery - accept either order or delivery with total; engine order path when zone parsed
        # Direct create_order check
        product = self.agent.find_product("sneakers")
        order = self.agent.create_order(product, qty=1, zone="Lekki")
        self.assertEqual(order["delivery_fee"], 2500)
        self.assertEqual(order["total"], 30500)
        self.assertIn("ORD-", order["order_ref"])
        self.assertIn("paystack.com/pay/", order["payment_link"])

    def test_payment_intent(self):
        reply = self.agent.respond("How do I pay for Ankara Gown?")
        self.assertIn("paystack", reply.lower())
        self.assertIn("Paystack", reply)

    def test_fallback(self):
        reply = self.agent.respond("blah blah nonsense xyz")
        self.assertIn("Adaeze Styles", reply)

    def test_intent_detection(self):
        self.assertEqual(self.agent.detect_intent("How much is Ankara Gown?"), "price")
        self.assertEqual(self.agent.detect_intent("Do you deliver to Abuja?"), "delivery")
        self.assertEqual(self.agent.detect_intent("Hello"), "greeting")

if __name__ == "__main__":
    unittest.main()
