from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.core.database import Base

class Medicine(Base):
    __tablename__ = "medicines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    generic_name = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    category = Column(String, nullable=True)
    unit_price = Column(Numeric(10, 2), nullable=False)
    is_schedule_h = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    batches = relationship("Batch", back_populates="medicine", cascade="all, delete-orphan")
    sale_items = relationship("SaleItem", back_populates="medicine")

class Batch(Base):
    __tablename__ = "batches"
    
    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    batch_number = Column(String, nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    expiry_date = Column(Date, nullable=False)
    received_date = Column(Date, default=date.today)
    
    medicine = relationship("Medicine", back_populates="batches")
    sale_items = relationship("SaleItem", back_populates="batch")
