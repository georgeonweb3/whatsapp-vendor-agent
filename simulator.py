"""CLI Simulator - chat as a customer in your terminal.
Run: python3 simulator.py
Preloaded with demo vendor Adaeze Styles.
Type 'quit' or 'exit' to stop. Type 'catalog' to see products.
"""
import sys
from engine import VendorAgent

def main():
    agent = VendorAgent()
    vendor = agent.vendor.get("name", "Vendor")
    print(f"=== WhatsApp Simulator - {vendor} ===")
    print("You are the customer. The bot is the vendor assistant.")
    print("Try: Hello / How much is Ankara Gown? / Do you deliver to Lekki? / I want to buy Ankara Gown")
    print("Type 'quit' to exit.\n")
    print(f"Bot: {agent.respond('Hello')}\n")
    # Interactive if tty, else line-by-line from stdin (supports scripted tests)
    while True:
        try:
            line = input("You: ")
        except EOFError:
            break
        if line is None:
            break
        text = line.strip()
        if not text:
            continue
        if text.lower() in ("quit", "exit", "bye"):
            print("Bot: Thank you o! Come back anytime. Bye bye!")
            break
        if text.lower() == "catalog":
            print(f"Bot: {agent.list_products_text()}\n")
            continue
        reply = agent.respond(text)
        print(f"Bot: {reply}\n")

if __name__ == "__main__":
    main()
