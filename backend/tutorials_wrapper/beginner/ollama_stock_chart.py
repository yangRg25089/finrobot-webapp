import os
from datetime import datetime
from pathlib import Path

from autogen import AssistantAgent, UserProxyAgent
from common.runtime import guard_run
from common.utils import (
    build_lang_directive,
    create_llm_config,
    create_output_directory,
    get_script_result,
    setup_and_chat_with_raw_agents,
)


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
    _AI_model = params.get("_AI_model", "qwen2.5-coder:14b")
    lang_snippet = build_lang_directive(lang)

    from pathlib import Path

    current_dir = Path(__file__).resolve().parent
    config_path = current_dir.parent.parent / "OAI_CONFIG_LIST"

    # 使用共通方法创建 LLM 配置，自动适配不同模型类型
    llm_config = create_llm_config(
        config_path=str(config_path), model_name=_AI_model, temperature=0
    )

    assistant = AssistantAgent(
        "assistant",
        llm_config=llm_config,
        system_message=(
            "You are a non-conversational code assistant. "
            "Do NOT greet or ask questions. "
            "Output exactly one Python code block that performs the task; "
            "no extra text outside the code block."
        ),
    )

    current_dir = Path(__file__).resolve().parent
    result_path = create_output_directory()

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

    # 使用共通方法处理原生 agents 对话
    messages = setup_and_chat_with_raw_agents(
        user_proxy, assistant, prompt, max_turns=10
    )

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
        return get_script_result(
            messages=messages,
            error=last_err or "No image generated.",
            additional_data={
                "result_folder": web_folder,
                "result_images": images,
            },
        )

    return get_script_result(
        messages=messages,
        additional_data={
            "result_folder": web_folder,
            "result_images": images,
        },
    )
