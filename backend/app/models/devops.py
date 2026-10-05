from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Area(Base):
    __tablename__ = "areas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    parent_id = Column(Integer, ForeignKey("areas.id"), nullable=True)

    application = relationship("Application", backref="areas")
    parent = relationship("Area", remote_side=[id], backref="children")
    user_stories = relationship("UserStory", back_populates="area", cascade="all, delete-orphan")


class UserStory(Base):
    __tablename__ = "user_stories"

    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    state = Column(String(50), default="Active")
    assigned_to = Column(String(100), default="QA Team")
    area_id = Column(Integer, ForeignKey("areas.id"), nullable=False)

    area = relationship("Area", back_populates="user_stories")
    acceptance_criteria = relationship("AcceptanceCriteria", back_populates="user_story", cascade="all, delete-orphan")


class AcceptanceCriteria(Base):
    __tablename__ = "acceptance_criteria"

    id = Column(String(50), primary_key=True, index=True)
    user_story_id = Column(String(50), ForeignKey("user_stories.id"), nullable=False)
    criteria_number = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    user_story = relationship("UserStory", back_populates="acceptance_criteria")
