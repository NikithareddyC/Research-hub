import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ARXIV_API_KEY = os.getenv("ARXIV_API_KEY", "")
CROSSREF_API_KEY = os.getenv("CROSSREF_API_KEY", "")
CORE_API_KEY = os.getenv("CORE_API_KEY", "")
OPENALEX_API_KEY = os.getenv("OPENALEX_API_KEY", "")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./papers.db")

# Model settings
MAX_PAPERS_PER_QUERY = 500
SUMMARY_MAX_LENGTH = 200
SUMMARY_MIN_LENGTH = 50

# Frontend URL
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Cache settings
CACHE_TTL = 3600  # 1 hour
