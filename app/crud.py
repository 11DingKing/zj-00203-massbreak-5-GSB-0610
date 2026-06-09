from typing import List, Optional
from sqlalchemy.orm import Session

from app import models, schemas
from app.models import PowerType, VehicleCategory
from app.calculations import (
    WEIGHT_COMPONENT_NAMES,
    calc_weight_ratios,
    find_main_weight_contributor,
    convert_weight_with_ratio
)


def create_vehicle(db: Session, vehicle_in: schemas.VehicleCreate) -> models.Vehicle:
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

    return db_vehicle


def get_vehicle(db: Session, vehicle_id: int) -> Optional[models.Vehicle]:
    return db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()


def get_vehicles(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    brand: Optional[str] = None,
    category: Optional[VehicleCategory] = None,
    power_type: Optional[PowerType] = None
) -> List[models.Vehicle]:
    query = db.query(models.Vehicle)
    if brand:
        query = query.filter(models.Vehicle.brand.ilike(f"%{brand}%"))
    if category:
        query = query.filter(models.Vehicle.category == category)
    if power_type:
        query = query.filter(models.Vehicle.power_type == power_type)
    return query.offset(skip).limit(limit).all()


def get_vehicle_with_weight(db: Session, vehicle_id: int) -> Optional[schemas.VehicleWithWeight]:
    vehicle = get_vehicle(db, vehicle_id)
    if not vehicle:
        return None

    weight_component = vehicle.weight_component
    if not weight_component:
        return schemas.VehicleWithWeight(
            **{c.name: getattr(vehicle, c.name) for c in vehicle.__table__.columns},
            weight_component=None
        )

    weight_with_ratio = convert_weight_with_ratio(vehicle, weight_component)
    return schemas.VehicleWithWeight(
        **{c.name: getattr(vehicle, c.name) for c in vehicle.__table__.columns},
        weight_component=weight_with_ratio
    )


def update_vehicle(
    db: Session,
    vehicle_id: int,
    vehicle_in: schemas.VehicleUpdate
) -> Optional[models.Vehicle]:
    db_vehicle = get_vehicle(db, vehicle_id)
    if not db_vehicle:
        return None

    update_data = vehicle_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vehicle, field, value)

    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


def delete_vehicle(db: Session, vehicle_id: int) -> bool:
    db_vehicle = get_vehicle(db, vehicle_id)
    if not db_vehicle:
        return False

    if db_vehicle.weight_component:
        db.delete(db_vehicle.weight_component)

    db.delete(db_vehicle)
    db.commit()
    return True


def create_weight_component(
    db: Session,
    vehicle_id: int,
    weight_in: schemas.WeightComponentCreate
) -> Optional[models.WeightComponent]:
    vehicle = get_vehicle(db, vehicle_id)
    if not vehicle:
        return None

    existing = db.query(models.WeightComponent).filter(
        models.WeightComponent.vehicle_id == vehicle_id
    ).first()

    if existing:
        for field, value in weight_in.model_dump().items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    db_weight = models.WeightComponent(
        vehicle_id=vehicle_id,
        **weight_in.model_dump()
    )
    db.add(db_weight)
    db.commit()
    db.refresh(db_weight)
    return db_weight


def get_vehicles_by_brand_model(
    db: Session,
    brand: str,
    model: str
) -> List[models.Vehicle]:
    return db.query(models.Vehicle).filter(
        models.Vehicle.brand.ilike(f"%{brand}%"),
        models.Vehicle.model.ilike(f"%{model}%")
    ).all()
