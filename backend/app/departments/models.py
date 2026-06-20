from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)

    name_el = Column(String(255), nullable=False)
    name_en = Column(String(255), nullable=True)

    department_type = Column(String(50), nullable=False, default="DEPARTMENT")
    city = Column(String(100), nullable=True)
    website_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    institution = relationship(
        "Institution",
        back_populates="departments"
    )