from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, crud
from app.models import PowerType, VehicleCategory

router = APIRouter(prefix="/vehicles", tags=["车辆管理"])


@router.post("", response_model=schemas.VehicleResponse, summary="新增车辆")
def create_vehicle(vehicle_in: schemas.VehicleCreate, db: Session = Depends(get_db)):
    db_vehicle = crud.create_vehicle(db, vehicle_in)
    return db_vehicle


@router.get("", response_model=List[schemas.VehicleListItem], summary="获取车辆列表")
def get_vehicles(
    skip: int = Query(0, description="跳过数量"),
    limit: int = Query(100, description="返回数量", le=200),
    brand: Optional[str] = Query(None, description="品牌筛选"),
    category: Optional[VehicleCategory] = Query(None, description="车型类别筛选"),
    power_type: Optional[PowerType] = Query(None, description="动力类型筛选"),
    sort_by: Optional[str] = Query(
        "battery_ratio_desc",
        description="排序方式",
        enum=["battery_ratio_desc", "battery_ratio_asc", "curb_weight_desc", "curb_weight_asc"]
    ),
    db: Session = Depends(get_db)
):
    from app.services import get_vehicle_list_with_summary
    return get_vehicle_list_with_summary(db, skip, limit, brand, category, power_type, sort_by)


@router.get("/{vehicle_id}", response_model=schemas.VehicleWithWeight, summary="获取车辆详情及重量构成")
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = crud.get_vehicle_with_weight(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="车辆不存在")
    return vehicle


@router.put("/{vehicle_id}", response_model=schemas.VehicleResponse, summary="更新车辆信息")
def update_vehicle(
    vehicle_id: int,
    vehicle_in: schemas.VehicleUpdate,
    db: Session = Depends(get_db)
):
    db_vehicle = crud.update_vehicle(db, vehicle_id, vehicle_in)
    if not db_vehicle:
        raise HTTPException(status_code=404, detail="车辆不存在")
    return db_vehicle


@router.delete("/{vehicle_id}", summary="删除车辆")
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    success = crud.delete_vehicle(db, vehicle_id)
    if not success:
        raise HTTPException(status_code=404, detail="车辆不存在")
    return {"message": "删除成功"}


@router.post("/{vehicle_id}/weight", response_model=schemas.WeightComponentResponse, summary="创建/更新车辆重量构成")
def create_or_update_weight(
    vehicle_id: int,
    weight_in: schemas.WeightComponentCreate,
    db: Session = Depends(get_db)
):
    db_weight = crud.create_weight_component(db, vehicle_id, weight_in)
    if not db_weight:
        raise HTTPException(status_code=404, detail="车辆不存在")
    return db_weight
