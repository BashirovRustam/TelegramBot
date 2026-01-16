from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from telegram_bot_app.db.base import Base


class MasterService(Base):
    __tablename__ = "master_services"

    master_id: Mapped[int] = mapped_column(Integer, ForeignKey("masters.id"), primary_key=True)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), primary_key=True)

    # Relationships
    master: Mapped["Master"] = relationship("Master", back_populates="master_services")
    service: Mapped["Service"] = relationship("Service", back_populates="master_services")

    def __repr__(self) -> str:
        return f"MasterService(master_id={self.master_id}, service_id={self.service_id})"
