import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Test Case Generator Platform"
    API_V1_STR: str = "/api/v1"
    
    # Azure DevOps Configuration
    AZURE_DEVOPS_MODE: str = (os.getenv("AZURE_DEVOPS_MODE") or "mock").lower().strip()
    AZURE_DEVOPS_ORG: str = os.getenv("AZURE_DEVOPS_ORG") or os.getenv("ADO_ORGANIZATION", "DemoOrganization")
    AZURE_DEVOPS_PROJECT: str = os.getenv("AZURE_DEVOPS_PROJECT") or os.getenv("ADO_PROJECT", "TestCaseDemoProject")
    AZURE_DEVOPS_PAT: str = os.getenv("AZURE_DEVOPS_PAT") or os.getenv("ADO_PAT", "")
    
    # Backward compatibility aliases
    @property
    def ADO_ORGANIZATION(self) -> str:
        return self.AZURE_DEVOPS_ORG

    @property
    def ADO_PROJECT(self) -> str:
        return self.AZURE_DEVOPS_PROJECT

    @property
    def ADO_PAT(self) -> str:
        return self.AZURE_DEVOPS_PAT
    
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

