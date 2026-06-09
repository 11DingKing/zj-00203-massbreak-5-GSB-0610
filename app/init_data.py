import json
import os
from pathlib import Path
from sqlalchemy.orm import Session
from app import models, schemas
from app.models import PowerType, VehicleCategory


DATA_DIR = Path(__file__).parent.parent / "data"
VEHICLES_JSON_PATH = DATA_DIR / "vehicles.json"


def load_vehicle_data():
    if not VEHICLES_JSON_PATH.exists():
        raise FileNotFoundError(f"Vehicle data file not found: {VEHICLES_JSON_PATH}")
    
    with open(VEHICLES_JSON_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    vehicle_data = []
    for item in raw_data:
        item_copy = item.copy()
        item_copy["category"] = VehicleCategory(item["category"])
        item_copy["power_type"] = PowerType(item["power_type"])
        vehicle_data.append(item_copy)
    
    return vehicle_data


def init_vehicle_data(db: Session):
    existing_count = db.query(models.Vehicle).count()
    if existing_count > 0:
        return

    vehicle_data = load_vehicle_data()

    for data in vehicle_data:
        weight_data = data.pop("weight_component")
        vehicle_in = schemas.VehicleCreate(**data)
        vehicle_in.weight_component = schemas.WeightComponentCreate(**weight_data)

        db_vehicle = models.Vehicle(
            brand=vehicle_in.brand,
            model=vehicle_in.model,
            model_year=vehicle_in.model_year,
            category=vehicle_in.category,
            power_type=vehicle_in.power_type,
            curb_weight=vehicle_in.curb_weight,
            description=vehicle_in.description
        )
        db.add(db_vehicle)
        db.commit()
        db.refresh(db_vehicle)

        if vehicle_in.weight_component:
            db_weight = models.WeightComponent(
                vehicle_id=db_vehicle.id,
                **vehicle_in.weight_component.model_dump()
            )
            db.add(db_weight)
            db.commit()
            db.refresh(db_weight)
