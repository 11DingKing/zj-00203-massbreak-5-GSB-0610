from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, services
from app.models import PowerType, VehicleCategory

router = APIRouter(prefix="/analysis", tags=["重量分析"])


@router.get("/highest-battery-ratio", response_model=schemas.VehicleWithWeight, summary="获取电池占比最高的车型")
def get_highest_battery_ratio(db: Session = Depends(get_db)):
    vehicle = services.get_highest_battery_ratio_vehicle(db)
    if not vehicle:
        raise HTTPException(status_code=404, detail="暂无数据")
    return vehicle


@router.get("/compare/brand-model", response_model=schemas.VehicleComparisonResponse, summary="按品牌型号对比油电版本")
def compare_by_brand_model(
    brand: str = Query(..., description="品牌名称"),
    model: str = Query(..., description="型号名称"),
    db: Session = Depends(get_db)
):
    result = services.compare_fuel_ev_by_brand_model(db, brand, model)
    if not result:
        raise HTTPException(status_code=404, detail="未找到对应品牌型号的油电版本对比数据，请确保品牌和型号同时存在燃油版和纯电版")
    return result


@router.get("/compare/ids", response_model=schemas.VehicleComparisonResponse, summary="按车辆ID对比两款车")
def compare_by_ids(
    vehicle_id_1: int = Query(..., description="第一款车ID"),
    vehicle_id_2: int = Query(..., description="第二款车ID"),
    db: Session = Depends(get_db)
):
    result = services.compare_vehicles_by_ids(db, vehicle_id_1, vehicle_id_2)
    if not result:
        raise HTTPException(status_code=404, detail="对比失败，请确保两款车都存在且都有重量构成数据")
    return result


@router.get("/statistics", response_model=schemas.CategoryStatsResponse, summary="按车型类别统计平均占比")
def get_statistics(db: Session = Depends(get_db)):
    return services.get_category_statistics(db)


@router.get("/weight-breakdown/{vehicle_id}", response_model=schemas.VehicleWithWeight, summary="获取单台车重量拆解")
def get_weight_breakdown(vehicle_id: int, db: Session = Depends(get_db)):
    from app import crud
    vehicle = crud.get_vehicle_with_weight(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="车辆不存在")
    return vehicle


@router.get("/model-year-evolution", response_model=schemas.ModelYearEvolutionResponse, summary="同一车型不同年款重量演变分析")
def get_model_year_evolution(
    brand: str = Query(..., description="品牌名称"),
    model: str = Query(..., description="型号名称"),
    db: Session = Depends(get_db)
):
    result = services.get_model_year_evolution(db, brand, model)
    if not result:
        raise HTTPException(status_code=404, detail="未找到足够的年款数据，请确保该车型至少有2个不同年款的数据")
    return result


@router.get("/weight-gain-attribution", response_model=schemas.WeightGainAttributionResponse, summary="单个车型增重归因分析")
def get_weight_gain_attribution(
    target_vehicle_id: int = Query(..., description="待分析车型ID"),
    baseline_vehicle_id: Optional[int] = Query(None, description="基准车型ID（可选，不填则自动选择同级别最轻车型）"),
    category: Optional[VehicleCategory] = Query(None, description="对比级别（可选，不填则使用目标车型级别）"),
    db: Session = Depends(get_db)
):
    result = services.get_weight_gain_attribution(db, target_vehicle_id, baseline_vehicle_id, category)
    if not result:
        raise HTTPException(status_code=404, detail="分析失败，请确保目标车型存在且有重量构成数据")
    return result


@router.get("/component-ranking", response_model=schemas.ComponentRankingResponse, summary="按部件跨车型横向排行")
def get_component_ranking(
    component_key: str = Query(..., description="部件字段名，可选：battery_system_weight, intelligent_config_weight, body_chassis_reinforce_weight, powertrain_weight, interior_comfort_weight, suspension_brake_weight, sound_insulation_weight, other_weight"),
    category: Optional[VehicleCategory] = Query(None, description="车型类别过滤"),
    power_type: Optional[PowerType] = Query(None, description="动力类型过滤"),
    limit: int = Query(20, description="返回排名数量", ge=1, le=100),
    db: Session = Depends(get_db)
):
    valid_components = list(services.WEIGHT_COMPONENT_DETAILS.keys())
    if component_key not in valid_components:
        raise HTTPException(status_code=400, detail=f"无效的部件字段名，可选值：{', '.join(valid_components)}")
    result = services.get_component_ranking(db, component_key, category, power_type, limit)
    if not result:
        raise HTTPException(status_code=404, detail="暂无数据")
    return result


@router.get("/available-components", response_model=List[dict], summary="获取可用的部件列表")
def get_available_components():
    return [
        {"key": key, "name": details["name"], "description": details["description"]}
        for key, details in services.WEIGHT_COMPONENT_DETAILS.items()
    ]
