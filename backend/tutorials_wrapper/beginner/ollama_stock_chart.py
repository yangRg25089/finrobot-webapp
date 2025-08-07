from datetime import datetime

from autogen import AssistantAgent, UserProxyAgent
from tutorials_wrapper.utils import build_lang_directive, extract_conversation


def run(params: dict, lang: str) -> dict:

    company = params.get("company", "apple")
    year = params.get("year", "2025")
    lang_snippet = build_lang_directive(lang)

    config_list = [
        {
            "model": "llama3",
            "base_url": "http://127.0.0.1:11434/v1/",
            "api_key": "ollama",
        }
    ]

    assistant = AssistantAgent("assistant", llm_config={"config_list": config_list})

    from pathlib import Path

    current_dir = Path(__file__).resolve().parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    folder_name = f"ollama_stock_chart_{timestamp}"

    result_path = current_dir.parent.parent / "static" / folder_name

    result_path.mkdir(parents=True, exist_ok=True)

    user_proxy = UserProxyAgent(
        "user_proxy",
        code_execution_config={"work_dir": str(result_path), "use_docker": False},
        human_input_mode="NEVER",
    )

    user_proxy.initiate_chat(
        assistant,
        message=f"Plot a chart of {company} stock price change in {year} and save in a file. Get information using yfinance."
        f"{lang_snippet}",
    )

    messages = extract_conversation(user_proxy)

    return {"result": messages}
