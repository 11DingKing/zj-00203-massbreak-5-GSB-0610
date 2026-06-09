# 汽车重量构成分析系统

拆解油电同款车型重量差异的后端分析系统。

## 功能特性

- **车辆重量构成拆解**：每个车型登记动力电池系统、智能化配置、车身与底盘强化、隔音舒适件等重量来源
- **占比自动计算**：系统算出每个车型各部分占整备质量的比例
- **增重大头定位**：自动识别最大重量贡献项（一般是电池包）
- **油电同款对比**：支持同品牌油电同款对比，逐项重量摆一起看差在哪
- **分类统计**：按车型类别统计各重量来源的平均占比
- **初始数据**：内置40+款车型及重量构成明细

## 技术栈

- FastAPI 0.109.0
- SQLAlchemy 2.0.25
- Pydantic 2.5.3
- SQLite

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 访问文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 接口

### 车辆管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/vehicles` | 新增车辆及重量构成 |
| GET | `/api/v1/vehicles` | 获取车辆列表（默认按电池占比降序） |
| GET | `/api/v1/vehicles/{id}` | 获取车辆详情及重量构成 |
| PUT | `/api/v1/vehicles/{id}` | 更新车辆信息 |
| DELETE | `/api/v1/vehicles/{id}` | 删除车辆 |
| POST | `/api/v1/vehicles/{id}/weight` | 创建/更新车辆重量构成 |

### 重量分析

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/analysis/highest-battery-ratio` | 获取电池占比最高的车型 |
| GET | `/api/v1/analysis/compare/brand-model` | 按品牌型号对比油电版本 |
| GET | `/api/v1/analysis/compare/ids` | 按车辆ID对比两款车 |
| GET | `/api/v1/analysis/statistics` | 按车型类别统计平均占比 |
| GET | `/api/v1/analysis/weight-breakdown/{id}` | 获取单台车重量拆解 |

## 数据示例

### 重量构成字段说明

| 字段 | 说明 |
|------|------|
| powertrain_weight | 动力系统重量（发动机/电机+变速箱） |
| battery_system_weight | 动力电池系统重量 |
| intelligent_config_weight | 智能化配置总重量 |
| body_chassis_reinforce_weight | 车身与底盘强化重量 |
| sound_insulation_weight | 隔音舒适件重量 |
| suspension_brake_weight | 悬挂与制动系统重量 |
| interior_comfort_weight | 内饰舒适性配置重量 |
| other_weight | 其他重量 |

### 智能化配置细分

| 字段 | 说明 |
|------|------|
| intelligent_adas_weight | 智能驾驶辅助系统 |
| intelligent_cockpit_weight | 智能座舱系统 |
| intelligent_sensor_weight | 传感器系统 |
| intelligent_connectivity_weight | 网联系统 |

## 油电对比示例

**宝马 3系 325Li vs 宝马 i3 eDrive40L**

| 项目 | 燃油版(kg) | 纯电版(kg) | 差值(kg) |
|------|-----------|-----------|---------|
| 整备质量 | 1610 | 2055 | +445 |
| 动力系统 | 320 | 160 | -160 |
| 动力电池 | 15 | 530 | **+515** |
| 智能化配置 | 85 | 130 | +45 |
| 车身底盘强化 | 260 | 330 | +70 |
| 隔音舒适件 | 60 | 95 | +35 |

**结论**：虽然电机比发动机轻160kg，但电池包重了515kg，最终纯电版比燃油版重445kg，最大增重项是动力电池系统。
