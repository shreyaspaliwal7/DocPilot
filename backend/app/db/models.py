from datetime import datetime
from app.config import settings
try:
  from pgvector.sqlalchemy import Vector
except ImportError:
  from sqlalchemy.types import UserDefinedType

  class Vector(UserDefinedType):
    def __init__(self, dim):
      self.dim = dim
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Document(Base):
  __tablename__ = "documents"

  id = Column(Integer, primary_key=True, index=True)
  filename = Column(String(255), nullable=False)
  file_size = Column(Integer, nullable=False)
  chunk_count = Column(Integer, default=0)
  uploaded_at = Column(DateTime, default=datetime.utcnow)

  chunks = relationship(
      "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
  )


class DocumentChunk(Base):
  __tablename__ = "document_chunks"

  id = Column(Integer, primary_key=True, index=True)
  document_id = Column(
      Integer,
      ForeignKey("documents.id", ondelete="CASCADE"),
      nullable=False,
      index=True,
  )
  page_number = Column(Integer, nullable=False)
  chunk_index = Column(Integer, nullable=False)
  content = Column(Text, nullable=False)
  embedding = Column(Vector(settings.embedding_dim), nullable=False)

  document = relationship("Document", back_populates="chunks")


class Customer(Base):
  __tablename__ = "customers"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(String(100), nullable=False)
  email = Column(String(100), unique=True, nullable=False)
  city = Column(String(100), nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow)

  orders = relationship("Order", back_populates="customer")


class Product(Base):
  __tablename__ = "products"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(String(100), nullable=False)
  category = Column(String(50), nullable=False)
  price = Column(Float, nullable=False)
  stock = Column(Integer, nullable=False)

  order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
  __tablename__ = "orders"

  id = Column(Integer, primary_key=True, index=True)
  customer_id = Column(
      Integer, ForeignKey("customers.id"), nullable=False, index=True
  )
  status = Column(String(20), nullable=False)
  total_amount = Column(Float, nullable=False)
  order_date = Column(DateTime, default=datetime.utcnow)

  customer = relationship("Customer", back_populates="orders")
  items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
  __tablename__ = "order_items"

  id = Column(Integer, primary_key=True, index=True)
  order_id = Column(
      Integer, ForeignKey("orders.id"), nullable=False, index=True
  )
  product_id = Column(
      Integer, ForeignKey("products.id"), nullable=False, index=True
  )
  quantity = Column(Integer, nullable=False)
  unit_price = Column(Float, nullable=False)

  order = relationship("Order", back_populates="items")
  product = relationship("Product", back_populates="order_items")


class RequestLog(Base):
  __tablename__ = "request_logs"

  id = Column(Integer, primary_key=True, index=True)
  timestamp = Column(DateTime, default=datetime.utcnow, index=True)
  masked_question = Column(Text, nullable=False)
  tools_used = Column(String(255), default="")
  latency = Column(Float, nullable=False, default=0.0)
  input_tokens = Column(Integer, default=0)
  output_tokens = Column(Integer, default=0)
  estimated_cost = Column(Float, default=0.0)
  success = Column(Boolean, default=True)
  is_fallback = Column(Boolean, default=False)
  error_type = Column(String(50), nullable=True)
  is_not_found = Column(Boolean, default=False)
