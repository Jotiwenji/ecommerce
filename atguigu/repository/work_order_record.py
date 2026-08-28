from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import TEXT, VARCHAR, BigInteger, DateTime, func

from atguigu.repository.base import Base


class WorkOrderRecord(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    work_order_no: Mapped[str] = mapped_column(VARCHAR(32), unique=True, nullable=False)
    sender_id: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    ticket_type: Mapped[str] = mapped_column(VARCHAR(16), nullable=False)
    order_id: Mapped[str] = mapped_column(VARCHAR(64), nullable=True)
    description: Mapped[str] = mapped_column(TEXT, nullable=True)
    status: Mapped[str] = mapped_column(VARCHAR(16), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
