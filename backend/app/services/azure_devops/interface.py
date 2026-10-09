from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from app.schemas.devops import (
    DevOpsWorkItem,
    AzureDevOpsProjectItem,
    AzureDevOpsAreaItem
)

class AzureDevOpsService(ABC):
    """
    Abstract interface for Azure DevOps integration.
    Both MockAzureDevOpsService and RealAzureDevOpsService adhere to this contract,
    allowing seamless switching between mock mode and real Microsoft Azure DevOps.
    """

    @property
    @abstractmethod
    def mode(self) -> str:
        """Returns 'mock' or 'real'."""
        pass

    @property
    @abstractmethod
    def organization(self) -> str:
        """Currently configured organization name."""
        pass

    @property
    @abstractmethod
    def project(self) -> str:
        """Currently configured project name."""
        pass

    @property
    @abstractmethod
    def pat(self) -> str:
        """Personal access token (empty in mock mode)."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Whether the service is currently marked as connected."""
        pass

    @abstractmethod
    def configure(
        self,
        organization: Optional[str] = None,
        project: Optional[str] = None,
        pat: Optional[str] = None
    ) -> None:
        """Update runtime Azure DevOps credentials / settings in memory."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Reset connection state to disconnected / offline mode."""
        pass

    @abstractmethod
    def reload_from_env(self) -> None:
        """Dynamically reload credentials / settings from environment variables."""
        pass

    @abstractmethod
    async def test_connection(
        self,
        organization: Optional[str] = None,
        project: Optional[str] = None,
        pat: Optional[str] = None
    ) -> Tuple[bool, str, List[AzureDevOpsProjectItem]]:
        """
        Tests connection to Azure DevOps.
        Returns: (success: bool, message: str, projects: List[AzureDevOpsProjectItem])
        """
        pass

    @abstractmethod
    async def get_projects(self) -> List[AzureDevOpsProjectItem]:
        """Fetches all projects in the configured organization."""
        pass

    @abstractmethod
    async def get_areas(self, project: Optional[str] = None) -> List[AzureDevOpsAreaItem]:
        """Fetches classification nodes (Areas) as a hierarchical tree."""
        pass

    @abstractmethod
    async def get_flat_areas(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetches classification nodes (Areas) as a flattened list suitable for UI selectors.
        Each area dictionary has: id, name, code, path, parent_id.
        """
        pass

    @abstractmethod
    async def query_work_items(
        self,
        project: Optional[str] = None,
        area_path: Optional[str] = None,
        work_item_type: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50
    ) -> List[DevOpsWorkItem]:
        """
        Queries User Stories and Work Items (simulating WIQL in mock mode or executing WIQL in real mode).
        Supports filtering by project, area_path, work_item_type, and search text.
        """
        pass

    @abstractmethod
    async def get_single_work_item(
        self,
        work_item_id: str,
        project: Optional[str] = None
    ) -> Optional[DevOpsWorkItem]:
        """Retrieves complete work item details by ID."""
        pass

    @abstractmethod
    async def create_test_case(
        self,
        tc_data: Dict[str, Any],
        parent_work_item_id: Optional[str] = None,
        area_path: Optional[str] = None,
        project: Optional[str] = None,
        db=None
    ) -> Dict[str, Any]:
        """Creates a new test case in Azure DevOps."""
        pass

    @abstractmethod
    async def update_test_case(
        self,
        existing_ado_id: int,
        tc_data: Dict[str, Any],
        parent_work_item_id: Optional[str] = None,
        area_path: Optional[str] = None,
        project: Optional[str] = None,
        db=None
    ) -> Dict[str, Any]:
        """Updates an existing test case in Azure DevOps."""
        pass

    @abstractmethod
    async def sync_test_case(
        self,
        tc_data: Dict[str, Any],
        parent_work_item_id: Optional[str] = None,
        area_path: Optional[str] = None,
        project: Optional[str] = None,
        db=None
    ) -> Dict[str, Any]:
        """
        Synchronizes a single test case:
        If azure_test_case_id already exists (in payload or DB), updates it.
        Otherwise creates a new one. Prevents duplicate test case creation.
        """
        pass

    @abstractmethod
    async def sync_all_test_cases(
        self,
        test_cases: List[Dict[str, Any]],
        parent_work_item_id: Optional[str] = None,
        area_path: Optional[str] = None,
        project: Optional[str] = None,
        db=None
    ) -> Tuple[List[Dict[str, Any]], int, int, int]:
        """
        Synchronizes a list of test cases in batch.
        Returns: (updated_test_cases, synced_count, updated_count, failed_count)
        """
        pass
