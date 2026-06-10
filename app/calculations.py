from typing import Dict, Tuple, List, Optional
from app import models, schemas
from app.models import PowerType, VehicleCategory


WEIGHT_COMPONENT_NAMES = {
    "powertrain_weight": "动力系统",
    "battery_system_weight": "动力电池系统",
    "intelligent_config_weight": "智能化配置",
    "body_chassis_reinforce_weight": "车身与底盘强化",
    "sound_insulation_weight": "隔音舒适件",
    "suspension_brake_weight": "悬挂与制动系统",
    "interior_comfort_weight": "内饰舒适性配置",
    "other_weight": "其他",
}

WEIGHT_COMPONENT_DETAILS = {
    "battery_system_weight": {
        "name": "动力电池系统",
        "description": "电池包、BMS、冷却系统等"
    },
    "intelligent_config_weight": {
        "name": "智能化配置",
        "description": "智能驾驶、智能座舱、传感器、网联系统等"
    },
    "body_chassis_reinforce_weight": {
        "name": "车身与底盘强化",
        "description": "车身结构加强、底盘架构、车架等"
    },
    "powertrain_weight": {
        "name": "动力系统",
        "description": "发动机/电机、变速箱、驱动系统等"
    },
    "interior_comfort_weight": {
        "name": "内饰舒适性配置",
        "description": "座椅、内饰板、氛围灯等"
    },
    "suspension_brake_weight": {
        "name": "悬挂与制动系统",
        "description": "悬挂系统、刹车系统、轮毂轮胎等"
    },
    "sound_insulation_weight": {
        "name": "隔音舒适件",
        "description": "隔音棉、密封件、降噪材料等"
    },
    "other_weight": {
        "name": "其他",
        "description": "未归类的其他部件"
    }
}

INTELLIGENT_SUB_COMPONENTS = [
    "intelligent_adas_weight",
    "intelligent_cockpit_weight",
    "intelligent_sensor_weight",
    "intelligent_connectivity_weight",
]

MAIN_COMPONENT_FIELDS = list(WEIGHT_COMPONENT_NAMES.keys())


def calc_ratio(weight: float, total: float) -> float:
    return round(weight / total * 100, 2) if total > 0 else 0


def calc_weight_ratios(
    weight_component: models.WeightComponent,
    curb_weight: float
) -> Dict[str, float]:
    ratios = {}
    for field in MAIN_COMPONENT_FIELDS:
        value = getattr(weight_component, field, 0)
        ratios[field.replace("_weight", "_ratio")] = calc_ratio(value, curb_weight)

    for field in INTELLIGENT_SUB_COMPONENTS:
        value = getattr(weight_component, field, 0)
        ratios[field.replace("_weight", "_ratio")] = calc_ratio(value, curb_weight)

    return ratios


def find_main_weight_contributor(
    weight_component: models.WeightComponent,
    curb_weight: float
) -> Tuple[str, float, float]:
    contributors = []
    for field, name in WEIGHT_COMPONENT_NAMES.items():
        value = getattr(weight_component, field, 0)
        contributors.append((name, value, calc_ratio(value, curb_weight)))

    contributors.sort(key=lambda x: x[1], reverse=True)
    return contributors[0]


def convert_weight_with_ratio(
    vehicle: models.Vehicle,
    weight_component: models.WeightComponent
) -> schemas.WeightComponentWithRatio:
    ratios = calc_weight_ratios(weight_component, vehicle.curb_weight)
    main_name, main_value, main_ratio = find_main_weight_contributor(
        weight_component, vehicle.curb_weight
    )

    return schemas.WeightComponentWithRatio(
        **{c.name: getattr(weight_component, c.name) for c in weight_component.__table__.columns},
        **ratios,
        main_weight_contributor=main_name,
        main_weight_contributor_value=main_value,
        main_weight_contributor_ratio=main_ratio
    )


def calc_component_diff(
    base_wc: models.WeightComponent,
    compare_wc: models.WeightComponent,
    field: str
) -> float:
    base_value = getattr(base_wc, field, 0)
    compare_value = getattr(compare_wc, field, 0)
    return compare_value - base_value


def create_comparison_item(
    vehicle: models.Vehicle,
    wc: models.WeightComponent,
    base_vehicle: models.Vehicle,
    base_wc: models.WeightComponent,
    is_base: bool
) -> schemas.VehicleComparisonItem:
    def diff(field: str) -> float:
        return 0 if is_base else calc_component_diff(base_wc, wc, field)

    return schemas.VehicleComparisonItem(
        name=f"{vehicle.brand} {vehicle.model}",
        power_type=vehicle.power_type,
        curb_weight=vehicle.curb_weight,
        weight_diff=0 if is_base else vehicle.curb_weight - base_vehicle.curb_weight,

        powertrain_weight=wc.powertrain_weight,
        powertrain_diff=diff("powertrain_weight"),
        powertrain_ratio=calc_ratio(wc.powertrain_weight, vehicle.curb_weight),
        battery_system_weight=wc.battery_system_weight,
        battery_system_diff=diff("battery_system_weight"),
        battery_system_ratio=calc_ratio(wc.battery_system_weight, vehicle.curb_weight),
        intelligent_config_weight=wc.intelligent_config_weight,
        intelligent_config_diff=diff("intelligent_config_weight"),
        intelligent_config_ratio=calc_ratio(wc.intelligent_config_weight, vehicle.curb_weight),
        body_chassis_reinforce_weight=wc.body_chassis_reinforce_weight,
        body_chassis_reinforce_diff=diff("body_chassis_reinforce_weight"),
        body_chassis_reinforce_ratio=calc_ratio(wc.body_chassis_reinforce_weight, vehicle.curb_weight),
        sound_insulation_weight=wc.sound_insulation_weight,
        sound_insulation_diff=diff("sound_insulation_weight"),
        sound_insulation_ratio=calc_ratio(wc.sound_insulation_weight, vehicle.curb_weight),
        suspension_brake_weight=wc.suspension_brake_weight,
        suspension_brake_diff=diff("suspension_brake_weight"),
        suspension_brake_ratio=calc_ratio(wc.suspension_brake_weight, vehicle.curb_weight),
        interior_comfort_weight=wc.interior_comfort_weight,
        interior_comfort_diff=diff("interior_comfort_weight"),
        interior_comfort_ratio=calc_ratio(wc.interior_comfort_weight, vehicle.curb_weight),
        other_weight=wc.other_weight,
        other_diff=diff("other_weight"),
        other_ratio=calc_ratio(wc.other_weight, vehicle.curb_weight)
    )


def build_weight_diff_summary(
    base_wc: models.WeightComponent,
    compare_wc: models.WeightComponent
) -> Dict[str, float]:
    return {
        "动力系统差异": calc_component_diff(base_wc, compare_wc, "powertrain_weight"),
        "动力电池系统差异": calc_component_diff(base_wc, compare_wc, "battery_system_weight"),
        "智能化配置差异": calc_component_diff(base_wc, compare_wc, "intelligent_config_weight"),
        "车身与底盘强化差异": calc_component_diff(base_wc, compare_wc, "body_chassis_reinforce_weight"),
        "隔音舒适件差异": calc_component_diff(base_wc, compare_wc, "sound_insulation_weight"),
        "悬挂与制动系统差异": calc_component_diff(base_wc, compare_wc, "suspension_brake_weight"),
        "内饰舒适性配置差异": calc_component_diff(base_wc, compare_wc, "interior_comfort_weight"),
        "其他差异": calc_component_diff(base_wc, compare_wc, "other_weight"),
    }


def find_biggest_diff_item(
    base_wc: models.WeightComponent,
    compare_wc: models.WeightComponent
) -> Tuple[str, float]:
    diff_items = [
        ("动力电池系统", calc_component_diff(base_wc, compare_wc, "battery_system_weight")),
        ("动力系统", calc_component_diff(base_wc, compare_wc, "powertrain_weight")),
        ("智能化配置", calc_component_diff(base_wc, compare_wc, "intelligent_config_weight")),
        ("车身与底盘强化", calc_component_diff(base_wc, compare_wc, "body_chassis_reinforce_weight")),
        ("隔音舒适件", calc_component_diff(base_wc, compare_wc, "sound_insulation_weight")),
        ("悬挂与制动系统", calc_component_diff(base_wc, compare_wc, "suspension_brake_weight")),
        ("内饰舒适性配置", calc_component_diff(base_wc, compare_wc, "interior_comfort_weight")),
        ("其他", calc_component_diff(base_wc, compare_wc, "other_weight")),
    ]
    diff_items.sort(key=lambda x: abs(x[1]), reverse=True)
    return diff_items[0]


def calc_weight_gain_contribution(
    target_wc: models.WeightComponent,
    baseline_wc: models.WeightComponent,
    total_weight_diff: float
) -> List[Tuple[str, float, float, str]]:
    component_diffs = []
    for key, details in WEIGHT_COMPONENT_DETAILS.items():
        target_weight = getattr(target_wc, key, 0)
        baseline_weight = getattr(baseline_wc, key, 0)
        diff = round(target_weight - baseline_weight, 1)
        contribution_pct = round(diff / total_weight_diff * 100, 1) if total_weight_diff != 0 else 0
        component_diffs.append((
            details["name"],
            diff,
            contribution_pct,
            details["description"]
        ))

    component_diffs.sort(key=lambda x: abs(x[1]), reverse=True)
    return component_diffs


def calc_avg_ratio_for_vehicles(
    vehicles: List[models.Vehicle],
    component_field: str
) -> float:
    ratios = []
    for v in vehicles:
        if v.curb_weight > 0 and v.weight_component:
            value = getattr(v.weight_component, component_field, 0)
            ratios.append(value / v.curb_weight * 100)
    return round(sum(ratios) / len(ratios), 2) if ratios else 0
