from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, field_validator

from app.models import PowerType, VehicleCategory


class WeightComponentBase(BaseModel):
    powertrain_weight: float = Field(default=0, ge=0, description="动力系统重量（发动机/电机+变速箱）kg")
    battery_system_weight: float = Field(default=0, ge=0, description="动力电池系统重量 kg")
    intelligent_config_weight: float = Field(default=0, ge=0, description="智能化配置总重量 kg")
    body_chassis_reinforce_weight: float = Field(default=0, ge=0, description="车身与底盘强化重量 kg")
    sound_insulation_weight: float = Field(default=0, ge=0, description="隔音舒适件重量 kg")
    suspension_brake_weight: float = Field(default=0, ge=0, description="悬挂与制动系统重量 kg")
    interior_comfort_weight: float = Field(default=0, ge=0, description="内饰舒适性配置重量 kg")
    other_weight: float = Field(default=0, ge=0, description="其他重量 kg")

    intelligent_adas_weight: float = Field(default=0, ge=0, description="智能驾驶辅助系统重量 kg")
    intelligent_cockpit_weight: float = Field(default=0, ge=0, description="智能座舱系统重量 kg")
    intelligent_sensor_weight: float = Field(default=0, ge=0, description="传感器系统重量 kg")
    intelligent_connectivity_weight: float = Field(default=0, ge=0, description="网联系统重量 kg")

    remarks: Optional[str] = Field(default=None, max_length=500)


class WeightComponentCreate(WeightComponentBase):
    pass


class WeightComponentUpdate(WeightComponentBase):
    pass


class WeightComponentResponse(WeightComponentBase):
    id: int
    vehicle_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class WeightComponentWithRatio(WeightComponentResponse):
    powertrain_ratio: float
    battery_system_ratio: float
    intelligent_config_ratio: float
    body_chassis_reinforce_ratio: float
    sound_insulation_ratio: float
    suspension_brake_ratio: float
    interior_comfort_ratio: float
    other_ratio: float

    intelligent_adas_ratio: float
    intelligent_cockpit_ratio: float
    intelligent_sensor_ratio: float
    intelligent_connectivity_ratio: float

    main_weight_contributor: str
    main_weight_contributor_value: float
    main_weight_contributor_ratio: float


class VehicleBase(BaseModel):
    model_config = {"protected_namespaces": ()}

    brand: str = Field(..., max_length=100, description="品牌")
    model: str = Field(..., max_length=100, description="型号")
    model_year: Optional[int] = Field(default=None, description="年款")
    category: VehicleCategory = Field(..., description="车型类别")
    power_type: PowerType = Field(..., description="动力类型")
    curb_weight: float = Field(..., gt=0, description="整备质量 kg")
    description: Optional[str] = Field(default=None, max_length=500)


class VehicleCreate(VehicleBase):
    weight_component: Optional[WeightComponentCreate] = None


class VehicleUpdate(BaseModel):
    model_config = {"protected_namespaces": ()}

    brand: Optional[str] = Field(default=None, max_length=100)
    model: Optional[str] = Field(default=None, max_length=100)
    model_year: Optional[int] = None
    category: Optional[VehicleCategory] = None
    power_type: Optional[PowerType] = None
    curb_weight: Optional[float] = Field(default=None, gt=0)
    description: Optional[str] = Field(default=None, max_length=500)


class VehicleResponse(VehicleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class VehicleWithWeight(VehicleResponse):
    weight_component: Optional[WeightComponentWithRatio] = None


class VehicleListItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    id: int
    brand: str
    model: str
    model_year: Optional[int]
    category: VehicleCategory
    power_type: PowerType
    curb_weight: float
    battery_ratio: Optional[float] = None
    main_contributor: Optional[str] = None
    main_contributor_ratio: Optional[float] = None


class VehicleComparisonItem(BaseModel):
    name: str
    power_type: PowerType
    curb_weight: float
    weight_diff: float

    powertrain_weight: float
    powertrain_diff: float
    powertrain_ratio: float
    battery_system_weight: float
    battery_system_diff: float
    battery_system_ratio: float
    intelligent_config_weight: float
    intelligent_config_diff: float
    intelligent_config_ratio: float
    body_chassis_reinforce_weight: float
    body_chassis_reinforce_diff: float
    body_chassis_reinforce_ratio: float
    sound_insulation_weight: float
    sound_insulation_diff: float
    sound_insulation_ratio: float
    suspension_brake_weight: float
    suspension_brake_diff: float
    suspension_brake_ratio: float
    interior_comfort_weight: float
    interior_comfort_diff: float
    interior_comfort_ratio: float
    other_weight: float
    other_diff: float
    other_ratio: float


class VehicleComparisonResponse(BaseModel):
    vehicle1: VehicleComparisonItem
    vehicle2: VehicleComparisonItem
    weight_diff_summary: Dict[str, float]
    biggest_diff_item: str
    biggest_diff_value: float
    comparison_type: str
    base_vehicle_is_vehicle1: bool
    analysis_summary: str


class CategoryStatsItem(BaseModel):
    category: VehicleCategory
    vehicle_count: int
    avg_curb_weight: float
    avg_battery_system_ratio: float
    avg_intelligent_config_ratio: float
    avg_body_chassis_reinforce_ratio: float
    avg_sound_insulation_ratio: float
    avg_powertrain_ratio: float


class CategoryStatsResponse(BaseModel):
    total_vehicles: int
    by_power_type: Dict[str, int]
    by_category: List[CategoryStatsItem]
    overall_avg_battery_ratio: float
    overall_avg_intelligent_ratio: float


class YearlyWeightItem(BaseModel):
    model_year: int
    curb_weight: float
    battery_system_weight: float
    battery_system_ratio: float
    intelligent_config_weight: float
    intelligent_config_ratio: float
    body_chassis_reinforce_weight: float
    body_chassis_reinforce_ratio: float
    powertrain_weight: float
    powertrain_ratio: float
    interior_comfort_weight: float
    interior_comfort_ratio: float
    suspension_brake_weight: float
    suspension_brake_ratio: float
    sound_insulation_weight: float
    sound_insulation_ratio: float
    other_weight: float
    other_ratio: float


class YearlyChangeItem(BaseModel):
    model_year: int
    curb_weight_change: float
    battery_system_weight_change: float
    intelligent_config_weight_change: float
    body_chassis_reinforce_weight_change: float
    powertrain_weight_change: float
    interior_comfort_weight_change: float
    suspension_brake_weight_change: float
    sound_insulation_weight_change: float
    other_weight_change: float


class ModelYearEvolutionResponse(BaseModel):
    brand: str
    model: str
    total_years: int
    year_range: str
    yearly_data: List[YearlyWeightItem]
    yearly_changes: List[YearlyChangeItem]
    total_curb_weight_change: float
    total_battery_system_change: float
    total_intelligent_config_change: float
    total_body_chassis_reinforce_change: float
    total_powertrain_change: float
    biggest_weight_gain_contributor: str
    biggest_weight_gain_value: float
    analysis_summary: str


class WeightGainContributionItem(BaseModel):
    component: str
    weight_diff: float
    contribution_percent: float
    description: str


class WeightGainAttributionResponse(BaseModel):
    target_vehicle: Dict[str, str]
    baseline_vehicle: Dict[str, str]
    total_weight_diff: float
    contributions: List[WeightGainContributionItem]
    top_contributor: str
    top_contributor_weight: float
    top_contributor_percent: float
    analysis_summary: str
    weight_diff_breakdown: Dict[str, float]


class ComponentRankingItem(BaseModel):
    rank: int
    brand: str
    model: str
    model_year: int
    category: VehicleCategory
    power_type: PowerType
    component_weight: float
    component_ratio: float
    curb_weight: float
    description: Optional[str] = None


class ComponentRankingResponse(BaseModel):
    component_name: str
    component_key: str
    total_vehicles: int
    ranking: List[ComponentRankingItem]
    max_weight: float
    min_weight: float
    avg_weight: float
    median_weight: float
