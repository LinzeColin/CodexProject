"""
模块：机械加工服务

提供车削、磨削、镗孔等加工工艺咨询，结合武汉开明先进设备能力。
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple


@dataclass
class MachiningRequest:
    """加工请求。"""
    material: str  # 材料种类，例如 “42CrMo”
    diameter: float  # 直径（mm）
    length: float  # 长度（mm）
    tolerance: float  # 精度要求（mm）
    process_type: str  # 加工类型：turning/milling/grinding/boring
    other_params: Dict[str, Any]


def recommend_process(request: MachiningRequest) -> Dict[str, Any]:
    """
    根据加工请求推荐工艺和设备。

    返回字典包含工艺流程、刀具选择、设备建议。
    """
    processes: List[str] = []
    tools: List[str] = []
    machines: List[str] = []
    # 示例逻辑：简单根据加工类型和材料判断
    if request.process_type == "turning":
        processes.append("车削：粗车→半精车→精车")
        tools.append("硬质合金刀具")
        machines.append("8m 数控立车")
    elif request.process_type == "grinding":
        processes.append("磨削：粗磨→精磨")
        tools.append("砂轮和冷却液")
        machines.append("数控磨床")
    elif request.process_type == "boring":
        processes.append("镗孔：粗镗→精镗")
        tools.append("镗刀与钻头")
        machines.append("大型镗床")
    else:
        processes.append("未识别的加工类型，请确认 process_type 字段。")
    return {
        "processes": processes,
        "tools": tools,
        "machines": machines,
    }
