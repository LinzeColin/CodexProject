"""
主程序：示例性命令行接口，用于调用各模块。

运行方式：
    python main.py --module dynamic --params '{"centerline_offset": 3.5, "ovality": 0.025, "eccentricity": 0.01, "runout": 1.2, "temperature": 380, "rotation_speed": 2.3}'

注意：此处仅为演示，真实项目应使用更完备的参数解析和异常处理。
"""

import argparse
import json

from modules.dynamic_monitoring import KilnMeasurement, analyze_kiln
from modules.fault_diagnosis import FaultInput, diagnose_fault
from modules.gear_repair import GearInspection, repair_gear
from modules.machining_service import MachiningRequest, recommend_process


def parse_args():
    parser = argparse.ArgumentParser(description="武汉开明智能工业运维助手示例")
    parser.add_argument("--module", type=str, required=True, help="要调用的模块：dynamic/fault/gear/machining")
    parser.add_argument("--params", type=str, required=True, help="JSON 格式的参数")
    return parser.parse_args()


def main():
    args = parse_args()
    params = json.loads(args.params)
    if args.module == "dynamic":
        measurement = KilnMeasurement(
            centerline_offset=params.get("centerline_offset", 0.0),
            ovality=params.get("ovality", 0.0),
            eccentricity=params.get("eccentricity", 0.0),
            runout=params.get("runout", 0.0),
            temperature=params.get("temperature", 0.0),
            rotation_speed=params.get("rotation_speed", 0.0),
            additional_params={k: v for k, v in params.items() if k not in [
                "centerline_offset", "ovality", "eccentricity", "runout", "temperature", "rotation_speed"
            ]},
        )
        result = analyze_kiln(measurement)
    elif args.module == "fault":
        fault_input = FaultInput(
            description=params.get("description", ""),
            temperature=params.get("temperature", 0.0),
            vibration=params.get("vibration", 0.0),
            speed=params.get("speed", 0.0),
            other_params={k: v for k, v in params.items() if k not in [
                "description", "temperature", "vibration", "speed"
            ]},
        )
        result = diagnose_fault(fault_input)
    elif args.module == "gear":
        inspection = GearInspection(
            wear_depth=params.get("wear_depth", 0.0),
            crack_length=params.get("crack_length", 0.0),
            temperature=params.get("temperature", 0.0),
            other_params={k: v for k, v in params.items() if k not in [
                "wear_depth", "crack_length", "temperature"
            ]},
        )
        result = repair_gear(inspection)
    elif args.module == "machining":
        request = MachiningRequest(
            material=params.get("material", ""),
            diameter=params.get("diameter", 0.0),
            length=params.get("length", 0.0),
            tolerance=params.get("tolerance", 0.0),
            process_type=params.get("process_type", ""),
            other_params={k: v for k, v in params.items() if k not in [
                "material", "diameter", "length", "tolerance", "process_type"
            ]},
        )
        result = recommend_process(request)
    else:
        result = {"error": "未知的模块"}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
