# 汽车重量构成分析系统 - 架构与数据流转说明文档

## 一、系统整体架构

### 1.1 技术栈
```
┌─────────────────────────────────────────────────┐
│                  API 层 (FastAPI)               │
│  routers/vehicles.py  |  routers/analysis.py    │
├─────────────────────────────────────────────────┤
│              业务逻辑层 (services.py)            │
│  对比 | 统计 | 排行 | 演变 | 归因                │
├─────────────────────────────────────────────────┤
│          数据访问 + 占比核算层 (crud.py)         │
│  CRUD | 比例计算 | 主贡献项识别                  │
├─────────────────────────────────────────────────┤
│              数据模型层 (models.py)              │
│  Vehicle (车辆) | WeightComponent (重量构成)    │
├─────────────────────────────────────────────────┤
│                  SQLite 数据库                  │
└─────────────────────────────────────────────────┘
```

### 1.2 目录结构
```
app/
├── routers/
│   ├── vehicles.py      # 车辆管理接口（增删改查、重量录入）
│   └── analysis.py      # 重量分析接口（对比、统计、拆解等）
├── services.py          # 业务逻辑层（对比算法、统计算法等）
├── crud.py              # 数据访问层 + 占比核算核心逻辑
├── models.py            # SQLAlchemy 数据模型
├── schemas.py           # Pydantic 请求/响应模型
├── database.py          # 数据库连接配置
├── config.py            # 配置管理
├── init_data.py         # 初始化数据（40+款车型）
└── main.py              # 应用入口
```

---

## 二、核心数据模型

### 2.1 数据关系图

```
┌─────────────────────────────────────────────────────────────┐
│                        vehicles 表                          │
├────────────┬─────────────────┬──────────────────────────────┤
│ id         │ Integer         │ 主键                         │
│ brand      │ String(100)     │ 品牌                         │
│ model      │ String(100)     │ 型号                         │
│ model_year │ Integer         │ 年款                         │
│ category   │ Enum            │ 车型类别（7种）              │
│ power_type │ Enum            │ 动力类型（fuel/ev/hybrid/phev）│
│ curb_weight│ Float           │ 整备质量 (kg) ⭐             │
└────────────┴─────────────────┴──────────────────────────────┘
                              │
                              │ 1 : 1
                              │
┌─────────────────────────────────────────────────────────────┐
│                    weight_components 表                     │
├──────────────────────────────────┬────────┬─────────────────┤
│ id                               │ Integer│ 主键            │
│ vehicle_id                       │ Integer│ 外键 → vehicles │
├──────────────────────────────────┼────────┼─────────────────┤
│ 8大重量构成项 (kg)               │        │                 │
│ ├─ powertrain_weight             │ Float  │ 动力系统        │
│ ├─ battery_system_weight         │ Float  │ 动力电池系统 ⭐ │
│ ├─ intelligent_config_weight     │ Float  │ 智能化配置 ⭐   │
│ ├─ body_chassis_reinforce_weight │ Float  │ 车身底盘强化    │
│ ├─ sound_insulation_weight       │ Float  │ 隔音舒适件      │
│ ├─ suspension_brake_weight       │ Float  │ 悬挂制动系统    │
│ ├─ interior_comfort_weight       │ Float  │ 内饰舒适配置    │
│ └─ other_weight                  │ Float  │ 其他            │
├──────────────────────────────────┼────────┼─────────────────┤
│ 4大智能配置细分项 (kg)           │        │                 │
│ ├─ intelligent_adas_weight       │ Float  │ 智能驾驶辅助    │
│ ├─ intelligent_cockpit_weight    │ Float  │ 智能座舱        │
│ ├─ intelligent_sensor_weight     │ Float  │ 传感器系统      │
│ └─ intelligent_connectivity_weight│ Float │ 网联系统        │
└──────────────────────────────────┴────────┴─────────────────┘
```

### 2.2 关键数据说明

| 字段 | 说明 | 重要性 |
|------|------|--------|
| `curb_weight` | 整备质量，所有占比计算的基准 | ⭐⭐⭐ |
| `battery_system_weight` | 动力电池系统重量，油电差异核心 | ⭐⭐⭐ |
| `intelligent_config_weight` | 智能化配置总重量，含4个细分项 | ⭐⭐⭐ |

---

## 三、数据完整流转路径

### 3.1 数据流全景图

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                         数据录入阶段                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
                        ┌───────────────────────────────────┐
                        │  POST /api/v1/vehicles           │
                        │  录入车辆基本信息 + 重量构成       │
                        └─────────────┬─────────────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────────────┐
                        │  crud.create_vehicle()           │
                        │  写入 vehicles 表                │
                        │  写入 weight_components 表       │
                        └─────────────┬─────────────────────┘
                                      │
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                         占比核算阶段                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────────────┐
                        │  crud.calculate_weight_ratios()  │
                        │  各部件重量 ÷ 整备质量 × 100      │
                        │  得到 8 + 4 = 12 个占比值         │
                        └─────────────┬─────────────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────────────┐
                        │  crud.find_main_weight_contributor() │
                        │  遍历8大项，找出重量最大的那个     │
                        └─────────────┬─────────────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────────────┐
                        │  crud.convert_weight_with_ratio()│
                        │  组装成 WeightComponentWithRatio  │
                        └─────────────┬─────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│   单台车拆解展示     │   │   油电同款对比       │   │   类别统计汇总       │
│ GET /weight-breakdown│   │ GET /compare/brand  │   │ GET /statistics     │
└─────────┬───────────┘   └──────────┬──────────┘   └──────────┬──────────┘
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│ services 其他分析    │   │ services.compare_   │   │ services.get_       │
│ ・年款演变分析       │   │ fuel_ev_by_brand_   │   │ category_           │
│ ・增重归因分析       │   │ model()             │   │ statistics()        │
│ ・部件跨车型排行     │   │ services.compare_   │   │  按category分组     │
│                     │   │ vehicles_by_ids()   │   │  计算各维度平均值   │
└─────────────────────┘   └──────────┬──────────┘   └──────────┬──────────┘
                                      │                           │
                                      ▼                           ▼
                          ┌─────────────────────┐   ┌─────────────────────┐
                          │ 逐项计算差值         │   │ avg_battery_ratio   │
                          │ 识别最大差异项       │   │ avg_intelligent_    │
                          │ biggest_diff_item    │   │ ratio               │
                          └─────────────────────┘   └─────────────────────┘
```

### 3.2 阶段一：数据录入流程

**入口**：`POST /api/v1/vehicles`

```
请求体 (VehicleCreate):
├─ brand: "宝马"
├─ model: "i3 eDrive40L"
├─ model_year: 2024
├─ category: "mid_size_car"
├─ power_type: "ev"
├─ curb_weight: 2055  ← 整备质量基准
└─ weight_component: (WeightComponentCreate)
   ├─ powertrain_weight: 160
   ├─ battery_system_weight: 530
   ├─ intelligent_config_weight: 130
   ├─ body_chassis_reinforce_weight: 330
   ├─ sound_insulation_weight: 95
   ├─ suspension_brake_weight: 260
   ├─ interior_comfort_weight: 210
   ├─ other_weight: 340
   ├─ intelligent_adas_weight: 50
   ├─ intelligent_cockpit_weight: 55
   ├─ intelligent_sensor_weight: 18
   └─ intelligent_connectivity_weight: 7
```

**处理逻辑** (`crud.create_vehicle()` at `app/crud.py:67`):
1. 先写入 `vehicles` 表，获取车辆 ID
2. 再写入 `weight_components` 表，关联车辆 ID
3. 两表通过 `vehicle_id` 建立 1:1 关系

---

### 3.3 阶段二：占比核算流程

**核心函数**：`crud.calculate_weight_ratios()` at `app/crud.py:21`

**计算公式**：
```
部件占比 = (部件重量 ÷ 整备质量) × 100 （保留2位小数）
```

**代码逻辑**：
```python
# 8大主项遍历计算
for field in ["powertrain_weight", "battery_system_weight", ...]:
    value = getattr(weight_component, field, 0)
    ratios[field.replace("_weight", "_ratio")] = 
        round(value / curb_weight * 100, 2) if curb_weight > 0 else 0

# 4大智能细分项单独计算
ratios["intelligent_adas_ratio"] = 
    round(weight_component.intelligent_adas_weight / curb_weight * 100, 2)
...
```

**以宝马i3为例**（整备质量 2055kg）：
| 部件 | 重量(kg) | 占比计算 | 占比(%) |
|------|---------|---------|---------|
| 动力电池系统 | 530 | 530 ÷ 2055 × 100 | 25.79 |
| 动力系统 | 160 | 160 ÷ 2055 × 100 | 7.79 |
| 智能化配置 | 130 | 130 ÷ 2055 × 100 | 6.33 |
| 车身底盘强化 | 330 | 330 ÷ 2055 × 100 | 16.06 |
| ... | ... | ... | ... |

**主贡献项识别**：`crud.find_main_weight_contributor()` at `app/crud.py:38`
- 遍历8大项，按重量降序排序
- 返回重量最大的项：名称、重量、占比
- 宝马i3的主贡献项：动力电池系统 (530kg, 25.79%)

---

### 3.4 阶段三：分析输出流程

#### 3.4.1 单台车重量拆解

**接口**：`GET /api/v1/analysis/weight-breakdown/{id}`

**调用链**：
```
routers/analysis.py:49 → crud.get_vehicle_with_weight() → crud.convert_weight_with_ratio()
                                                          ↳ crud.calculate_weight_ratios()
                                                          ↳ crud.find_main_weight_contributor()
```

**输出结构** (`WeightComponentWithRatio`):
- 12个原始重量值
- 12个对应的占比值（`*_ratio`）
- `main_weight_contributor`: 最大贡献项名称
- `main_weight_contributor_value`: 最大贡献项重量
- `main_weight_contributor_ratio`: 最大贡献项占比

#### 3.4.2 油电同款逐项对比

**接口**：`GET /api/v1/analysis/compare/brand-model?brand=宝马&model=3系`

**调用链**：
```
routers/analysis.py:20 → services.compare_fuel_ev_by_brand_model()
                           ↳ crud.get_vehicles_by_brand_model()
                           ↳ 筛选燃油版和纯电版各1台
                           ↳ 逐项计算差值和占比
                           ↳ 识别最大差异项
```

**对比算法**（`services.compare_fuel_ev_by_brand_model()` at `app/services.py:59`）：

1. **基准选择**：燃油版为基准 (base)，纯电版为对比对象 (compare)

2. **逐项差值计算**：
   ```
   weight_diff = compare_value - base_value
   （正值表示纯电版更重，负值表示更轻）
   ```

3. **宝马3系 vs 宝马i3 对比示例**：

   | 项目 | 燃油版(kg) | 纯电版(kg) | 差值(kg) | 纯电版占比 |
   |------|-----------|-----------|---------|-----------|
   | 整备质量 | 1610 | 2055 | **+445** | - |
   | 动力系统 | 320 | 160 | -160 | 7.79% |
   | 动力电池 | 15 | 530 | **+515** | 25.79% |
   | 智能化配置 | 85 | 130 | +45 | 6.33% |
   | 车身底盘强化 | 260 | 330 | +70 | 16.06% |
   | 隔音舒适件 | 60 | 95 | +35 | 4.62% |
   | ... | ... | ... | ... | ... |

4. **最大差异项识别**：
   - 遍历所有差值，按绝对值降序排序
   - `biggest_diff_item = "动力电池系统"`
   - `biggest_diff_value = 515`

#### 3.4.3 按类别统计汇总

**接口**：`GET /api/v1/analysis/statistics`

**调用链**：
```
routers/analysis.py:44 → services.get_category_statistics()
                           ↳ 统计总车辆数
                           ↳ 按动力类型分组计数
                           ↳ 按车型类别分组（7类）
                             ↳ 每类计算：平均整备质量
                             ↳ 每类计算：各部件平均占比
                           ↳ 整体平均：电池占比、智能配置占比
```

**统计逻辑**（`services.get_category_statistics()` at `app/services.py:267`）：

1. **按车型类别分组**（7类：compact_car, mid_size_car, full_size_car, suv, luxury_suv, mpv, sports_car）

2. **每类内部计算**：
   ```python
   for v in category_vehicles:
       battery_ratios.append(battery_weight / curb_weight * 100)
       intelligent_ratios.append(intelligent_weight / curb_weight * 100)
       ...
   
   avg_battery_ratio = sum(battery_ratios) / len(battery_ratios)
   ```

3. **输出结构** (`CategoryStatsResponse`):
   - `total_vehicles`: 总车辆数
   - `by_power_type`: 各动力类型数量 {fuel: 12, ev: 25, ...}
   - `by_category`: 每类统计明细（平均重量、各维度平均占比）
   - `overall_avg_battery_ratio`: 所有纯电车平均电池占比
   - `overall_avg_intelligent_ratio`: 所有纯电车平均智能配置占比

---

## 四、核心模块职责与调用关系

### 4.1 模块职责划分

| 模块 | 主要职责 | 核心函数 | 所在文件 |
|------|---------|---------|---------|
| **重量明细模块** | 数据录入、查询、更新、删除 | `create_vehicle()`<br>`get_vehicle()`<br>`create_weight_component()` | `crud.py` |
| **占比核算模块** | 计算各部件占比、识别主贡献项 | `calculate_weight_ratios()`<br>`find_main_weight_contributor()`<br>`convert_weight_with_ratio()` | `crud.py` |
| **对比模块** | 油电同款对比、任意两车对比 | `compare_fuel_ev_by_brand_model()`<br>`compare_vehicles_by_ids()` | `services.py` |
| **类别统计模块** | 按车型类别统计平均占比 | `get_category_statistics()` | `services.py` |
| **扩展分析模块** | 年款演变、增重归因、部件排行 | `get_model_year_evolution()`<br>`get_weight_gain_attribution()`<br>`get_component_ranking()` | `services.py` |

### 4.2 模块调用关系图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              API Layer                                  │
│  ┌──────────────────────┐      ┌──────────────────────┐                │
│  │  routers/vehicles.py │      │  routers/analysis.py │                │
│  └──────────┬───────────┘      └──────────┬───────────┘                │
└─────────────┼─────────────────────────────┼────────────────────────────┘
              │                             │
              │ ┌───────────────────────────┘
              │ │
              ▼ ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Services Layer                                 │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  services.py                                                      │  │
│  │  ├─ get_vehicle_list_with_summary()  ←┐                           │  │
│  │  ├─ compare_fuel_ev_by_brand_model()   │  调用占比核算函数        │  │
│  │  ├─ compare_vehicles_by_ids()          │                           │  │
│  │  ├─ get_category_statistics()          │                           │  │
│  │  ├─ get_highest_battery_ratio_vehicle()│                           │  │
│  │  ├─ get_model_year_evolution()         │                           │  │
│  │  ├─ get_weight_gain_attribution()      │                           │  │
│  │  └─ get_component_ranking()            │                           │  │
│  └─────────────────────────────────────────┼───────────────────────────┘  │
                                            │
└───────────────────────────────────────────┼────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          CRUD + Calculation Layer                       │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  crud.py                                                          │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  占比核算核心                                                │  │  │
│  │  │  ├─ calculate_weight_ratios()                               │  │  │
│  │  │  ├─ find_main_weight_contributor()                          │  │  │
│  │  │  └─ convert_weight_with_ratio()  ←──────────────────────────┘  │  │
│  │  │                                                               │  │  │
│  │  │  数据访问                                                     │  │  │
│  │  │  ├─ create_vehicle()                                          │  │  │
│  │  │  ├─ get_vehicle()                                             │  │  │
│  │  │  ├─ get_vehicles()                                            │  │  │
│  │  │  ├─ get_vehicle_with_weight()                                 │  │  │
│  │  │  ├─ update_vehicle()                                          │  │  │
│  │  │  ├─ delete_vehicle()                                          │  │  │
│  │  │  ├─ create_weight_component()                                 │  │  │
│  │  │  └─ get_vehicles_by_brand_model()                             │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Data Model Layer                               │
│  ┌──────────────────┐          ┌──────────────────────┐                │
│  │  models.Vehicle  │◄─────────┤ models.WeightComponent │                │
│  │  (车辆基本信息)   │  1 : 1   │  (重量构成明细)       │                │
│  └──────────────────┘          └──────────────────────┘                │
└───────────────────────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          SQLite Database                                 │
│  ┌──────────────┐              ┌────────────────────┐                   │
│  │  vehicles    │              │ weight_components  │                   │
│  └──────────────┘              └────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.3 关键调用路径示例

**场景1：获取单台车重量拆解**
```
GET /api/v1/analysis/weight-breakdown/1
    ↓
routers/analysis.py:49 (get_weight_breakdown)
    ↓
crud.py:115 (get_vehicle_with_weight)
    ├─ 查 vehicles 表
    ├─ 查 weight_components 表（通过关系）
    └─ crud.py:51 (convert_weight_with_ratio)
        ├─ crud.py:21 (calculate_weight_ratios) → 计算12个占比
        └─ crud.py:38 (find_main_weight_contributor) → 识别主贡献项
```

**场景2：油电同款对比**
```
GET /api/v1/analysis/compare/brand-model?brand=宝马&model=3系
    ↓
routers/analysis.py:20 (compare_by_brand_model)
    ↓
services.py:59 (compare_fuel_ev_by_brand_model)
    ├─ crud.py:195 (get_vehicles_by_brand_model) → 查同品牌型号
    ├─ 筛选 fuel 和 ev 各1台
    ├─ 为每台车计算占比（calc_ratio 内部函数）
    ├─ 逐项计算差值
    └─ 识别 biggest_diff_item
```

**场景3：按类别统计**
```
GET /api/v1/analysis/statistics
    ↓
routers/analysis.py:44 (get_statistics)
    ↓
services.py:267 (get_category_statistics)
    ├─ 统计总车辆数
    ├─ 按动力类型分组计数
    ├─ 遍历7种车型类别
    │   └─ 每类计算：平均重量 + 各部件平均占比
    └─ 计算整体平均电池占比、智能配置占比
```

---

## 五、核心数据结构映射

### 5.1 重量构成字段映射表

| 数据库字段 | 中文名称 | 占比字段 |
|-----------|---------|---------|
| powertrain_weight | 动力系统 | powertrain_ratio |
| battery_system_weight | 动力电池系统 | battery_system_ratio |
| intelligent_config_weight | 智能化配置 | intelligent_config_ratio |
| body_chassis_reinforce_weight | 车身与底盘强化 | body_chassis_reinforce_ratio |
| sound_insulation_weight | 隔音舒适件 | sound_insulation_ratio |
| suspension_brake_weight | 悬挂与制动系统 | suspension_brake_ratio |
| interior_comfort_weight | 内饰舒适性配置 | interior_comfort_ratio |
| other_weight | 其他 | other_ratio |
| intelligent_adas_weight | 智能驾驶辅助 | intelligent_adas_ratio |
| intelligent_cockpit_weight | 智能座舱 | intelligent_cockpit_ratio |
| intelligent_sensor_weight | 传感器系统 | intelligent_sensor_ratio |
| intelligent_connectivity_weight | 网联系统 | intelligent_connectivity_ratio |

### 5.2 核心常量定义

**`WEIGHT_COMPONENT_NAMES`** (`crud.py:9`) - 8大主项名称映射
**`WEIGHT_COMPONENT_DETAILS`** (`services.py:371`) - 8大主项详细说明

---

## 六、数据流转关键控制点

### 6.1 数据完整性检查点
1. **录入时**：`curb_weight > 0` 校验（schemas.py:72）
2. **计算时**：`curb_weight > 0` 防护，避免除零错误
3. **对比时**：检查两款车都有 `weight_component` 数据
4. **统计时**：过滤掉没有重量构成数据的车辆

### 6.2 精度控制
- 重量值：直接存储，无精度损失
- 占比值：保留2位小数（`round(value, 2)`）
- 差值：保留1位小数（`round(value, 1)`）

### 6.3 排序规则
- 车辆列表默认按电池占比降序
- 对比差值按绝对值降序识别最大差异
- 统计时按车型类别枚举顺序遍历

---

## 七、快速上手路径

新接手同学可按此顺序理解代码：

1. **先看数据模型**：`models.py` → 理解表结构和关系
2. **再看数据结构**：`schemas.py` → 理解输入输出格式
3. **理解占比核算**：`crud.py` 的 `calculate_weight_ratios()` 和 `find_main_weight_contributor()`
4. **看单台车查询**：`crud.py` 的 `get_vehicle_with_weight()` 和 `convert_weight_with_ratio()`
5. **看对比逻辑**：`services.py` 的 `compare_fuel_ev_by_brand_model()`
6. **看统计逻辑**：`services.py` 的 `get_category_statistics()`
7. **最后看接口**：`routers/vehicles.py` 和 `routers/analysis.py`

---

## 八、典型业务场景走查

### 场景：分析"宝马3系燃油版 vs 宝马i3纯电版"的重量差异

1. **数据准备**：两车数据已在 `init_data.py` 中预置
2. **调用接口**：`GET /api/v1/analysis/compare/brand-model?brand=宝马&model=3系`
3. **内部执行**：
   - 查出宝马品牌3系相关的所有车辆
   - 筛选出 fuel 类型的"3系 325Li"和 ev 类型的"i3 eDrive40L"
   - 为每台车逐项计算占比（动力/电池/智能...）
   - 逐项计算差值（530-15=+515, 160-320=-160...）
   - 按差值绝对值排序，找到最大差异项"动力电池系统"(+515kg)
4. **返回结果**：含两车完整对比数据、差值汇总、最大差异项

---

*文档生成日期：2026-06-09*
*适用于版本：v1.0.0*
