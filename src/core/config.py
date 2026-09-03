from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Project metadata
    PROJECT_NAME: str = "AI Expert Trading Assistant"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Indodax Trade API V2 Credentials
    INDODAX_API_KEY: str = ""
    INDODAX_SECRET_KEY: str = ""
    INDODAX_REST_URL: str = "https://indodax.com/api"
    INDODAX_TAPI_URL: str = "https://indodax.com/tapi"
    INDODAX_WS_URL: str = "wss://indodax.com/ws/"

    # Trading Execution Mode
    # If False, runs in paper trading (simulated) mode to prevent accidental live losses.
    LIVE_TRADING: bool = False

    # Confluence Scoring Weights (Strict PRD rule: 40% Trend, 30% SND, 30% Macro)
    WEIGHT_TREND: float = Field(default=0.40, description="40% Trend & Market Structure")
    WEIGHT_SND: float = Field(default=0.30, description="30% Key Levels / Supply & Demand")
    WEIGHT_MACRO: float = Field(default=0.30, description="30% Macroeconomic Sentiment")

    # Confluence Thresholds
    MIN_CONFLUENCE_BUY_SCORE: float = 70.0
    MIN_CONFLUENCE_SELL_SCORE: float = 70.0

    # Risk Management
    MAX_RISK_PER_TRADE_PERCENT: float = 2.0  # Max 2% risk of equity per trade
    MIN_RISK_REWARD_RATIO: float = 2.0      # Minimum 1:2 R:R ratio

    # Safety & Deadman Switch
    DEADMAN_TIMEOUT_SEC: int = 30           # 30 seconds watchdog
    ENABLE_DEADMAN_SWITCH: bool = True

    # Web Dashboard & API
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    # Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    HISTORICAL_DIR: Path = BASE_DIR / "data" / "historical"
    MEMORY_DIR: Path = BASE_DIR / "data" / "memory"

settings = Settings()
