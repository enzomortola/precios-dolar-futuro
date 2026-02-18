from simulator import Portfolio
import os

# Reset portfolio for testing
with open("portfolio.json", "w") as f:
    f.write('{"cash": 20000000, "positions": {}}')

p = Portfolio()
print(f"Initial Cash: {p.cash}")
assert p.cash == 20000000
assert p.positions == {}

# Test Buy
success, msg = p.buy("TEST/AGO24", 10, 100) # Cost 1000
print(f"Buy 1: {msg}")
assert success
assert p.cash == 19999000
assert p.positions["TEST/AGO24"] == 10

# Test Buy Insufficient Funds
success, msg = p.buy("EXPENSIVE", 1, 25000000)
print(f"Buy Fail: {msg}")
assert not success
assert p.cash == 19999000

# Test Sell
success, msg = p.sell("TEST/AGO24", 5, 200) # Income 1000
print(f"Sell 1: {msg}")
assert success
assert p.cash == 20000000 # Back to 20M (+1000 profit from trade diff? No, bought at 100*10=1000. Sold 5*200=1000. Cash was 19999000 + 1000 = 20000000 OK)
assert p.positions["TEST/AGO24"] == 5

# Test Sell All
success, msg = p.sell("TEST/AGO24", 5, 200)
print(f"Sell All: {msg}")
assert success
assert "TEST/AGO24" not in p.positions

print("✅ Logic Verification Passed")
