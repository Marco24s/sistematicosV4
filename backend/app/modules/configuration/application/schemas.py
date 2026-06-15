from pydantic import BaseModel, ConfigDict


class AircraftModelCreate(BaseModel):
    manufacturer: str
    code: str
    name: str


class AircraftModelRead(BaseModel):
    id: int
    manufacturer: str
    code: str
    name: str
    active: bool

    model_config = ConfigDict(from_attributes=True)


class EngineModelCreate(BaseModel):
    manufacturer: str
    code: str
    name: str


class EngineModelRead(BaseModel):
    id: int
    manufacturer: str
    code: str
    name: str
    active: bool

    model_config = ConfigDict(from_attributes=True)


class ComponentTypeCreate(BaseModel):
    code: str
    name: str
    requires_certificate: bool = True
    life_limit_hours: int | None = None
    life_limit_cycles: int | None = None
    calendar_limit_days: int | None = None


class ComponentTypeRead(BaseModel):
    id: int
    code: str
    name: str
    requires_certificate: bool
    life_limit_hours: int | None
    life_limit_cycles: int | None
    calendar_limit_days: int | None
    active: bool

    model_config = ConfigDict(from_attributes=True)
