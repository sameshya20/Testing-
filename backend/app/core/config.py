import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Test Case Generator Platform"
    API_V1_STR: str = "/api/v1"
    
    # Azure DevOps Configuration
    ADO_ORGANIZATION: str = os.getenv("ADO_ORGANIZATION", "EnterpriseOrg")
    ADO_PROJECT: str = os.getenv("ADO_PROJECT", "QualityAssurance")
    ADO_PAT: str = os.getenv("ADO_PAT", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test_generator.db")

    # CORS Allowed Origins
    CORS_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
        if origin.strip()
    ]

settings = Settings()

