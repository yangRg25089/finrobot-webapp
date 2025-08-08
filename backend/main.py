import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from services.script_manager import run_script_stream
from sse_starlette.sse import EventSourceResponse

app = FastAPI(
    title="FinRobot API",
    description="API for running financial strategies and visualizing results.",
    version="1.0.0",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class scriptRequest(BaseModel):
    script_path: str
    params: dict
    lang: str


# ===== SSE 流式输出 =====
@app.get("/api/run-script/stream")
async def run_script_stream_endpoint(
    script_path: str,
    lang: str = "zh",
    params: Optional[str] = None,  # 允许前端以 JSON 字符串传参（也可改成 dict）
):
    """
    SSE：实时返回脚本运行的事件流（stdout/stderr/result/exit/error）
    前端可用 EventSource 直接接收。
    """
    try:
        parsed_params: Dict[str, Any] = (
            json.loads(params) if isinstance(params, str) and params else {}
        )
    except Exception:
        parsed_params = {}

    async def event_gen():
        try:
            async for ev in run_script_stream(script_path, parsed_params, lang):
                # SSE: 每条消息是一个 dict，写入 data 字段
                yield {
                    "event": "message",
                    "data": json.dumps(ev, ensure_ascii=False),
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps(
                    {"type": "error", "error": str(e)}, ensure_ascii=False
                ),
            }

    return EventSourceResponse(event_gen())


BASE_DIR = Path(__file__).resolve()
CONFIG_FILE = BASE_DIR.parent / "OAI_CONFIG_LIST"


@app.get("/api/models")
async def list_available_models():
    if not CONFIG_FILE.exists():
        raise HTTPException(status_code=404, detail="OAI_CONFIG_LIST not found")

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)  # 期望是 list[dict]

        # 抹掉 api_key
        sanitized = []
        for entry in data:
            if isinstance(entry, dict):
                entry = entry.copy()
                entry.pop("api_key", None)  # 移除 api_key（若有）
                sanitized.append(entry)

        return sanitized

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="OAI_CONFIG_LIST JSON decode error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def extract_params_from_file(py_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    返回示例:
      {
        "company": {"type": "string", "defaultValue": "apple"},
        "date":    {"type": "date",   "defaultValue": "2025-05-01"}
      }
    """
    text = py_path.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(
        r"""(\w+)\s*=\s*params\.get\(\s*['"](\w+)['"]\s*,\s*['"]([^'"]*)['"]\s*\)""",
        re.MULTILINE,
    )

    out: Dict[str, Dict[str, Any]] = {}
    for full_var, key, default in pattern.findall(text):
        _type = "date" if DATE_PATTERN.match(default) else "string"
        out[key] = {"type": _type, "defaultValue": default}
    return out


@app.get("/api/tutorial-scripts")
async def list_tutorial_scripts() -> Dict[str, List[Dict[str, Any]]]:
    """
    扫描 tutorials_wrapper 下所有 .py 脚本，组装脚本信息 + 参数信息
    """
    TW_DIR = Path(__file__).resolve().parent / "tutorials_wrapper"
    if not TW_DIR.exists():
        raise HTTPException(
            status_code=404, detail="tutorials_wrapper directory not found"
        )

    scripts_info: List[Dict[str, Any]] = []

    for py_file in TW_DIR.rglob("*.py"):
        # 跳过 __init__.py、根目录脚本(util 等)、以及 site-packages 编译文件
        if py_file.name == "__init__.py" or "site-packages" in py_file.parts:
            continue
        relative_parts = py_file.relative_to(TW_DIR).parts
        if len(relative_parts) == 1:  # 仅一层 → 位于根目录，忽略
            continue

        folder = relative_parts[0]  # beginner / advanced ...
        script_name = py_file.stem
        params = extract_params_from_file(py_file)

        scripts_info.append(
            {
                "script_name": script_name,
                "folder": folder,
                "params": params,
            }
        )

    # 排序：先按 folder，再按 script_name
    scripts_info.sort(key=lambda x: (x["folder"], x["script_name"]))

    return {"tutorials_wrapper": scripts_info}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
