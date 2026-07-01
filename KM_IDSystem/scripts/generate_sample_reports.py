from app.models.schemas import ModuleType
from app.services import db
from app.services.analysis import analyze_case
from app.services.reporting import generate_case_report


SAMPLES = [
    (
        ModuleType.dynamic,
        "样例-旋转窑动态调测",
        {
            "centerline_offset": 3.6,
            "ovality": 0.026,
            "eccentricity": 0.014,
            "runout": 1.4,
            "temperature": 418,
            "rotation_speed": 2.3,
        },
        [
            {"point": "1#轮带", "centerline_offset": 2.8, "temperature": 398},
            {"point": "2#轮带", "centerline_offset": 3.6, "temperature": 418},
            {"point": "3#轮带", "centerline_offset": 4.1, "temperature": 426},
        ],
    ),
    (
        ModuleType.fault,
        "样例-回转窑故障诊断",
        {"description": "窑体振动明显，伴随支承轮区域异响。", "temperature": 468, "vibration": 2.6, "speed": 2.1},
        [],
    ),
    (
        ModuleType.gear,
        "样例-大齿圈修复评估",
        {"wear_depth": 1.8, "crack_length": 22, "temperature": 128},
        [],
    ),
    (
        ModuleType.machining,
        "样例-机械加工工艺建议",
        {"material": "42CrMo", "diameter": 3200, "length": 7800, "tolerance": 0.04, "process_type": "turning"},
        [],
    ),
]


def main() -> None:
    db.init_db()
    for module, title, input_data, rows in SAMPLES:
        result = analyze_case(module, input_data, rows)
        case_id = db.create_case(module.value, title, input_data, None, result)
        case_data = db.get_case(case_id)
        path = generate_case_report(case_data)
        db.update_case_report(case_id, str(path), "ready")
        db.add_report(case_id, str(path), "ready", "样例 PDF 报告生成成功")
        print(f"{module.value}: case #{case_id} -> {path}")


if __name__ == "__main__":
    main()

