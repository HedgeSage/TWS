import json
import os
import re
from typing import Any, Dict
from dotenv import load_dotenv

class ConfigLoader:
    """
    配置加载器
    负责读取 JSON 配置文件，并解析环境变量占位符 ${VAR}
    """
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        
        # 自动加载 .env
        load_dotenv()

    def load(self) -> Dict[str, Any]:
        """加载配置"""
        if not os.path.exists(self.config_path):
            # Fallback to example if exists, or error
            if os.path.exists("config.example.json"):
                print(f"Warning: {self.config_path} not found, using config.example.json")
                self.config_path = "config.example.json"
            else:
                raise FileNotFoundError(f"Config file {self.config_path} not found")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 替换环境变量 ${VAR}
        # 正则匹配 ${VAR_NAME}
        pattern = re.compile(r'\$\{(\w+)\}')
        
        def replace_env(match):
            env_var = match.group(1)
            return os.getenv(env_var, "") # 默认为空字符串，或者保留原值? 建议空
            
        content_substituted = pattern.sub(replace_env, content)
        
        try:
            self._config = json.loads(content_substituted)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
            
        return self._config

    @property
    def config(self) -> Dict[str, Any]:
        return self._config

# Global instance for easy access? Or just class.
