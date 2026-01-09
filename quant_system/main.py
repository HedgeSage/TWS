import asyncio
import signal
import logging
import sys
from typing import Dict, Type

from quant_system.core.event import EventEngine
from quant_system.exchange.okx_adapter import OkxExchangeAdapter
from quant_system.utils.config import ConfigLoader
from quant_system.strategy.base import BaseStrategy

# Strategy Registry
from quant_system.strategy.dynamic_demo import DynamicRebalanceStrategy
from quant_system.strategy.dual_ma import DualMAStrategy

STRATEGY_MAP: Dict[str, Type[BaseStrategy]] = {
    "DynamicRebalance": DynamicRebalanceStrategy,
    "DualMA": DualMAStrategy,
}

import argparse

class TradingSystem:
    def __init__(self, config_path: str, account_name: str):
        # 1. Load Config
        self.loader = ConfigLoader(config_path)
        self.full_config = self.loader.load()
        
        # 2. Extract Account Config
        accounts = self.full_config.get('accounts', {})
        if account_name not in accounts:
            print(f"Error: Account '{account_name}' not found in config.")
            print(f"Available accounts: {list(accounts.keys())}")
            sys.exit(1)
            
        self.config = accounts[account_name]
        self.system_config = self.full_config.get('system', {})
        
        self.setup_logging()
        self.logger = logging.getLogger(f"System[{account_name}]")
        self.logger.info(f"Initializing for Account: {account_name}")
        
        # 3. Components
        self.event_engine = EventEngine()
        self.exchange = OkxExchangeAdapter(self.event_engine, self.config['exchange'])
        
        # 4. Strategy Factory
        strat_conf = self.config['strategy']
        strat_name = strat_conf['name']
        strat_cls = STRATEGY_MAP.get(strat_name)
        
        if not strat_cls:
            self.logger.error(f"Unknown Strategy: {strat_name}")
            sys.exit(1)
            
        self.strategy = strat_cls(
            self.event_engine, 
            self.exchange, 
            strat_conf['symbols']
        )
        
        self.is_running = True

    def setup_logging(self):
        from datetime import datetime
        import os
        
        # Ensure logs directory exists
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_level = self.system_config.get('log_level', 'INFO')
        log_filename = f"{log_dir}/TWS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            handlers=[
                logging.FileHandler(log_filename)
            ]
        )

    async def run(self):
        """Main Loop"""
        self.logger.info(">>> Starting TWS Quant System <<<")
        
        # 1. Start Event Engine
        self.event_engine.start()
        
        # 2. Connect Exchange
        try:
            await self.exchange.connect()
            
            # Login Check
            if not await self.exchange.check_login():
                self.logger.error("Exchange Login Failed! Check API Keys.")
                sys.exit(1)
                
            # Init Leverage
            params = self.config['strategy'].get('parameters', {})
            leverage = params.get('leverage', 10)
            
            for s in self.config['strategy']['symbols']:
                await self.exchange.init_leverage(s, leverage)
                
        except Exception as e:
            self.logger.critical(f"Initialization Failed: {e}")
            sys.exit(1)

        # 3. Start Strategy
        await self.strategy.start()
        self.logger.info("Strategy Started.")

        # 4. Wait for Shutdown
        while self.is_running:
            await asyncio.sleep(1)

        # 5. Cleanup
        await self.shutdown()

    async def shutdown(self):
        self.logger.info("Shutting down...")
        await self.strategy.stop()
        await self.exchange.close()
        self.event_engine.stop()
        self.logger.info("Shutdown Complete.")

    def stop_signal(self):
        self.is_running = False

def main():
    parser = argparse.ArgumentParser(description="TWS Quant System")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    parser.add_argument("--account", required=True, help="Account ID to run (e.g. account1)")
    
    args = parser.parse_args()

    system = TradingSystem(args.config, args.account)

    def handle_sig(sig, frame):
        print(f"\nReceived Signal {sig}, stopping...")
        system.stop_signal()

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)
    
    asyncio.run(system.run())

if __name__ == "__main__":
    main()
