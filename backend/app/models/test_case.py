from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.db.session import Base

class TestCaseRecord(Base):
    """
    Persisted test case record maintaining traceability to Azure DevOps User Stories
    and synchronizing with Azure DevOps Test Case work items.
    """
    __tablename__ = "test_cases"

    id = Column(String(50), primary_key=True, index=True)
    azure_work_item_id = Column(String(50), index=True, nullable=True)
    azure_test_case_id = Column(Integer, index=True, nullable=True)
    azure_project_id = Column(String(100), nullable=True)
    azure_area_path = Column(String(255), nullable=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    category = Column(String(50), nullable=False)
    priority = Column(String(50), default="Medium")
    scenario = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    preconditions = Column(Text, nullable=True)
    test_data = Column(Text, nullable=True)
    test_steps = Column(Text, nullable=False)  # JSON or newline-delimited steps
    expected_result = Column(Text, nullable=False)
    requirement_ref = Column(String(100), nullable=True)
    application_page = Column(String(255), nullable=True)
    application_link = Column(String(500), nullable=True)
    sync_status = Column(String(50), default="Not Synced")
    sync_message = Column(Text, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
