import { FileJson, Play, RotateCcw, Upload } from "lucide-react";
import { useMemo, useState } from "react";

const MODULES = {
  dynamic: {
    label: "动态调测窑",
    fields: [
      ["centerline_offset", "中心线偏移 mm", "number", 3.6],
      ["ovality", "椭圆度", "number", 0.026],
      ["eccentricity", "偏心率", "number", 0.014],
      ["runout", "跳动值 mm", "number", 1.4],
      ["temperature", "壳体温度 C", "number", 418],
      ["rotation_speed", "转速 rpm", "number", 2.3]
    ]
  },
  fault: {
    label: "故障诊断",
    fields: [
      ["description", "故障描述", "textarea", "窑体振动明显，伴随支承轮区域异响。"],
      ["temperature", "壳体温度 C", "number", 468],
      ["vibration", "振动 mm/s", "number", 2.6],
      ["speed", "转速 rpm", "number", 2.1]
    ]
  },
  gear: {
    label: "齿圈修复",
    fields: [
      ["wear_depth", "磨损深度 mm", "number", 1.8],
      ["crack_length", "裂纹长度 mm", "number", 22],
      ["temperature", "齿圈温度 C", "number", 128]
    ]
  },
  machining: {
    label: "机械加工",
    fields: [
      ["material", "材料", "text", "42CrMo"],
      ["diameter", "直径 mm", "number", 3200],
      ["length", "长度 mm", "number", 7800],
      ["tolerance", "精度要求 mm", "number", 0.04],
      ["process_type", "加工类型", "select", "turning"]
    ]
  },
  other: {
    label: "其他咨询",
    fields: [["topic", "咨询主题", "textarea", "金属表面修复和设备升级改造综合咨询"]]
  }
};

function defaultsFor(module) {
  return Object.fromEntries(MODULES[module].fields.map(([key, , , value]) => [key, value]));
}

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) return [];
  const headers = lines[0].split(",").map((item) => item.trim());
  return lines.slice(1).map((line) => {
    const cells = line.split(",").map((item) => item.trim());
    return Object.fromEntries(headers.map((header, index) => [header, Number.isNaN(Number(cells[index])) ? cells[index] : Number(cells[index])]));
  });
}

export default function ModuleForm({ module, onSubmit, busy }) {
  const [values, setValues] = useState(defaultsFor(module));
  const [uploadedRows, setUploadedRows] = useState([]);
  const [uploadedFileName, setUploadedFileName] = useState("");

  const config = MODULES[module];
  const fields = useMemo(() => config.fields, [config]);

  function switchDefaults() {
    setValues(defaultsFor(module));
    setUploadedRows([]);
    setUploadedFileName("");
  }

  async function handleFile(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    const rows = file.name.endsWith(".json") ? JSON.parse(text) : parseCsv(text);
    setUploadedRows(Array.isArray(rows) ? rows : [rows]);
    setUploadedFileName(file.name);
  }

  function changeValue(key, type, nextValue) {
    setValues((current) => ({
      ...current,
      [key]: type === "number" ? Number(nextValue) : nextValue
    }));
  }

  return (
    <section className="workbench-form">
      <div className="section-title">
        <h2>{config.label}</h2>
        <button className="icon-button" type="button" onClick={switchDefaults} title="恢复样例">
          <RotateCcw size={18} />
        </button>
      </div>
      <div className="form-grid">
        {fields.map(([key, label, type]) => (
          <label key={key} className={type === "textarea" ? "field field--wide" : "field"}>
            <span>{label}</span>
            {type === "textarea" ? (
              <textarea value={values[key] ?? ""} onChange={(event) => changeValue(key, type, event.target.value)} />
            ) : type === "select" ? (
              <select value={values[key] ?? ""} onChange={(event) => changeValue(key, type, event.target.value)}>
                <option value="turning">车削 turning</option>
                <option value="grinding">磨削 grinding</option>
                <option value="boring">镗孔 boring</option>
                <option value="milling">铣削 milling</option>
              </select>
            ) : (
              <input type={type} value={values[key] ?? ""} step="any" onChange={(event) => changeValue(key, type, event.target.value)} />
            )}
          </label>
        ))}
      </div>
      <div className="upload-row">
        <label className="upload-button">
          <Upload size={18} />
          <span>上传 JSON/CSV</span>
          <input type="file" accept=".json,.csv" onChange={handleFile} />
        </label>
        <div className="upload-status">
          <FileJson size={16} />
          <span>{uploadedFileName || "未上传文件，使用表单样例数据"}</span>
          {uploadedRows.length > 0 && <strong>{uploadedRows.length} 行</strong>}
        </div>
        <button
          className="primary-button"
          type="button"
          disabled={busy}
          onClick={() =>
            onSubmit({
              module,
              title: `${config.label}案例`,
              input_data: values,
              uploaded_file_name: uploadedFileName || null,
              uploaded_rows: uploadedRows,
              role: "engineer",
              auto_generate_report: true
            })
          }
        >
          <Play size={18} />
          <span>{busy ? "分析中" : "生成分析与PDF"}</span>
        </button>
      </div>
    </section>
  );
}

