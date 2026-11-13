import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    model_path: Path = ROOT_DIR / os.getenv("MODEL_PATH", "models/document_classifier.joblib")
    dataset_path: Path = ROOT_DIR / os.getenv("DATASET_PATH", "data/documents.csv")
    min_award_amount: float = float(os.getenv("MIN_AWARD_AMOUNT", "1000"))
    classifier_min_confidence: float = float(os.getenv("CLASSIFIER_MIN_CONFIDENCE", "0.55"))
    llm_enabled: bool = os.getenv("LLM_ENABLED", "false").lower() == "true"
    llm_model: str = os.getenv("LLM_MODEL", "claude-opus-5-5")
    llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
    api_url: str = os.getenv("API_URL", "http://localhost:8000")


settings = Settings()
