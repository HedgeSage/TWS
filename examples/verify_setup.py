
import asyncio
import os
import sys
from quant_system.utils.config import ConfigLoader
from quant_system.exchange.okx_adapter import OkxExchangeAdapter
from quant_system.core.event import EventEngine

async def verify():
    print(">>> Verifying Config & Connectivity <<<")
    
    # 1. Load Config
    try:
        loader = ConfigLoader("config.json")
        config = loader.load()
        print("[Pass] Config Loaded")
    except Exception as e:
        print(f"[Fail] Config Load Error: {e}")
        return

    # 2. Check Account 'sub06'
    account_name = "sub06"
    if account_name not in config['accounts']:
        print(f"[Fail] Account {account_name} not found in config")
        return
        
    acc_conf = config['accounts'][account_name]
    print(f"[Pass] Account '{account_name}' found")
    
    # 3. Check Keys (Masked)
    api_key = acc_conf['exchange'].get('api_key')
    if not api_key or "${" in api_key:
        print(f"[Fail] API Key appears invalid or missing env var: {api_key}")
        # Debug: Print env vars (masked)
        print("Debug: OKX_API_KEY env var is:", "SET" if os.getenv("OKX_API_KEY") else "UNSET")
        return
    else:
        print(f"[Pass] API Key loaded: {api_key[:4]}***")

    secret = acc_conf['exchange'].get('secret')
    if not secret or "${" in secret:
        print(f"[Fail] Secret appears invalid or missing env var")
        print("Debug: OKX_SECRET env var is:", "SET" if os.getenv("OKX_SECRET") else "UNSET")
    else:
        print(f"[Pass] Secret loaded: {secret[:2]}***")

    # 4. Connect Exchange
    print("Testing Exchange Connection...")
    event_engine = EventEngine()
    exchange = OkxExchangeAdapter(event_engine, acc_conf['exchange'])
    
    try:
        await exchange.connect()
        # Implicitly checks login in connect() usually, or we call check_login
        login_ok = await exchange.check_login()
        if login_ok:
            print("[Pass] Exchange Login SUCCESS!")
        else:
            print("[Fail] Exchange Login FAILED")
            
        await exchange.close()
    except Exception as e:
        print(f"[Fail] Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
