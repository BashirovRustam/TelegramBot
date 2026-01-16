from pydantic import BaseModel, Field


class MasterServiceCreate(BaseModel):
    """Схема для создания связи мастера с услугой"""
    master_id: int = Field(..., description="Идентификатор мастера")
    service_id: int = Field(..., description="Идентификатор услуги")


class MasterServiceUpdate(BaseModel):
    """Схема для обновления связи мастера с услугой"""
    master_id: int = Field(..., description="Идентификатор мастера")
    service_id: int = Field(..., description="Идентификатор услуги")


class MasterServiceRead(BaseModel):
    """Схема для вывода информации о связи мастера с услугой"""
    master_id: int = Field(..., description="Идентификатор мастера")
    service_id: int = Field(..., description="Идентификатор услуги")

    class Config:
        from_attributes = True
