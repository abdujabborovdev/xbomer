from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH, override=True)


SEENSMS_KEY = os.getenv('SEENSMS_KEY')
DB_KEY = os.getenv('DB_KEY')
