# app/core/config.py

from pydantic_settings import BaseSettings
from typing import Dict, List, Optional

class Settings(BaseSettings):
    """
    应用配置 - Ernie-2api
    """
    # --- 服务监听端口 ---
    LISTEN_PORT: int = 8083

    # --- 应用元数据 ---
    APP_NAME: str = "Ernie Multi-Account Local API"
    APP_VERSION: str = "1.0.0"
    DESCRIPTION: str = "一个支持多账号和粘性会话的高性能百度文心一言本地代理。"

    # --- 认证与安全 ---
    API_MASTER_KEY: Optional[str] = None

    # --- 模型列表 (从抓包数据中分析得出) ---
    SUPPORTED_MODELS: List[str] = [
        "ernie-4.5-turbo", # 对应 EB45T
        "ernie-x1",        # 对应 X1_1
    ]

    # --- 百度账号 1 (默认) ---
    # 这是处理所有请求的主力账号，必须填写
    BAIDU_ACCOUNT_1_COOKIE: str = ""
    BAIDU_ACCOUNT_1_ACS_TOKEN: str = ""
    BAIDU_ACCOUNT_1_SIGN: str = "" # 这是一个动态值，需要从请求Payload中获取

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()