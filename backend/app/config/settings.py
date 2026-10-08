from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"

class Settings(BaseSettings):
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # JWT Settings
    JWT_SECRET_KEY: str = "sentinel_rag_super_secret_dev_key_2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 8
    
    # LLM Settings (Groq) - used for production chatbot pipeline ONLY
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_FAST_MODEL: str = "llama-3.1-8b-instant"

    # Evaluation LLM Settings (Ollama - local, unlimited, free)
    # Production pipeline STAYS on Groq; ONLY evaluation judges use Ollama
    EVAL_LLM_PROVIDER: str = "ollama"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Embedding Settings
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    
    # Clearance Levels Mapping
    # Public-level documents are not yet present in the dataset as of this phase - 
    # RBAC logic still supports it for when such data is added.
    CLEARANCE_LEVELS: dict = {
        "Public": 0,
        "Internal": 1,
        "Confidential": 2,
        "Restricted": 3
    }
    
    # Optional OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # DB Settings
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    NEO4J_URI: Optional[str] = None
    NEO4J_USER: Optional[str] = None
    NEO4J_PASSWORD: Optional[str] = None

    DATA_DIR_PATH: Path = DATA_DIR
    COMPANY_STRUCTURE_PATH: Path = DATA_DIR / "Company_strucutre" / "company_structure.json"
    EMPLOYEE_ROSTER_DIR: Path = DATA_DIR / "Employee_roaster"
    DEPARTMENT_DOCS_DIR: Path = DATA_DIR / "department_docs"
    EMPLOYEE_DOCS_DIR: Path = DATA_DIR / "Employee_docs"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
