"""
FinTrace 360 - Configuration and Settings
Centralized paths, database configurations, and environment variables.
"""

from pathlib import Path
import os

# Base Directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLE_DATA_DIR = DATA_DIR / "sample"

AMLSIM_RAW_DIR = RAW_DATA_DIR / "amlsim"
PAYSIM_RAW_DIR = RAW_DATA_DIR / "paysim"
IEEE_CIS_RAW_DIR = RAW_DATA_DIR / "ieee_cis"

OUTPUTS_DIR = BASE_DIR / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
METRICS_DIR = OUTPUTS_DIR / "metrics"
REPORTS_OUTPUT_DIR = OUTPUTS_DIR / "reports"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
SQL_DIR = BASE_DIR / "sql"
POWERBI_DIR = BASE_DIR / "powerbi"

# Database Configuration (defaults with environment override)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "fintrace360")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def get_database_url() -> str:
    """Generate SQLAlchemy database URL."""
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Random Seed for Reproducibility
RANDOM_STATE = 42
