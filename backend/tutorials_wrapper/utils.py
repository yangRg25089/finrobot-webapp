from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from typing import Any, Dict, Final, List

import fitz  # PyMuPDF
from PIL import Image

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


def _to_plain_content(content: Any) -> Any:
    if isinstance(content, (bytes, bytearray)):
        return content.decode("utf-8", "ignore")
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict):
                parts.append(c.get("text") or c.get("content") or c.get("value") or "")
            else:
                parts.append(str(c))
        return "\n".join([p for p in parts if p])
    if isinstance(content, (str, int, float, bool, type(None), dict)):
        return content
    try:
        return json.loads(json.dumps(content, default=str))
    except Exception:
        return str(content)


def _normalize_msg(m: Any, conv_name: str | None) -> Dict[str, Any]:
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
                    if not s or s.upper() == "TERMINATE":
                        continue
                elif isinstance(content, list):
                    # 全部元素为假值则跳过（[], [""], [None], 等）
                    if not any(bool(x) for x in content):
                        continue
                # 其他类型按有值处理
                out.append(msg)

    return out


def extract_all(up) -> list[dict]:
    """
    提取 user_agent 中的全部对话消息，不区分 assistant。
    返回：[{role, name, tool_name, content}, ...]
    """
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


def pdf_first_page_to_base64(pdf_path: Path) -> str:
    """把 PDF 首页转成 base64-PNG 字符串"""
    pdf = fitz.open(str(pdf_path))
    page = pdf.load_page(0)
    pix = page.get_pixmap()
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
