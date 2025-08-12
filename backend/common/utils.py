from __future__ import annotations

import ast
import base64
import io
import json
import re
from pathlib import Path
from typing import Any, Dict, Final, List, Optional
from urllib.parse import unquote, unquote_plus

import fitz  # PyMuPDF
from PIL import Image

# =========================
# Language directives
# =========================

JA_DIRECTIVE: Final[
    str
] = """
言語指示：
- 分析本文を日本語で作成してください。
- セクション構成は英語版と同等にしつつ、日本語として自然な表現を用いてください。
- ティッカー、コード識別子、APIフィールド名は英語のままにしてください（翻訳しない）。
- Markdown 形式を使用し、日付は YYYY-MM-DD で表記してください。
- 全体のメッセージの末尾は "TERMINATE" で終えてください。
"""

ZH_DIRECTIVE: Final[
    str
] = """
语言指令：
- 分析正文使用中文撰写，并保持逻辑清晰、结构完整。
- 股票代码、函数名、API 字段名保持英文，不要翻译。
- 使用 Markdown 格式；日期使用 YYYY-MM-DD。
- 整体消息以 "TERMINATE" 作为结尾。
"""


def build_lang_directive(lang: str | None) -> str:
    code = (lang or "").lower()
    base = code.split("-")[0]
    if base == "ja":
        return JA_DIRECTIVE
    if base == "zh":
        return ZH_DIRECTIVE
    return ""


# =========================
# Message normalization
# =========================


def _to_plain_content(content: Any) -> Any:
    """把常见 message.content 形态揉成普通 str/list/dict，尽量保真。"""
    if isinstance(content, (bytes, bytearray)):
        return content.decode("utf-8", "ignore")
    if isinstance(content, list):
        # 有些框架把多段内容放 list；尽量取 text/content/value 字段，退化成 str
        parts = []
        for c in content:
            if isinstance(c, dict):
                parts.append(c.get("text") or c.get("content") or c.get("value") or "")
            else:
                parts.append(str(c))
        return "\n".join([p for p in parts if p])

    # 常见简单类型直接返回；复杂对象尽量 JSON 化兜底为 str
    if isinstance(content, (str, int, float, bool, type(None), dict)):
        return content
    try:
        return json.loads(json.dumps(content, default=str))
    except Exception:
        return str(content)


def _normalize_msg(m: Any, conv_name: str | None) -> Dict[str, Any]:
    """把不同 SDK 的消息结构拍平为统一 dict。"""
    if isinstance(m, dict):
        role = m.get("role") or m.get("from")
        name = m.get("name") or conv_name
        tool_name = m.get("tool_name") or m.get("tool")
        content = _to_plain_content(m.get("content"))
    else:
        role = getattr(m, "role", None) or getattr(m, "sender", None)
        name = getattr(m, "name", None) or conv_name
        tool_name = getattr(m, "tool_name", None) or getattr(m, "tool", None)
        content = _to_plain_content(
            getattr(m, "content", None) or getattr(m, "message", None)
        )
    return {
        "role": role or "",
        "name": name,
        "tool_name": tool_name,
        "content": content,
    }


# =========================
# Meaningfulness filter
# =========================

EMPTY_CODEBLOCK_RE = re.compile(
    r"""^\s*`{3,}[\w+\-]*\s*(?:\r?\n|\r|\s)*`{3,}\s*$""", re.DOTALL
)

# 去除掉 markdown 装饰符后检查是否还有“内容字符”
DECORATIONS_RE = re.compile(r"[`*_#>\-\+\|\[\]\(\)~\^=]{1,}")

# 去除零宽字符
ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")


def is_meaningful(raw: str) -> bool:
    if raw is None:
        return False

    s = ZERO_WIDTH_RE.sub("", str(raw))
    t = s.strip()
    if not t:
        return False

    if t.upper() == "TERMINATE":
        return False

    # 纯空的代码块（```[lang] ... ```，中间只有空白/换行）
    if EMPTY_CODEBLOCK_RE.match(t):
        return False

    # 去掉常见 markdown 装饰符，再看是否还有“内容字符”
    # 先把装饰符替换为空，再去空白
    stripped = DECORATIONS_RE.sub("", t)
    stripped = stripped.strip()

    # 简化判断：是否存在任意“字母/数字/东亚文字”
    if not re.search(r"[A-Za-z0-9\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", stripped):
        return False

    return True


# =========================
# Conversation extractors
# =========================
def extract_conversation(user_agent: Any) -> List[Dict[str, Any]]:
    """
    提取 user_agent 中的全部对话消息（不区分 assistant）。
    过滤：content 为空（None/空串/仅空白）或等于 'TERMINATE' 的记录。
    返回：[{role, name, tool_name, content}, ...]
    """
    out: List[Dict[str, Any]] = []

    # 统一收集两个来源
    sources = []
    cm = getattr(user_agent, "chat_messages", None)
    if isinstance(cm, dict) and cm:
        # key 可能是 str 或对象（取其 name）
        sources.append(
            (cm, lambda k: k if isinstance(k, str) else getattr(k, "name", None))
        )

    mh = getattr(user_agent, "message_history", None)
    if isinstance(mh, dict) and mh:
        sources.append((mh, lambda k: k))

    for store, key_to_name in sources:
        for k, msgs in store.items():
            if not msgs:
                continue
            conv_name = key_to_name(k)
            for m in msgs:
                msg = _normalize_msg(m, conv_name)  # 假定已存在
                content = msg.get("content")

                # 处理常见形态：None / str / list（有些框架把多段内容放 list）
                if content is None:
                    continue
                if isinstance(content, str):
                    s = content.strip()
                    if not s or s.upper() == "TERMINATE" or not is_meaningful(s):
                        continue
                elif isinstance(content, list):
                    # 全部元素为假值则跳过（[], [""], [None], 等）
                    if not any(bool(x) for x in content):
                        continue
                # 其他类型按有值处理
                out.append(msg)

    return out


def extract_all(up) -> list[dict]:
    """原始兜底：无过滤地抽出所有消息（调试用）。"""
    out = []
    cm = getattr(up, "chat_messages", None)
    if isinstance(cm, dict):
        for k, msgs in cm.items():
            name = k if isinstance(k, str) else getattr(k, "name", None)
            for m in msgs or []:
                role = (
                    m.get("role") if isinstance(m, dict) else getattr(m, "role", None)
                ) or ""
                content = (
                    m.get("content")
                    if isinstance(m, dict)
                    else getattr(m, "content", None)
                )
                if isinstance(content, (bytes, bytearray)):
                    content = content.decode("utf-8", "ignore")
                out.append({"name": name, "role": role, "content": content})
    mh = getattr(up, "message_history", None)
    if isinstance(mh, dict):
        for name, msgs in mh.items():
            for m in msgs or []:
                role = (
                    m.get("role") if isinstance(m, dict) else getattr(m, "role", None)
                ) or ""
                content = (
                    m.get("content")
                    if isinstance(m, dict)
                    else getattr(m, "content", None)
                )
                if isinstance(content, (bytes, bytearray)):
                    content = content.decode("utf-8", "ignore")
                out.append({"name": name, "role": role, "content": content})
    return out


# =========================
# PDF utility
# =========================


def pdf_first_page_to_base64(pdf_path: Path) -> str:
    """把 PDF 首页转成 base64-PNG 字符串（用于前端预览）。"""
    pdf = fitz.open(str(pdf_path))
    page = pdf.load_page(0)
    pix = page.get_pixmap()
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _parse_params(params: Optional[str]) -> Dict[str, Any]:
    if not params or not isinstance(params, str):
        return {}
    # 尝试 0/1/2 次解码
    candidates = [params, unquote(params), unquote_plus(params)]
    for cand in candidates:
        try:
            return json.loads(cand)
        except Exception:
            continue
    # 再保守一点：如果像 "a=1&b=2" 这种 query 风格，也简单兜一下
    kv = {}
    try:
        for pair in params.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                kv[unquote_plus(k)] = unquote_plus(v)
    except Exception:
        pass
    return kv


def extract_params_from_file(py_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    扫描形如:
        xxx = params.get("key", <default_literal>)
    的代码，解析默认值类型与内容。
    返回示例:
      {
        "company":        {"type": "string",   "defaultValue": "apple"},
        "date":           {"type": "date",     "defaultValue": "2025-05-01"},
        "filing_types":   {"type": "string[]", "defaultValue": ["10-K", "10-Q"]},
        "include_amends": {"type": "boolean",  "defaultValue": True},
        "build_marker_pdf": {"type": "boolean","defaultValue": False},
        "from_markdown":  {"type": "boolean",  "defaultValue": True},
      }
    """
    text = py_path.read_text(encoding="utf-8", errors="ignore")

    # 更通用：抓取任意字面量作为默认值（包含跨行列表）
    pattern = re.compile(
        r"""
        (\w+)\s*=\s*params\.get\(\s*
        (['"])(\w+)\2              # key
        \s*,\s*
        (.*?)                      # default expr (non-greedy)
        \s*\)
        """,
        re.VERBOSE | re.DOTALL,
    )

    DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    def infer_type_and_value(default_expr: str) -> (str, Any):
        default_expr = default_expr.strip()
        # 优先用 literal_eval 只解析“安全字面量”
        try:
            val = ast.literal_eval(default_expr)
            # 类型推断
            if isinstance(val, bool):
                return "boolean", val
            if isinstance(val, (int, float)):
                return "number", val
            if isinstance(val, str):
                return ("date" if DATE_PATTERN.match(val) else "string"), val
            if isinstance(val, list):
                if all(isinstance(x, str) for x in val):
                    return "string[]", val
                if all(isinstance(x, (int, float)) for x in val):
                    return "number[]", val
                return "array", val
            if isinstance(val, dict):
                return "object", val
            # 其它少见字面量类型
            return "unknown", val
        except Exception:
            # 兜底：处理 True/False/字符串字面量 & 其它表达式
            if default_expr in ("True", "False"):
                return "boolean", default_expr == "True"
            m = re.match(r"""^(['"])(.*)\1$""", default_expr, re.DOTALL)
            if m:
                s = bytes(m.group(2), "utf-8").decode("unicode_escape")
                return ("date" if DATE_PATTERN.match(s) else "string"), s
            # 实在不是字面量，就当字符串表达式给回去
            return "string", default_expr

    out: Dict[str, Dict[str, Any]] = {}
    for _full_var, _q, key, default_expr in pattern.findall(text):
        _type, _value = infer_type_and_value(default_expr)
        out[key] = {"type": _type, "defaultValue": _value}

    return out


# =========================
# Script output utilities
# =========================


def create_output_directory(base_dir: Path, script_name: str) -> Path:
    """
    Create a timestamped output directory for script results.

    Args:
        base_dir: Base directory (usually backend directory)
        script_name: Name of the script (e.g., 'agent_rag_earnings_call_sec_filings')

    Returns:
        Path to the created output directory
    """
    from datetime import datetime

    date = datetime.now().strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    folder_name = f"{script_name}_{timestamp}"
    result_path = base_dir / "static" / "output" / date / folder_name
    result_path.mkdir(parents=True, exist_ok=True)
    return result_path


def save_output_files(
    output_path: Path,
    script_name: str,
    params: Dict[str, Any],
    messages: List[Any],
    queries: Optional[List[str]] = None,
    additional_data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Save script output files in a standardized format.

    Args:
        output_path: Directory to save files
        script_name: Name of the script
        params: Script parameters
        messages: Chat messages or results
        queries: List of queries (if applicable)
        additional_data: Additional data to save
    """
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    # Prepare output data
    output_data = {
        "script_name": script_name,
        "timestamp": timestamp,
        "parameters": params,
        "messages": [],
        "queries": queries or [],
        "additional_data": additional_data or {},
    }

    # Process messages
    for i, message in enumerate(messages):
        if hasattr(message, "chat_history") and message.chat_history:
            # AutoGen chat result
            chat_data = {"message_index": i, "chat_history": []}
            for msg in message.chat_history:
                if isinstance(msg, dict):
                    chat_data["chat_history"].append(msg)
                else:
                    chat_data["chat_history"].append(str(msg))
            output_data["messages"].append(chat_data)
        elif isinstance(message, dict):
            # Direct dictionary message
            output_data["messages"].append({"message_index": i, "content": message})
        else:
            # String or other format
            output_data["messages"].append(
                {"message_index": i, "content": str(message)}
            )

    # Save JSON file
    json_file = output_path / "results.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    # Save summary text file
    summary_file = output_path / "summary.txt"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(f"{script_name.replace('_', ' ').title()} Results\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Parameters: {json.dumps(params, indent=2)}\n\n")

        if queries:
            f.write(f"Queries ({len(queries)}):\n")
            for i, query in enumerate(queries, 1):
                f.write(f"{i}. {query}\n")
            f.write("\n")

        f.write(f"Messages: {len(messages)} items\n")
        f.write(f"Output Directory: {output_path}\n\n")

        if additional_data:
            f.write("Additional Data:\n")
            for key, value in additional_data.items():
                f.write(f"- {key}: {value}\n")

    print(f"Results saved to: {output_path}")


def get_script_result(
    messages: List[Any],
    output_path: Optional[Path] = None,
    error: Optional[str] = None,
    preview: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a standardized script result dictionary.

    Args:
        messages: List of messages or results
        output_path: Path where output files are saved
        error: Error message (if any)
        preview: Preview data (e.g., base64 image)
        additional_data: Additional data to include

    Returns:
        Standardized result dictionary
    """
    result = {"result": messages}

    if output_path:
        result["output_path"] = str(output_path)

    if error:
        result["error"] = error

    if preview:
        result["preview"] = preview

    if additional_data:
        result.update(additional_data)

    return result
