from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    name_el = Column(String(255), nullable=False, unique=True)
    name_en = Column(String(255), nullable=True)
    short_name = Column(String(50), nullable=True)
    institution_type = Column(String(50), nullable=False, default="UNIVERSITY")
    country = Column(String(100), nullable=False, default="Greece")
    city = Column(String(100), nullable=True)
    website_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    departments = relationship(
        "Department",
        back_populates="institution"
    )