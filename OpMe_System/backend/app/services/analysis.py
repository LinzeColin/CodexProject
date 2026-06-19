from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.models.schemas import ModuleType
from app.services.model_router import route_model


REFERENCE_NOTES = [
    "参考 ThingsBoard/Grafana 的设备指标总览、风险状态和告警布局。",
    "参考 Open MCT/FUXA 的遥测趋势、设备状态和工业 HMI 表达方式。",
    "参考 Dify/Chatchat/LiteLLM 的模型配置、知识库和失败降级思路。",
]


def _risk_level(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 40:
        return "warning"
    return "normal"


def _bar_option(labels: List[str], values: List[float], color: str = "#2563eb") -> Dict[str, Any]:
    return {
        "tooltip": {"trigger": "axis"},
        "grid": {"left": 36, "right": 16, "top": 28, "bottom": 36},
        "xAxis": {"type": "category", "data": labels},
        "yAxis": {"type": "value"},
        "series": [{"type": "bar", "data": values, "itemStyle": {"color": color}, "barWidth": 28}],
    }


def _line_option(labels: List[str], values: List[float], color: str = "#0f766e") -> Dict[str, Any]:
    return {
        "tooltip": {"trigger": "axis"},
        "grid": {"left": 36, "right": 16, "top": 28, "bottom": 36},
        "xAxis": {"type": "category", "data": labels},
        "yAxis": {"type": "value"},
        "series": [{"type": "line", "data": values, "smooth": True, "areaStyle": {}, "lineStyle": {"color": color}}],
    }


def _gauge_option(value: float, max_value: float = 100) -> Dict[str, Any]:
    return {
        "series": [
            {
                "type": "gauge",
                "min": 0,
                "max": max_value,
                "progress": {"show": True, "width": 12},
                "axisLine": {"lineStyle": {"width": 12}},
                "detail": {"valueAnimation": True, "formatter": "{value}"},
                "data": [{"value": value, "name": "风险"}],
            }
        ]
    }


def analyze_dynamic(input_data: Dict[str, Any], uploaded_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    centerline = float(input_data.get("centerline_offset", 0) or 0)
    ovality = float(input_data.get("ovality", 0) or 0)
    eccentricity = float(input_data.get("eccentricity", 0) or 0)
    runout = float(input_data.get("runout", 0) or 0)
    temperature = float(input_data.get("temperature", 0) or 0)
    rotation_speed = float(input_data.get("rotation_speed", 0) or 0)
    history = uploaded_rows or [
        {"point": "1#轮带", "centerline_offset": max(centerline - 0.8, 0), "temperature": max(temperature - 18, 0)},
        {"point": "2#轮带", "centerline_offset": centerline, "temperature": temperature},
        {"point": "3#轮带", "centerline_offset": centerline + 0.4, "temperature": temperature + 8},
    ]
    risk_score = min(
        100,
        int(centerline / 5 * 35 + ovality / 0.04 * 25 + temperature / 520 * 25 + runout / 3 * 15),
    )
    suggestions = []
    if centerline > 3:
        suggestions.append(f"中心线偏移 {centerline:.2f}mm，优先复核支承滚轮位置和基础沉降。")
    if ovality > 0.02:
        suggestions.append(f"椭圆度 {ovality:.3f} 超出建议范围，建议检查壳体受力、轮带间隙和局部磨损。")
    if temperature > 400:
        suggestions.append(f"壳体温度 {temperature:.1f}℃ 偏高，需检查燃烧强度、冷却和耐火材料状态。")
    if eccentricity > 0.015:
        suggestions.append(f"偏心率 {eccentricity:.3f} 偏高，建议结合激光扫描复测动态中心线。")
    if not suggestions:
        suggestions.append("当前关键参数处于可控区间，建议保持巡检频率并记录趋势。")

    labels = [str(row.get("point", f"P{i+1}")) for i, row in enumerate(history)]
    center_values = [float(row.get("centerline_offset", centerline) or 0) for row in history]
    temp_values = [float(row.get("temperature", temperature) or 0) for row in history]
    visualizations = [
        {
            "id": "centerline-trend",
            "title": "中心线偏差趋势",
            "kind": "line",
            "description": "沿轮带/测点展示中心线偏差，辅助定位调整优先点。",
            "echarts_option": _line_option(labels, center_values),
            "data": {"labels": labels, "values": center_values, "unit": "mm"},
        },
        {
            "id": "thermal-profile",
            "title": "壳体温度分布",
            "kind": "bar",
            "description": "展示各测点温度，用于识别热态异常区域。",
            "echarts_option": _bar_option(labels, temp_values, "#dc2626"),
            "data": {"labels": labels, "values": temp_values, "unit": "C"},
        },
        {
            "id": "risk-gauge",
            "title": "动态运行风险",
            "kind": "gauge",
            "description": "综合中心线、椭圆度、温度、跳动值形成的规则风险评分。",
            "echarts_option": _gauge_option(risk_score),
            "data": {"value": risk_score, "unit": "score"},
        },
    ]
    return {
        "module": ModuleType.dynamic.value,
        "title": "旋转窑动态调测分析报告",
        "summary": f"中心线偏移 {centerline:.2f}mm，椭圆度 {ovality:.3f}，综合风险评分 {risk_score}/100。",
        "risk_level": _risk_level(risk_score),
        "risk_score": risk_score,
        "metrics": {
            "centerline_offset": centerline,
            "ovality": ovality,
            "eccentricity": eccentricity,
            "runout": runout,
            "temperature": temperature,
            "rotation_speed": rotation_speed,
        },
        "suggestions": suggestions,
        "evidence": REFERENCE_NOTES + ["原型逻辑：中心线偏移、椭圆度和温度阈值判断。"],
        "visualizations": visualizations,
    }


def analyze_fault(input_data: Dict[str, Any], uploaded_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    description = str(input_data.get("description", ""))
    temperature = float(input_data.get("temperature", 0) or 0)
    vibration = float(input_data.get("vibration", 0) or 0)
    speed = float(input_data.get("speed", 0) or 0)
    symptoms = {
        "振动": 1 if ("振动" in description or vibration > 2.0) else 0,
        "高温": 1 if temperature > 450 else 0,
        "速度异常": 1 if speed and (speed < 1.0 or speed > 4.5) else 0,
        "异响": 1 if "异响" in description or "噪音" in description else 0,
    }
    causes = []
    suggestions = []
    if symptoms["振动"]:
        causes.append("支撑滚轮磨损、安装不良或轮带间隙异常")
        suggestions.append("检查支撑滚轮接触斑、轴承温升和基础螺栓，必要时调整或修复。")
    if symptoms["高温"]:
        causes.append("燃烧过旺、冷却不足或耐火材料异常")
        suggestions.append("调整燃烧器与冷却系统，复核红外测温和壳体热斑分布。")
    if symptoms["速度异常"]:
        causes.append("传动系统负载波动或控制参数漂移")
        suggestions.append("检查主传动电流、减速机状态和变频控制参数。")
    if symptoms["异响"]:
        causes.append("齿轮啮合异常、润滑不足或局部裂纹")
        suggestions.append("检查齿面接触、润滑油膜和齿圈裂纹，安排停机复检。")
    if not causes:
        causes.append("规则库未识别明确故障")
        suggestions.append("请补充振动频谱、温度趋势、转速和巡检照片，交由工程师复核。")
    risk_score = min(100, int(vibration / 4 * 35 + temperature / 550 * 35 + len([v for v in symptoms.values() if v]) * 10))
    visualizations = [
        {
            "id": "symptom-matrix",
            "title": "症状触发矩阵",
            "kind": "matrix",
            "description": "将文字症状与监测指标映射为故障线索。",
            "echarts_option": _bar_option(list(symptoms.keys()), list(symptoms.values()), "#7c3aed"),
            "data": {"labels": list(symptoms.keys()), "values": list(symptoms.values())},
        },
        {
            "id": "component-impact",
            "title": "影响部件优先级",
            "kind": "bar",
            "description": "按规则推理输出部件排查优先级。",
            "echarts_option": _bar_option(["支承轮", "冷却系统", "传动系统", "齿圈"], [symptoms["振动"], symptoms["高温"], symptoms["速度异常"], symptoms["异响"]], "#0ea5e9"),
            "data": {"labels": ["支承轮", "冷却系统", "传动系统", "齿圈"], "values": [symptoms["振动"], symptoms["高温"], symptoms["速度异常"], symptoms["异响"]]},
        },
        {
            "id": "risk-gauge",
            "title": "故障风险评分",
            "kind": "gauge",
            "description": "综合振动、温度和症状数量形成的规则风险评分。",
            "echarts_option": _gauge_option(risk_score),
            "data": {"value": risk_score, "unit": "score"},
        },
    ]
    return {
        "module": ModuleType.fault.value,
        "title": "回转窑运行故障诊断报告",
        "summary": f"识别到 {len(causes)} 类可能原因，综合风险评分 {risk_score}/100。",
        "risk_level": _risk_level(risk_score),
        "risk_score": risk_score,
        "metrics": {"temperature": temperature, "vibration": vibration, "speed": speed, "symptoms": symptoms},
        "suggestions": suggestions,
        "evidence": REFERENCE_NOTES + causes,
        "visualizations": visualizations,
    }


def analyze_gear(input_data: Dict[str, Any], uploaded_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    wear_depth = float(input_data.get("wear_depth", 0) or 0)
    crack_length = float(input_data.get("crack_length", 0) or 0)
    temperature = float(input_data.get("temperature", 0) or 0)
    risk_score = min(100, int(wear_depth / 3 * 45 + crack_length / 80 * 35 + temperature / 180 * 20))
    materials = []
    suggestions = []
    if wear_depth > 1.0:
        materials.append("FGM-KM-B.U 合金修复材料")
        suggestions.append("齿面磨损已超过常规巡检阈值，建议清理磨损区后采用 FGM-KM-B.U 材料修复。")
    if crack_length > 0:
        materials.append("焊接材料与热处理剂")
        suggestions.append("裂纹需先做探伤、开坡口和焊补，再执行热处理与齿面精修。")
    if temperature > 120:
        suggestions.append("齿圈温度偏高，需检查润滑、啮合间隙和载荷波动。")
    if not suggestions:
        suggestions.append("当前检测数据未触发修复阈值，建议保持润滑和定期探伤。")
    steps = ["停机隔离", "清洁探伤", "表面处理", "材料修复", "热处理", "齿面精修", "质量验收"]
    visualizations = [
        {
            "id": "wear-crack-severity",
            "title": "磨损与裂纹严重度",
            "kind": "bar",
            "description": "对比磨损深度、裂纹长度和温度风险。",
            "echarts_option": _bar_option(["磨损mm", "裂纹mm", "温度C"], [wear_depth, crack_length, temperature], "#b45309"),
            "data": {"labels": ["磨损mm", "裂纹mm", "温度C"], "values": [wear_depth, crack_length, temperature]},
        },
        {
            "id": "repair-timeline",
            "title": "修复工艺流程",
            "kind": "timeline",
            "description": "齿圈齿面修复的建议工序。",
            "echarts_option": _bar_option(steps, [1] * len(steps), "#0f766e"),
            "data": {"steps": steps},
        },
        {
            "id": "risk-gauge",
            "title": "修复风险评分",
            "kind": "gauge",
            "description": "综合磨损、裂纹和温度形成的规则风险评分。",
            "echarts_option": _gauge_option(risk_score),
            "data": {"value": risk_score, "unit": "score"},
        },
    ]
    return {
        "module": ModuleType.gear.value,
        "title": "大齿圈齿面修复评估报告",
        "summary": f"磨损 {wear_depth:.2f}mm，裂纹 {crack_length:.1f}mm，推荐材料：{', '.join(materials) if materials else '暂不需要专项材料'}。",
        "risk_level": _risk_level(risk_score),
        "risk_score": risk_score,
        "metrics": {"wear_depth": wear_depth, "crack_length": crack_length, "temperature": temperature, "materials": materials},
        "suggestions": suggestions,
        "evidence": REFERENCE_NOTES + ["任务清单要求结合 FGM-KM-B.U 新材料修复工艺。"],
        "visualizations": visualizations,
    }


def analyze_machining(input_data: Dict[str, Any], uploaded_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    material = str(input_data.get("material", "42CrMo"))
    diameter = float(input_data.get("diameter", 0) or 0)
    length = float(input_data.get("length", 0) or 0)
    tolerance = float(input_data.get("tolerance", 0.1) or 0.1)
    process_type = str(input_data.get("process_type", "turning"))
    process_map = {
        "turning": ("车削：粗车 -> 半精车 -> 精车", "硬质合金刀具", "8m 数控立车"),
        "grinding": ("磨削：粗磨 -> 精磨 -> 抛光检测", "砂轮与冷却液", "数控磨床"),
        "boring": ("镗孔：粗镗 -> 半精镗 -> 精镗", "镗刀与钻头", "大型镗床"),
        "milling": ("铣削：粗铣 -> 精铣 -> 去毛刺", "面铣刀/立铣刀", "数控铣床"),
    }
    process, tool, machine = process_map.get(process_type, ("未识别加工类型，请确认 process_type", "待确认", "待确认"))
    precision_risk = 35 if tolerance < 0.05 else 15 if tolerance < 0.12 else 5
    size_risk = min(35, int((diameter + length) / 10000 * 35))
    material_risk = 20 if material.lower() in {"42crmo", "inconel", "高温合金"} else 10
    risk_score = min(100, precision_risk + size_risk + material_risk)
    suggestions = [
        f"推荐工艺路线：{process}。",
        f"建议设备：{machine}；建议刀具/耗材：{tool}。",
        "加工前需确认余量、热处理状态、装夹方式和最终检测标准。",
    ]
    if tolerance < 0.05:
        suggestions.append("精度要求较高，建议增加半精加工、消应力和终检复测。")
    visualizations = [
        {
            "id": "process-route",
            "title": "加工工艺路线",
            "kind": "timeline",
            "description": "按照加工类型生成的建议路线。",
            "echarts_option": _bar_option(process.split("：")[-1].split(" -> "), [1, 1, 1], "#2563eb"),
            "data": {"steps": process.split("：")[-1].split(" -> ")},
        },
        {
            "id": "capability-matrix",
            "title": "设备适配矩阵",
            "kind": "bar",
            "description": "尺寸、精度、材料对设备能力的压力。",
            "echarts_option": _bar_option(["尺寸", "精度", "材料"], [size_risk, precision_risk, material_risk], "#0891b2"),
            "data": {"labels": ["尺寸", "精度", "材料"], "values": [size_risk, precision_risk, material_risk]},
        },
        {
            "id": "risk-gauge",
            "title": "加工交付风险",
            "kind": "gauge",
            "description": "综合尺寸、精度和材料难度形成的规则风险评分。",
            "echarts_option": _gauge_option(risk_score),
            "data": {"value": risk_score, "unit": "score"},
        },
    ]
    return {
        "module": ModuleType.machining.value,
        "title": "机械加工工艺与计划建议报告",
        "summary": f"{material} 工件，直径 {diameter:.0f}mm、长度 {length:.0f}mm，推荐 {machine} 执行 {process_type}。",
        "risk_level": _risk_level(risk_score),
        "risk_score": risk_score,
        "metrics": {
            "material": material,
            "diameter": diameter,
            "length": length,
            "tolerance": tolerance,
            "process_type": process_type,
            "machine": machine,
            "tool": tool,
        },
        "suggestions": suggestions,
        "evidence": REFERENCE_NOTES + ["任务清单要求展示大型数控立车、卧车、滚齿机、100T 起重机等设备能力。"],
        "visualizations": visualizations,
    }


def analyze_other(input_data: Dict[str, Any], uploaded_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    topic = str(input_data.get("topic", "综合咨询"))
    suggestions = [
        "将咨询内容按设备、材料、工艺、安全和交付风险拆分，分别由工程师复核。",
        "若涉及现场施工，需补充照片、尺寸、工况和历史维修记录。",
    ]
    risk_score = 25
    return {
        "module": ModuleType.other.value,
        "title": "综合工业运维咨询报告",
        "summary": f"已形成 {topic} 的初步咨询建议，需结合现场资料复核。",
        "risk_level": _risk_level(risk_score),
        "risk_score": risk_score,
        "metrics": {"topic": topic},
        "suggestions": suggestions,
        "evidence": REFERENCE_NOTES,
        "visualizations": [
            {
                "id": "consulting-scope",
                "title": "咨询范围拆分",
                "kind": "bar",
                "description": "综合咨询的关注维度。",
                "echarts_option": _bar_option(["设备", "材料", "工艺", "安全", "交付"], [1, 1, 1, 1, 1], "#64748b"),
                "data": {"labels": ["设备", "材料", "工艺", "安全", "交付"], "values": [1, 1, 1, 1, 1]},
            }
        ],
    }


ANALYZERS = {
    ModuleType.dynamic: analyze_dynamic,
    ModuleType.fault: analyze_fault,
    ModuleType.gear: analyze_gear,
    ModuleType.machining: analyze_machining,
    ModuleType.other: analyze_other,
}


def analyze_case(module: ModuleType, input_data: Dict[str, Any], uploaded_rows: List[Dict[str, Any]], case_id: int | None = None) -> Dict[str, Any]:
    result = ANALYZERS[module](input_data, uploaded_rows)
    model_status = route_model(module.value, input_data, result, case_id)
    result["model_status"] = model_status
    if model_status.get("used") and model_status.get("message"):
        result["suggestions"].append(f"模型补充意见：{model_status['message']}")
    return result

