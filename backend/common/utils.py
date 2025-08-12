from __future__ import annotations

import ast
import base64
import io
import json
import re
from pathlib import Path
from typing import Any, Dict, Final, List, Optional
from urllib.parse import unquote, unquote_plus

# Optional imports for PDF processing
try:
    import fitz  # PyMuPDF

    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False
    print("Warning: PyMuPDF (fitz) not installed. PDF processing will be disabled.")

try:
    from PIL import Image

    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: PIL (Pillow) not installed. Image processing will be disabled.")

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


def setup_and_chat_with_agents(
    assistant_or_user_proxy,
    assistant_agent=None,
    prompt: str = None,
    script_name: str = None,
    save_history: bool = True,
    **chat_kwargs,
) -> list[dict]:
    """
    统一的 agent 对话方法，支持 SingleAssistantShadow 和原生 agents

    Args:
        assistant_or_user_proxy: SingleAssistantShadow 实例或 UserProxyAgent 实例
        assistant_agent: AssistantAgent 实例（仅当第一个参数是 UserProxyAgent 时需要）
        prompt: 对话提示
        script_name: 脚本名称，用于历史保存
        save_history: 是否保存对话历史
        **chat_kwargs: 传递给 initiate_chat 的额外参数

    Returns:
        list[dict]: 对话历史消息列表
    """
    # 检测是 SingleAssistantShadow 还是原生 agents
    is_single_assistant = hasattr(assistant_or_user_proxy, "user_proxy") and hasattr(
        assistant_or_user_proxy, "assistant"
    )

    if is_single_assistant:
        # SingleAssistantShadow 模式
        assistant = assistant_or_user_proxy
        up = assistant.user_proxy
        aa = assistant.assistant

        # 避免旧历史干扰
        if hasattr(up, "reset"):
            up.reset()
        if hasattr(aa, "reset"):
            aa.reset()

        # 适当放大自动回复轮数，避免未收尾
        if hasattr(up, "max_consecutive_auto_reply"):
            current_value = getattr(up, "max_consecutive_auto_reply", 3)
            if not callable(current_value):
                up.max_consecutive_auto_reply = max(6, current_value)

        # 进行对话
        up.initiate_chat(aa, message=prompt, **chat_kwargs)

        # 提取对话历史
        messages = extract_all(up)

    else:
        # 原生 agents 模式
        user_proxy = assistant_or_user_proxy

        if assistant_agent is None:
            raise ValueError("assistant_agent is required when using raw agents")

        # 避免旧历史干扰
        if hasattr(user_proxy, "reset"):
            user_proxy.reset()
        if hasattr(assistant_agent, "reset"):
            assistant_agent.reset()

        # 适当放大自动回复轮数，避免未收尾
        if hasattr(user_proxy, "max_consecutive_auto_reply"):
            current_value = getattr(user_proxy, "max_consecutive_auto_reply", 3)
            if not callable(current_value):
                user_proxy.max_consecutive_auto_reply = max(6, current_value)

        # 进行对话
        user_proxy.initiate_chat(assistant_agent, message=prompt, **chat_kwargs)

        # 提取对话历史
        messages = extract_conversation(user_proxy)

    # 保存对话历史
    if save_history and messages:
        try:
            save_conversation_history(messages, script_name, prompt)
        except Exception as e:
            # 历史保存失败不应该影响主流程
            print(f"Warning: Failed to save conversation history: {e}")

    return messages


def setup_and_chat_with_raw_agents(
    user_proxy, assistant_agent, prompt: str, **chat_kwargs
) -> list[dict]:
    """
    兼容性方法：设置原生 autogen agents 并进行对话

    Args:
        user_proxy: autogen.UserProxyAgent 实例
        assistant_agent: autogen.AssistantAgent 实例
        prompt: 对话提示
        **chat_kwargs: 传递给 initiate_chat 的额外参数

    Returns:
        list[dict]: 对话历史消息列表
    """
    return setup_and_chat_with_agents(
        assistant_or_user_proxy=user_proxy,
        assistant_agent=assistant_agent,
        prompt=prompt,
        save_history=True,
        **chat_kwargs,
    )


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
    if not HAS_FITZ:
        print("Warning: PyMuPDF not available, cannot process PDF")
        return ""

    if not HAS_PIL:
        print("Warning: PIL not available, cannot process images")
        return ""

    try:
        pdf = fitz.open(str(pdf_path))
        page = pdf.load_page(0)
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception as e:
        print(f"Error converting PDF to base64: {e}")
        return ""


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


def create_output_directory(
    output_subdir: str = "output", script_name: str = None
) -> Path:
    """
    Create a timestamped output directory for script results.

    Args:
        output_subdir: Subdirectory name under static (default: "output")
        script_name: Name of the script. If None, auto-detect from calling script

    Returns:
        Path to the created output directory
    """
    import inspect
    from datetime import datetime
    from pathlib import Path

    # Auto-detect script name if not provided
    if script_name is None:
        frame = inspect.currentframe()
        try:
            # Go up the call stack to find the calling script
            caller_frame = frame.f_back
            while caller_frame:
                filename = caller_frame.f_code.co_filename
                if filename != __file__:  # Skip this utils file
                    script_name = Path(filename).stem
                    break
                caller_frame = caller_frame.f_back
            else:
                script_name = "unknown_script"
        finally:
            del frame

    date = datetime.now().strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    # Use current working directory as base
    base_dir = Path.cwd()
    result_path = base_dir / "static" / output_subdir / script_name / date / timestamp
    result_path.mkdir(parents=True, exist_ok=True)
    return result_path


def collect_generated_files(output_path: Path) -> Dict[str, Any]:
    """
    收集输出目录中生成的所有文件，并生成可访问的 URL

    Args:
        output_path: 输出目录路径

    Returns:
        包含文件信息的字典
    """
    import os
    from datetime import datetime
    from pathlib import Path

    if not output_path.exists():
        return {"files": [], "image_urls": [], "file_urls": [], "total_files": 0}

    # 获取静态文件根目录
    backend_dir = Path.cwd()
    static_root = backend_dir / "static"

    # 计算相对于 static 目录的路径
    try:
        rel_path = output_path.resolve().relative_to(static_root.resolve())
        web_prefix = f"/static/{rel_path.as_posix()}"
    except ValueError:
        # 如果路径不在 static 目录下，使用绝对路径
        web_prefix = f"/static/output"

    files_info = []
    image_urls = []
    file_urls = []

    # 支持的图片格式
    image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}

    # 遍历输出目录中的所有文件
    for file_path in output_path.rglob("*"):
        if file_path.is_file():
            try:
                stat = file_path.stat()
                file_size = stat.st_size
                modified_time = datetime.fromtimestamp(stat.st_mtime)

                # 计算相对于输出目录的路径
                rel_file_path = file_path.relative_to(output_path)
                file_url = f"{web_prefix}/{rel_file_path.as_posix()}"

                file_info = {
                    "name": file_path.name,
                    "path": rel_file_path.as_posix(),
                    "full_path": str(file_path),
                    "size": file_size,
                    "size_human": format_file_size(file_size),
                    "modified_time": modified_time.isoformat(),
                    "extension": file_path.suffix.lower(),
                    "url": file_url,
                }

                files_info.append(file_info)

                # 分类文件
                if file_path.suffix.lower() in image_extensions:
                    image_urls.append(file_url)
                else:
                    file_urls.append(file_url)

            except (OSError, ValueError) as e:
                # 跳过无法访问的文件
                continue

    # 按修改时间排序（最新的在前）
    files_info.sort(key=lambda x: x["modified_time"], reverse=True)

    return {
        "files": files_info,
        "image_urls": image_urls,
        "file_urls": file_urls,
        "total_files": len(files_info),
        "output_directory": str(output_path),
        "web_prefix": web_prefix,
    }


def format_file_size(size_bytes: int) -> str:
    """
    将字节数格式化为人类可读的文件大小
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math

    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def create_llm_config(
    config_path: str,
    model_name: str,
    temperature: float = 0.5,
    timeout: int = 120,
    max_tokens: int = None,
) -> dict:
    """
    创建适用于不同模型类型的 LLM 配置

    Args:
        config_path: OAI_CONFIG_LIST 文件路径
        model_name: 模型名称
        temperature: 温度参数
        timeout: 超时时间
        max_tokens: 最大 token 数

    Returns:
        适配的 LLM 配置字典
    """
    import json
    from pathlib import Path

    import autogen

    # 读取配置文件
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file, "r") as f:
        all_configs = json.load(f)

    # 查找指定模型的配置
    model_config = None
    for config in all_configs:
        if config.get("model") == model_name:
            model_config = config.copy()
            break

    if not model_config:
        raise ValueError(f"Model '{model_name}' not found in config file")

    # 根据 api_type 处理不同类型的模型
    api_type = model_config.get("api_type", "openai")

    if api_type == "ollama":
        # Ollama 本地模型配置
        config_list = [
            {
                "model": model_config["model"],
                "base_url": model_config["base_url"],
                "api_key": model_config["api_key"],
            }
        ]

        llm_config = {
            "config_list": config_list,
            "temperature": temperature,
        }

        # Ollama 通常不需要 timeout 和 max_tokens
        if timeout and timeout != 120:  # 只有非默认值才设置
            llm_config["timeout"] = timeout

    else:
        # OpenAI API 类型模型配置
        config_list = autogen.config_list_from_json(
            config_path,
            filter_dict={"model": [model_name]},
        )

        if not config_list:
            raise ValueError(f"No valid config found for model '{model_name}'")

        llm_config = {
            "config_list": config_list,
            "temperature": temperature,
            "timeout": timeout,
        }

        # 只有指定了 max_tokens 才添加
        if max_tokens:
            llm_config["max_tokens"] = max_tokens

    return llm_config


def save_conversation_history(
    messages: List[dict], script_name: str = None, prompt: str = None
) -> Path:
    """
    保存对话历史到 history 目录

    Args:
        messages: 对话消息列表
        script_name: 脚本名称
        prompt: 对话提示

    Returns:
        保存的文件路径
    """
    import inspect
    import json
    from datetime import datetime
    from pathlib import Path

    # 自动检测脚本名称
    if script_name is None:
        frame = inspect.currentframe()
        try:
            # 向上查找调用栈，找到脚本文件
            caller_frame = frame.f_back
            while caller_frame:
                filename = caller_frame.f_code.co_filename
                if filename != __file__ and not filename.endswith("utils.py"):
                    script_name = Path(filename).stem
                    break
                caller_frame = caller_frame.f_back
            else:
                script_name = "unknown_script"
        finally:
            del frame

    # 创建历史目录
    history_dir = create_output_directory("history", script_name)

    # 创建历史记录数据
    history_data = {
        "timestamp": datetime.now().isoformat(),
        "script_name": script_name,
        "prompt": prompt,
        "messages": messages,
        "message_count": len(messages),
    }

    # 保存到 JSON 文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"conversation_{timestamp}.json"
    file_path = history_dir / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)

    # 清理旧的历史文件，只保留最新的5个
    cleanup_old_history(history_dir.parent, max_keep=5)

    return file_path


def cleanup_old_history(history_base_dir: Path, max_keep: int = 5):
    """
    清理旧的历史记录，只保留最新的几个版本

    Args:
        history_base_dir: 历史记录基础目录
        max_keep: 最多保留的版本数
    """
    if not history_base_dir.exists():
        return

    # 获取所有日期目录
    date_dirs = []
    for item in history_base_dir.iterdir():
        if item.is_dir() and item.name.isdigit() and len(item.name) == 8:
            date_dirs.append(item)

    # 按日期排序（最新的在前）
    date_dirs.sort(key=lambda x: x.name, reverse=True)

    # 删除超出保留数量的目录
    for old_dir in date_dirs[max_keep:]:
        try:
            import shutil

            shutil.rmtree(old_dir)
            print(f"Cleaned up old history: {old_dir}")
        except Exception as e:
            print(f"Failed to cleanup {old_dir}: {e}")


def load_conversation_history(script_name: str = None) -> List[dict]:
    """
    加载指定脚本的对话历史

    Args:
        script_name: 脚本名称，如果为 None 则自动检测

    Returns:
        历史记录列表，每个元素包含完整的对话数据
    """
    import inspect
    import json
    from pathlib import Path

    # 自动检测脚本名称
    if script_name is None:
        frame = inspect.currentframe()
        try:
            caller_frame = frame.f_back
            while caller_frame:
                filename = caller_frame.f_code.co_filename
                if filename != __file__ and not filename.endswith("utils.py"):
                    script_name = Path(filename).stem
                    break
                caller_frame = caller_frame.f_back
            else:
                script_name = "unknown_script"
        finally:
            del frame

    # 构建历史目录路径
    base_dir = Path.cwd()
    history_base_dir = base_dir / "static" / "history" / script_name

    if not history_base_dir.exists():
        return []

    history_records = []

    # 遍历所有日期目录
    for date_dir in sorted(history_base_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue

        # 遍历时间戳目录
        for timestamp_dir in sorted(date_dir.iterdir(), reverse=True):
            if not timestamp_dir.is_dir():
                continue

            # 查找 JSON 文件
            for json_file in timestamp_dir.glob("conversation_*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        data["file_path"] = str(json_file)
                        data["relative_path"] = str(json_file.relative_to(base_dir))
                        history_records.append(data)
                except Exception as e:
                    print(f"Failed to load history file {json_file}: {e}")

    # 按时间戳排序（最新的在前）
    history_records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return history_records


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
