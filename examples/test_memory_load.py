import asyncio
import ccxt.pro as ccxt
import os
from dotenv import load_dotenv

load_dotenv()

async def test_load_all():
    print("--- Testing Full Load ---")
    exchange = ccxt.okx()
    await exchange.load_markets()
    print(f"Loaded {len(exchange.markets)} markets.")
    # Check if we have SPOT
    spots = [m for m in exchange.markets.values() if m['type'] == 'spot']
    swaps = [m for m in exchange.markets.values() if m['type'] == 'swap']
    print(f"SPOT: {len(spots)}, SWAP: {len(swaps)}")
    await exchange.close()

async def test_load_swap_only():
    print("\n--- Testing Partial Load (params={'instType': 'SWAP'}) ---")
    exchange = ccxt.okx()
    # Try passing params. Note: load_markets(reload=True, params={...})
    # Warning: Not all exchanges support params in fetch_markets but OKX endpoint does.
    # OKX API: GET /api/v5/public/instruments?instType=SWAP
    try:
        # In CCXT, load_markets calls fetch_markets. 
        # But fetch_markets signature in base is (params={}).
        # Let's hope it passes it down.
        await exchange.load_markets(True, {'instType': 'SWAP'})
        print(f"Loaded {len(exchange.markets)} markets.")
        spots = [m for m in exchange.markets.values() if m['type'] == 'spot']
        swaps = [m for m in exchange.markets.values() if m['type'] == 'swap']
        print(f"SPOT: {len(spots)}, SWAP: {len(swaps)}")
    except Exception as e:
        print(f"Error: {e}")
    await exchange.close()

async def main():
    await test_load_all()
    await test_load_swap_only()

if __name__ == "__main__":
    asyncio.run(main())
