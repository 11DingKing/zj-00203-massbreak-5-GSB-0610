from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class PowerType(str, enum.Enum):
    FUEL = "fuel"
    EV = "ev"
    HYBRID = "hybrid"
    PHEV = "phev"


class VehicleCategory(str, enum.Enum):
    COMPACT_CAR = "compact_car"
    MID_SIZE_CAR = "mid_size_car"
    FULL_SIZE_CAR = "full_size_car"
    SUV = "suv"
    LUXURY_SUV = "luxury_suv"
    MPV = "mpv"
    SPORTS_CAR = "sports_car"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(100), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)
    model_year = Column(Integer)
    category = Column(Enum(VehicleCategory), nullable=False, index=True)
    power_type = Column(Enum(PowerType), nullable=False, index=True)
    curb_weight = Column(Float, nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    weight_component = relationship("WeightComponent", back_populates="vehicle", uselist=False)


class WeightComponent(Base):
    __tablename__ = "weight_components"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), unique=True, nullable=False)

    powertrain_weight = Column(Float, nullable=False, default=0)
    battery_system_weight = Column(Float, nullable=False, default=0)
    intelligent_config_weight = Column(Float, nullable=False, default=0)
    body_chassis_reinforce_weight = Column(Float, nullable=False, default=0)
    sound_insulation_weight = Column(Float, nullable=False, default=0)
    suspension_brake_weight = Column(Float, nullable=False, default=0)
    interior_comfort_weight = Column(Float, nullable=False, default=0)
    other_weight = Column(Float, nullable=False, default=0)

    intelligent_adas_weight = Column(Float, nullable=False, default=0)
    intelligent_cockpit_weight = Column(Float, nullable=False, default=0)
    intelligent_sensor_weight = Column(Float, nullable=False, default=0)
    intelligent_connectivity_weight = Column(Float, nullable=False, default=0)

    remarks = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    vehicle = relationship("Vehicle", back_populates="weight_component")
