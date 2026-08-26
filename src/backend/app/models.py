from datetime import date, datetime
from sqlalchemy import Date, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class UploadBatch(Base):
    __tablename__ = "upload_batches"
    id: Mapped[int] = mapped_column(primary_key=True)
    data_type: Mapped[str] = mapped_column(String(16))
    filename: Mapped[str] = mapped_column(String(255))
    file_hash: Mapped[str] = mapped_column(String(64), unique=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    row_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(16), default="processing")
    error_message: Mapped[str | None] = mapped_column(nullable=True)

class SalesRecord(Base):
    __tablename__ = "sales_records"
    __table_args__ = (UniqueConstraint("batch_id", "order_no", "sku"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("upload_batches.id"))
    created_date: Mapped[date] = mapped_column(Date, index=True)
    received_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    order_no: Mapped[str] = mapped_column(String(100))
    sku: Mapped[str] = mapped_column(String(100), index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantity: Mapped[float] = mapped_column(Float, default=0)
    returns: Mapped[float] = mapped_column(Float, default=0)
    gmv: Mapped[float] = mapped_column(Float, default=0)

class InventoryHistory(Base):
    __tablename__ = "inventory_history"
    __table_args__ = (UniqueConstraint("download_date", "sku", "region"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("upload_batches.id"))
    download_date: Mapped[date] = mapped_column(Date, index=True)
    sku: Mapped[str] = mapped_column(String(100), index=True)
    seller_sku: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product: Mapped[str | None] = mapped_column(String(255), nullable=True)
    color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    memory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    region: Mapped[str] = mapped_column(String(100), default="ALL")
    inventory: Mapped[float] = mapped_column(Float, default=0)

class TrafficHistory(Base):
    __tablename__ = "traffic_history"
    __table_args__ = (UniqueConstraint("record_date", "sku"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("upload_batches.id"))
    record_date: Mapped[date] = mapped_column(Date, index=True)
    sku: Mapped[str] = mapped_column(String(100), index=True)
    uv: Mapped[float | None] = mapped_column(Float, nullable=True)
    clicks: Mapped[float | None] = mapped_column(Float, nullable=True)
    impressions: Mapped[float | None] = mapped_column(Float, nullable=True)

class ProductMapping(Base):
    __tablename__ = "product_mappings"
    __table_args__ = (UniqueConstraint("xiaomi_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    xiaomi_id: Mapped[str] = mapped_column(String(100), index=True)
    sku: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    market_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    group: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    spu: Mapped[str | None] = mapped_column(String(255), nullable=True)
    color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    memory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
