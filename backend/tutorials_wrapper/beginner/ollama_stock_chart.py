import os
from datetime import datetime
from pathlib import Path

from autogen import AssistantAgent, UserProxyAgent
from tutorials_wrapper.runtime import guard_run
from tutorials_wrapper.utils import build_lang_directive, extract_conversation


def _has_image(work_dir: Path) -> bool:
    exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
    try:
        for name in os.listdir(work_dir):
            if Path(name).suffix.lower() in exts and (work_dir / name).is_file():
                return True
    except Exception:
        pass
    return False


def is_term_msg_factory(work_dir: Path):
    def _term(msg):
        # 名称/角色判断：只对 user_proxy 的输出启用终止判断
        name = (msg.get("name") or msg.get("from") or "").lower()
        role = (msg.get("role") or "").lower()

        content = msg.get("content") or ""
        if not isinstance(content, str):
            return False

        # 1) 忽略 assistant 的消息（通常包含代码块）
        if "assistant" in name or role == "assistant":
            return False

        # 2) 忽略带代码围栏的消息（``` 出现即视为“还在给代码”，不是执行输出）
        if "```" in content:
            return False

        # 3) 真正的执行输出：认成功/失败哨兵
        if "SAVED_IMAGE:" in content:
            return True
        if content.startswith("ERROR:"):
            return True

        # 4) 容错：若目录里已经有图片，哪怕没打印哨兵也允许结束
        if "TERMINATE" in content and _has_image(work_dir):
            return True

        return False

    return _term


@guard_run(reraise=True)
def run(params: dict, lang: str) -> dict:
    company = params.get("company", "AAPL")
    year = params.get("year", "2025")
    lang_snippet = build_lang_directive(lang)

    config_list = [
        {
            "model": "qwen2.5-coder:14b",
            "base_url": "http://127.0.0.1:11434/v1/",
            "api_key": "ollama",
        }
    ]

    assistant = AssistantAgent(
        "assistant",
        llm_config={"config_list": config_list, "temperature": 0},
        system_message=(
            "You are a non-conversational code assistant. "
            "Do NOT greet or ask questions. "
            "Output exactly one Python code block that performs the task; "
            "no extra text outside the code block."
        ),
    )

    current_dir = Path(__file__).resolve().parent
    date = datetime.now().strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    folder_name = f"ollama_stock_chart_{timestamp}"
    result_path = current_dir.parent.parent / "static" / "output" / date / folder_name
    result_path.mkdir(parents=True, exist_ok=True)

    user_proxy = UserProxyAgent(
        "user_proxy",
        code_execution_config={"work_dir": str(result_path), "use_docker": False},
        human_input_mode="NEVER",
        default_auto_reply="",  # 不要客套自动回帖
        max_consecutive_auto_reply=8,  # 给足回合跑代码
        is_termination_msg=is_term_msg_factory(result_path),
    )

    out_path = (result_path / f"{company}_{year}.png").as_posix()

    prompt = f"""
        You will write and run Python code in a headless environment. DO NOT greet or ask questions.
        Rules:
        - Use ticker "{company}", year {year}, download with yfinance: start="{year}-01-01", end="{year}-12-31", progress=False.
        - Use matplotlib.use("Agg"); DO NOT call plt.show().
        - Plot Close vs Date; tight_layout(); save PNG to exactly: "{out_path}".
        - On success, print exactly: "SAVED_IMAGE: {out_path}"
        - On failure, print exactly: "ERROR: <message>"
        - Return exactly ONE Python code block and nothing else. NO extra text outside the code block.

        {lang_snippet}
        """.strip()

    user_proxy.initiate_chat(assistant, message=prompt, max_turns=10)

    messages = extract_conversation(user_proxy)

    # 产物与可访问 URL
    static_root = (current_dir.parent.parent / "static").resolve()
    rel = result_path.resolve().relative_to(static_root)
    web_prefix = f"/static/{rel.as_posix()}"
    web_folder = web_prefix + "/"

    exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
    images = [
        f"{web_prefix}/{p.name}"
        for p in sorted(result_path.iterdir())
        if p.is_file() and p.suffix.lower() in exts
    ]

    # 如果没生成图片，把最后的错误回传，避免前端“无限等”
    if not images:
        last_err = next(
            (
                m.get("content")
                for m in reversed(messages)
                if isinstance(m.get("content"), str)
                and m["content"].startswith("ERROR:")
            ),
            None,
        )
        return {
            "result": messages,
            "result_folder": web_folder,
            "result_images": images,
            "error": last_err or "No image generated.",
        }

    return {
        "result": messages,
        "result_folder": web_folder,
        "result_images": images,
    }
