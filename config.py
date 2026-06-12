import os
import logging
from dotenv import load_dotenv


##### FIND AND LOAD THE .env FILE #####
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))
logger = logging.getLogger(__name__)

##### AWS CREDENTIALS #####
AWS_REGION        = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY    = os.getenv("AWS_SECRET_ACCESS_KEY")

##### BEDROCK/AI MODEL SETTINGS #####
BEDROCK_MODEL_ID  = "arn:aws:bedrock:us-east-1:469830469617:inference-profile/global.anthropic.claude-haiku-4-5-20251001-v1:0"
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID")

##### FILE PATHS #####
KB_DIR      = os.path.join(BASE_DIR, "KnowledgeBase")
CHART_DIR   = os.path.join(BASE_DIR, "static", "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "static", "reports")
CSV_PATH    = os.path.join(KB_DIR, "Sales_Data.csv")

os.makedirs(CHART_DIR,   exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

##### CHART COLORS #####
PALETTE = [
    "#4F8EF7", "#F76C5E", "#43C59E", "#F9A825",
    "#AB47BC", "#26C6DA", "#EF5350", "#66BB6A",
    "#FFA726", "#5C6BC0",
]

##### VALIDATION #####

REQUIRED_SETTINGS = {
    "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
    "AWS_SECRET_ACCESS_KEY": AWS_SECRET_KEY,
    "KNOWLEDGE_BASE": KNOWLEDGE_BASE_ID,
}

for name, value in REQUIRED_SETTINGS.items():
    if not value:
        logger.warning(
            f"'{name}' is missing from your .env file"
        )

logger.info(f"config Loaded - Region: {AWS_REGION} | Model: {BEDROCK_MODEL_ID}")