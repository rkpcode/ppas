from sqlalchemy import Column, Integer, String
from app.core.database import Base

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact_phone = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
