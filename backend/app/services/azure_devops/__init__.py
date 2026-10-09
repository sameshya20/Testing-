import os
import logging
from typing import Optional
from app.core.config import settings
from app.services.azure_devops.interface import AzureDevOpsService
from app.services.azure_devops.mock_service import MockAzureDevOpsService
from app.services.azure_devops.real_service import (
    RealAzureDevOpsService,
    normalize_organization,
    strip_html_tags
)

logger = logging.getLogger(__name__)

# Singletons for mock and real services
_mock_instance: Optional[MockAzureDevOpsService] = None
_real_instance: Optional[RealAzureDevOpsService] = None


def get_azure_devops_service() -> AzureDevOpsService:
    """
    Factory function returning the active AzureDevOpsService implementation.
    Controlled by the AZURE_DEVOPS_MODE environment variable or setting:
      - 'mock' (default): Returns MockAzureDevOpsService for local testing without real Azure credentials
      - 'real': Returns RealAzureDevOpsService for live Microsoft Azure DevOps REST API v7.0
    """
    global _mock_instance, _real_instance

    mode = os.getenv("AZURE_DEVOPS_MODE", getattr(settings, "AZURE_DEVOPS_MODE", "mock")).lower().strip()

    if mode == "real":
        if _real_instance is None:
            _real_instance = RealAzureDevOpsService()
        return _real_instance
    else:
        if _mock_instance is None:
            _mock_instance = MockAzureDevOpsService()
        return _mock_instance


class AzureDevOpsServiceProxy:
    """
    Dynamic proxy routing attribute/method access to the active Azure DevOps service.
    Allows seamless hot-switching between mock and real mode while preserving existing
    calls like `azure_devops_service.is_connected` or `await azure_devops_service.get_projects()`.
    """

    def __getattr__(self, name: str):
        active = get_azure_devops_service()
        return getattr(active, name)


# Singleton proxy exported for backward and forward compatibility
azure_devops_service = AzureDevOpsServiceProxy()

__all__ = [
    "AzureDevOpsService",
    "MockAzureDevOpsService",
    "RealAzureDevOpsService",
    "get_azure_devops_service",
    "azure_devops_service",
    "normalize_organization",
    "strip_html_tags"
]
