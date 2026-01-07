import asyncio
import ccxt.pro as ccxt
import json

async def test_specific():
    exchange = ccxt.okx()
    
    print("--- Testing Fetch Specific Instrument ---")
    # OKX Instrument ID format: BTC-USDT-SWAP
    target_inst_id = "BTC-USDT-SWAP"
    
    print("--- 1. Discovery Phase ---")
    await exchange.load_markets(True, {'instType': 'SWAP'})
    
    # Find BTC/USDT:USDT
    target_symbol = "BTC/USDT:USDT"
    if target_symbol in exchange.markets:
        market = exchange.markets[target_symbol]
        real_id = market['id']
        print(f"Found {target_symbol} -> ID: {real_id}")
    else:
        print(f"Could not find {target_symbol}")
        await exchange.close()
        return

    print("\n--- 2. Specific Fetch Phase ---")
    # Now try to fetch just this one
    # Note: CCXT fetch_markets returns a list
    try:
        # Pass BOTH instType and instId
        params = {
            'instType': 'SWAP',
            'instId': real_id
        }
        print(f"Requesting with params: {params}")
        specific_markets = await exchange.fetch_markets(params)
        print(f"Fetched {len(specific_markets)} markets.")
        if specific_markets:
            print(f"Result: {specific_markets[0]['symbol']} ({specific_markets[0]['id']})")
            
    except Exception as e:
        print(f"Specific fetch failed: {e}")
        
    await exchange.close()

if __name__ == "__main__":
    asyncio.run(test_specific())
