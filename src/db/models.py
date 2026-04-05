from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    subscription_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FifaAlert(Base):
    __tablename__ = "fifa_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False) # ForeignKey omitted in SQLite simple setup
    product_code = Column(String, nullable=False) # ej ARG_GROUP, ARG_KNOCKOUT, FINAL
    ticket_category = Column(String, nullable=True) # ej FMT_P
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint('user_id', 'product_code', name='uix_user_product'),)


class AuditLog(Base):
    """Mantiene trazabilidad de las alertas enviadas para tu análisis de datos"""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    alert_id = Column(Integer, nullable=True)
    product_code = Column(String, nullable=False)
    message_sent = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
