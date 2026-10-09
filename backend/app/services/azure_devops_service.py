"""
Backward-compatibility bridge for app.services.azure_devops_service.
Re-exports the active azure_devops_service from the new app.services.azure_devops package.
"""
from app.services.azure_devops import (
    AzureDevOpsService,
    MockAzureDevOpsService,
    RealAzureDevOpsService,
    get_azure_devops_service,
    azure_devops_service,
    normalize_organization,
    strip_html_tags
)

# Alias for backwards compatibility
AzureDevOpsRealService = RealAzureDevOpsService

__all__ = [
    "AzureDevOpsService",
    "MockAzureDevOpsService",
    "RealAzureDevOpsService",
    "AzureDevOpsRealService",
    "get_azure_devops_service",
    "azure_devops_service",
    "normalize_organization",
    "strip_html_tags"
]
