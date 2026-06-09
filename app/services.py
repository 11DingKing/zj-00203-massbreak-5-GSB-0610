from typing import List, Optional, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models, schemas, crud
from app.models import PowerType, VehicleCategory
from app.calculations import (
    WEIGHT_COMPONENT_NAMES,
    WEIGHT_COMPONENT_DETAILS,
    calc_ratio,
    find_main_weight_contributor,
    create_comparison_item,
    build_weight_diff_summary,
    find_biggest_diff_item,
    calc_weight_gain_contribution,
    calc_avg_ratio_for_vehicles
)


def get_vehicle_list_with_summary(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    brand: Optional[str] = None,
    category: Optional[VehicleCategory] = None,
    power_type: Optional[PowerType] = None,
    sort_by: Optional[str] = "battery_ratio_desc"
) -> List[schemas.VehicleListItem]:
    vehicles = crud.get_vehicles(db, skip, limit, brand, category, power_type)
    result = []

    for vehicle in vehicles:
        item = schemas.VehicleListItem(
            id=vehicle.id,
            brand=vehicle.brand,
            model=vehicle.model,
            model_year=vehicle.model_year,
            category=vehicle.category,
            power_type=vehicle.power_type,
            curb_weight=vehicle.curb_weight
        )

        if vehicle.weight_component:
            main_name, _, main_ratio = find_main_weight_contributor(
                vehicle.weight_component, vehicle.curb_weight
            )
            battery_ratio = calc_ratio(
                vehicle.weight_component.battery_system_weight, vehicle.curb_weight
            )

            item.battery_ratio = battery_ratio
            item.main_contributor = main_name
            item.main_contributor_ratio = main_ratio

        result.append(item)

    if sort_by == "battery_ratio_desc":
        result.sort(key=lambda x: (x.battery_ratio is not None, x.battery_ratio), reverse=True)
    elif sort_by == "battery_ratio_asc":
        result.sort(key=lambda x: (x.battery_ratio is None, x.battery_ratio))
    elif sort_by == "curb_weight_desc":
        result.sort(key=lambda x: x.curb_weight, reverse=True)
    elif sort_by == "curb_weight_asc":
        result.sort(key=lambda x: x.curb_weight)

    return result


def _build_comparison_response(
    base_vehicle: models.Vehicle,
    compare_vehicle: models.Vehicle,
    base_wc: models.WeightComponent,
    compare_wc: models.WeightComponent
) -> schemas.VehicleComparisonResponse:
    vehicle1_item = create_comparison_item(base_vehicle, base_wc, base_vehicle, base_wc, True)
    vehicle2_item = create_comparison_item(compare_vehicle, compare_wc, base_vehicle, base_wc, False)

    weight_diff_summary = build_weight_diff_summary(base_wc, compare_wc)
    biggest_diff_item, biggest_diff_value = find_biggest_diff_item(base_wc, compare_wc)

    comparison_type = f"{base_vehicle.power_type.value}_vs_{compare_vehicle.power_type.value}"

    return schemas.VehicleComparisonResponse(
        vehicle1=vehicle1_item,
        vehicle2=vehicle2_item,
        weight_diff_summary=weight_diff_summary,
        biggest_diff_item=biggest_diff_item,
        biggest_diff_value=biggest_diff_value,
        comparison_type=comparison_type,
        base_vehicle_is_vehicle1=True
    )


def compare_fuel_ev_by_brand_model(
    db: Session,
    brand: str,
    model: str
) -> Optional[schemas.VehicleComparisonResponse]:
    vehicles = crud.get_vehicles_by_brand_model(db, brand, model)
    if len(vehicles) < 2:
        return None

    fuel_vehicles = [v for v in vehicles if v.power_type == PowerType.FUEL and v.weight_component]
    ev_vehicles = [v for v in vehicles if v.power_type == PowerType.EV and v.weight_component]

    if not fuel_vehicles or not ev_vehicles:
        return None

    fuel_vehicle = fuel_vehicles[0]
    ev_vehicle = ev_vehicles[0]

    return _build_comparison_response(
        fuel_vehicle, ev_vehicle,
        fuel_vehicle.weight_component, ev_vehicle.weight_component
    )


def compare_vehicles_by_ids(
    db: Session,
    vehicle_id_1: int,
    vehicle_id_2: int
) -> Optional[schemas.VehicleComparisonResponse]:
    vehicle1 = crud.get_vehicle(db, vehicle_id_1)
    vehicle2 = crud.get_vehicle(db, vehicle_id_2)

    if not vehicle1 or not vehicle2:
        return None
    if not vehicle1.weight_component or not vehicle2.weight_component:
        return None

    return _build_comparison_response(
        vehicle1, vehicle2,
        vehicle1.weight_component, vehicle2.weight_component
    )


def get_category_statistics(db: Session) -> schemas.CategoryStatsResponse:
    total_vehicles = db.query(func.count(models.Vehicle.id)).scalar() or 0

    by_power_type_counts = db.query(
        models.Vehicle.power_type,
        func.count(models.Vehicle.id)
    ).group_by(models.Vehicle.power_type).all()

    by_power_type = {pt.value: cnt for pt, cnt in by_power_type_counts}

    all_ev_vehicles = db.query(models.Vehicle).filter(
        models.Vehicle.power_type == PowerType.EV
    ).all()

    ev_vehicles = [v for v in all_ev_vehicles if v.weight_component is not None]

    overall_avg_battery_ratio = calc_avg_ratio_for_vehicles(ev_vehicles, "battery_system_weight")
    overall_avg_intelligent_ratio = calc_avg_ratio_for_vehicles(ev_vehicles, "intelligent_config_weight")

    category_results = []
    for category in VehicleCategory:
        all_cat_vehicles = db.query(models.Vehicle).filter(
            models.Vehicle.category == category
        ).all()

        cat_vehicles = [v for v in all_cat_vehicles if v.weight_component is not None]

        if not cat_vehicles:
            continue

        cat_count = len(cat_vehicles)
        total_curb_weight = sum(v.curb_weight for v in cat_vehicles)
        avg_curb_weight = round(total_curb_weight / cat_count, 1)

        category_results.append(schemas.CategoryStatsItem(
            category=category,
            vehicle_count=cat_count,
            avg_curb_weight=avg_curb_weight,
            avg_battery_system_ratio=calc_avg_ratio_for_vehicles(cat_vehicles, "battery_system_weight"),
            avg_intelligent_config_ratio=calc_avg_ratio_for_vehicles(cat_vehicles, "intelligent_config_weight"),
            avg_body_chassis_reinforce_ratio=calc_avg_ratio_for_vehicles(cat_vehicles, "body_chassis_reinforce_weight"),
            avg_sound_insulation_ratio=calc_avg_ratio_for_vehicles(cat_vehicles, "sound_insulation_weight"),
            avg_powertrain_ratio=calc_avg_ratio_for_vehicles(cat_vehicles, "powertrain_weight")
        ))

    return schemas.CategoryStatsResponse(
        total_vehicles=total_vehicles,
        by_power_type=by_power_type,
        by_category=category_results,
        overall_avg_battery_ratio=overall_avg_battery_ratio,
        overall_avg_intelligent_ratio=overall_avg_intelligent_ratio
    )


def get_highest_battery_ratio_vehicle(db: Session) -> Optional[schemas.VehicleWithWeight]:
    all_ev_vehicles = db.query(models.Vehicle).filter(
        models.Vehicle.power_type == PowerType.EV
    ).all()

    ev_vehicles = [v for v in all_ev_vehicles if v.weight_component is not None]

    if not ev_vehicles:
        return None

    max_ratio_vehicle = None
    max_ratio = -1

    for v in ev_vehicles:
        if v.curb_weight > 0:
            ratio = calc_ratio(v.weight_component.battery_system_weight, v.curb_weight)
            if ratio > max_ratio:
                max_ratio = ratio
                max_ratio_vehicle = v

    if max_ratio_vehicle:
        return crud.get_vehicle_with_weight(db, max_ratio_vehicle.id)

    return None


def get_model_year_evolution(
    db: Session,
    brand: str,
    model: str
) -> Optional[schemas.ModelYearEvolutionResponse]:
    vehicles = crud.get_vehicles_by_brand_model(db, brand, model)
    vehicles_with_weight = [v for v in vehicles if v.weight_component is not None and v.model_year is not None]

    if len(vehicles_with_weight) < 2:
        return None

    vehicles_with_weight.sort(key=lambda x: x.model_year)

    yearly_data = []
    for v in vehicles_with_weight:
        wc = v.weight_component
        yearly_data.append(schemas.YearlyWeightItem(
            model_year=v.model_year,
            curb_weight=v.curb_weight,
            battery_system_weight=wc.battery_system_weight,
            battery_system_ratio=calc_ratio(wc.battery_system_weight, v.curb_weight),
            intelligent_config_weight=wc.intelligent_config_weight,
            intelligent_config_ratio=calc_ratio(wc.intelligent_config_weight, v.curb_weight),
            body_chassis_reinforce_weight=wc.body_chassis_reinforce_weight,
            body_chassis_reinforce_ratio=calc_ratio(wc.body_chassis_reinforce_weight, v.curb_weight),
            powertrain_weight=wc.powertrain_weight,
            powertrain_ratio=calc_ratio(wc.powertrain_weight, v.curb_weight),
            interior_comfort_weight=wc.interior_comfort_weight,
            interior_comfort_ratio=calc_ratio(wc.interior_comfort_weight, v.curb_weight),
            suspension_brake_weight=wc.suspension_brake_weight,
            suspension_brake_ratio=calc_ratio(wc.suspension_brake_weight, v.curb_weight),
            sound_insulation_weight=wc.sound_insulation_weight,
            sound_insulation_ratio=calc_ratio(wc.sound_insulation_weight, v.curb_weight),
            other_weight=wc.other_weight,
            other_ratio=calc_ratio(wc.other_weight, v.curb_weight)
        ))

    yearly_changes = []
    for i in range(1, len(yearly_data)):
        prev = yearly_data[i - 1]
        curr = yearly_data[i]
        yearly_changes.append(schemas.YearlyChangeItem(
            model_year=curr.model_year,
            curb_weight_change=round(curr.curb_weight - prev.curb_weight, 1),
            battery_system_weight_change=round(curr.battery_system_weight - prev.battery_system_weight, 1),
            intelligent_config_weight_change=round(curr.intelligent_config_weight - prev.intelligent_config_weight, 1),
            body_chassis_reinforce_weight_change=round(curr.body_chassis_reinforce_weight - prev.body_chassis_reinforce_weight, 1),
            powertrain_weight_change=round(curr.powertrain_weight - prev.powertrain_weight, 1),
            interior_comfort_weight_change=round(curr.interior_comfort_weight - prev.interior_comfort_weight, 1),
            suspension_brake_weight_change=round(curr.suspension_brake_weight - prev.suspension_brake_weight, 1),
            sound_insulation_weight_change=round(curr.sound_insulation_weight - prev.sound_insulation_weight, 1),
            other_weight_change=round(curr.other_weight - prev.other_weight, 1)
        ))

    first = yearly_data[0]
    last = yearly_data[-1]

    total_curb_weight_change = round(last.curb_weight - first.curb_weight, 1)
    total_battery_system_change = round(last.battery_system_weight - first.battery_system_weight, 1)
    total_intelligent_config_change = round(last.intelligent_config_weight - first.intelligent_config_weight, 1)
    total_body_chassis_reinforce_change = round(last.body_chassis_reinforce_weight - first.body_chassis_reinforce_weight, 1)
    total_powertrain_change = round(last.powertrain_weight - first.powertrain_weight, 1)

    changes = [
        ("动力电池系统", total_battery_system_change),
        ("智能化配置", total_intelligent_config_change),
        ("车身与底盘强化", total_body_chassis_reinforce_change),
        ("动力系统", total_powertrain_change),
        ("内饰舒适性配置", round(last.interior_comfort_weight - first.interior_comfort_weight, 1)),
        ("悬挂与制动系统", round(last.suspension_brake_weight - first.suspension_brake_weight, 1)),
        ("隔音舒适件", round(last.sound_insulation_weight - first.sound_insulation_weight, 1)),
        ("其他", round(last.other_weight - first.other_weight, 1)),
    ]
    changes.sort(key=lambda x: x[1], reverse=True)
    biggest_contributor, biggest_value = changes[0]

    battery_gain_pct = round(total_battery_system_change / total_curb_weight_change * 100, 1) if total_curb_weight_change > 0 else 0
    intelligent_gain_pct = round(total_intelligent_config_change / total_curb_weight_change * 100, 1) if total_curb_weight_change > 0 else 0

    if biggest_contributor == "动力电池系统":
        analysis_summary = f"从{first.model_year}年到{last.model_year}年，{brand}{model}整备质量增加了{total_curb_weight_change}kg。电池增重是主要因素，贡献了{total_battery_system_change}kg（占比{battery_gain_pct}%），主要原因是续航里程提升带来的电池容量增加。智能化配置增加了{total_intelligent_config_change}kg（占比{intelligent_gain_pct}%），体现了智能驾驶和智能座舱配置的升级。"
    elif biggest_contributor == "智能化配置":
        analysis_summary = f"从{first.model_year}年到{last.model_year}年，{brand}{model}整备质量增加了{total_curb_weight_change}kg。智能化配置增重是主要因素，贡献了{total_intelligent_config_change}kg（占比{intelligent_gain_pct}%），主要原因是激光雷达、多Orin芯片、多屏智能座舱等配置的加入。电池系统增加了{total_battery_system_change}kg（占比{battery_gain_pct}%）。"
    else:
        analysis_summary = f"从{first.model_year}年到{last.model_year}年，{brand}{model}整备质量增加了{total_curb_weight_change}kg。{biggest_contributor}增重是主要因素，贡献了{biggest_value}kg。电池增加{total_battery_system_change}kg，智能化配置增加{total_intelligent_config_change}kg。"

    year_range = f"{first.model_year}-{last.model_year}"

    return schemas.ModelYearEvolutionResponse(
        brand=brand,
        model=model,
        total_years=len(yearly_data),
        year_range=year_range,
        yearly_data=yearly_data,
        yearly_changes=yearly_changes,
        total_curb_weight_change=total_curb_weight_change,
        total_battery_system_change=total_battery_system_change,
        total_intelligent_config_change=total_intelligent_config_change,
        total_body_chassis_reinforce_change=total_body_chassis_reinforce_change,
        total_powertrain_change=total_powertrain_change,
        biggest_weight_gain_contributor=biggest_contributor,
        biggest_weight_gain_value=biggest_value,
        analysis_summary=analysis_summary
    )


def get_weight_gain_attribution(
    db: Session,
    target_vehicle_id: int,
    baseline_vehicle_id: Optional[int] = None,
    category: Optional[VehicleCategory] = None
) -> Optional[schemas.WeightGainAttributionResponse]:
    target = crud.get_vehicle(db, target_vehicle_id)
    if not target or not target.weight_component:
        return None

    baseline = None
    if baseline_vehicle_id:
        baseline = crud.get_vehicle(db, baseline_vehicle_id)
        if not baseline or not baseline.weight_component:
            return None
    else:
        search_category = category if category else target.category
        category_vehicles = db.query(models.Vehicle).filter(
            models.Vehicle.category == search_category,
            models.Vehicle.weight_component is not None
        ).all()
        category_vehicles_with_weight = [v for v in category_vehicles if v.weight_component is not None]
        if not category_vehicles_with_weight:
            return None

        category_vehicles_with_weight.sort(key=lambda x: x.curb_weight)
        baseline = category_vehicles_with_weight[0]

    target_wc = target.weight_component
    baseline_wc = baseline.weight_component

    total_weight_diff = round(target.curb_weight - baseline.curb_weight, 1)

    component_diffs = calc_weight_gain_contribution(target_wc, baseline_wc, total_weight_diff)

    contributions = [
        schemas.WeightGainContributionItem(
            component=name,
            weight_diff=diff,
            contribution_percent=pct,
            description=desc
        )
        for name, diff, pct, desc in component_diffs
    ]

    top_contributor, top_contributor_weight, top_contributor_percent, _ = component_diffs[0]

    weight_diff_breakdown = {
        name: diff for name, diff, _, _ in component_diffs
    }

    if total_weight_diff > 0:
        analysis_summary = f"{target.brand}{target.model}({target.model_year}年)比{baseline.brand}{baseline.model}({baseline.model_year}年)重{total_weight_diff}kg。主要增重来自{top_contributor}，贡献了{top_contributor_weight}kg（占比{top_contributor_percent}%）。"

        battery_contribution = next((c for c in contributions if c.component == "动力电池系统"), None)
        intelligent_contribution = next((c for c in contributions if c.component == "智能化配置"), None)

        if battery_contribution and battery_contribution.weight_diff > 0:
            analysis_summary += f"其中电池系统重{battery_contribution.weight_diff}kg（占{battery_contribution.contribution_percent}%），"
        if intelligent_contribution and intelligent_contribution.weight_diff > 0:
            analysis_summary += f"智能化配置重{intelligent_contribution.weight_diff}kg（占{intelligent_contribution.contribution_percent}%），"

        analysis_summary += f"整体定位更高，配置更丰富是增重的核心原因。"
    elif total_weight_diff < 0:
        analysis_summary = f"{target.brand}{target.model}({target.model_year}年)比{baseline.brand}{baseline.model}({baseline.model_year}年)轻{abs(total_weight_diff)}kg，轻量化设计做得更好。"
    else:
        analysis_summary = f"两款车整备质量相同，但重量分布可能不同。"

    return schemas.WeightGainAttributionResponse(
        target_vehicle={
            "brand": target.brand,
            "model": target.model,
            "model_year": str(target.model_year),
            "category": target.category.value,
            "power_type": target.power_type.value,
            "curb_weight": str(target.curb_weight)
        },
        baseline_vehicle={
            "brand": baseline.brand,
            "model": baseline.model,
            "model_year": str(baseline.model_year),
            "category": baseline.category.value,
            "power_type": baseline.power_type.value,
            "curb_weight": str(baseline.curb_weight)
        },
        total_weight_diff=total_weight_diff,
        contributions=contributions,
        top_contributor=top_contributor,
        top_contributor_weight=top_contributor_weight,
        top_contributor_percent=top_contributor_percent,
        analysis_summary=analysis_summary,
        weight_diff_breakdown=weight_diff_breakdown
    )


def get_component_ranking(
    db: Session,
    component_key: str,
    category: Optional[VehicleCategory] = None,
    power_type: Optional[PowerType] = None,
    limit: int = 20
) -> Optional[schemas.ComponentRankingResponse]:
    if component_key not in WEIGHT_COMPONENT_DETAILS:
        return None

    query = db.query(models.Vehicle).filter(
        models.Vehicle.weight_component is not None
    )

    if category:
        query = query.filter(models.Vehicle.category == category)
    if power_type:
        query = query.filter(models.Vehicle.power_type == power_type)

    vehicles = query.all()
    vehicles_with_weight = [v for v in vehicles if v.weight_component is not None]

    if not vehicles_with_weight:
        return None

    ranked_vehicles = []
    for v in vehicles_with_weight:
        component_weight = getattr(v.weight_component, component_key, 0)
        component_ratio = calc_ratio(component_weight, v.curb_weight)
        ranked_vehicles.append((v, component_weight, component_ratio))

    ranked_vehicles.sort(key=lambda x: x[1], reverse=True)

    component_name = WEIGHT_COMPONENT_DETAILS[component_key]["name"]

    ranking = []
    for i, (v, comp_weight, comp_ratio) in enumerate(ranked_vehicles[:limit]):
        ranking.append(schemas.ComponentRankingItem(
            rank=i + 1,
            brand=v.brand,
            model=v.model,
            model_year=v.model_year or 0,
            category=v.category,
            power_type=v.power_type,
            component_weight=comp_weight,
            component_ratio=comp_ratio,
            curb_weight=v.curb_weight,
            description=v.description
        ))

    all_weights = [x[1] for x in ranked_vehicles]
    all_weights.sort()
    max_weight = round(all_weights[-1], 1)
    min_weight = round(all_weights[0], 1)
    avg_weight = round(sum(all_weights) / len(all_weights), 1)
    median_weight = round(all_weights[len(all_weights) // 2], 1) if len(all_weights) % 2 == 1 else round((all_weights[len(all_weights) // 2 - 1] + all_weights[len(all_weights) // 2]) / 2, 1)

    return schemas.ComponentRankingResponse(
        component_name=component_name,
        component_key=component_key,
        total_vehicles=len(ranked_vehicles),
        ranking=ranking,
        max_weight=max_weight,
        min_weight=min_weight,
        avg_weight=avg_weight,
        median_weight=median_weight
    )
