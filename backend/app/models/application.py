from sqlalchemy import Column, Integer, String, Text
from app.db.session import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, unique=True, index=True)
    code = Column(String(50), nullable=False, unique=True)
    domain = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    default_url = Column(String(255), nullable=True)
    business_rules = Column(Text, nullable=True)
    user_roles = Column(Text, nullable=True)
    key_modules = Column(Text, nullable=True)
