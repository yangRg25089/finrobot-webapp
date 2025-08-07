import autogen
from autogen import AssistantAgent, UserProxyAgent
from finrobot.data_source import YFinanceUtils
from finrobot.utils import get_current_date, register_keys_from_json
from pyexpat.errors import messages
from tutorials_wrapper.utils import build_lang_directive, extract_conversation


def run(params: dict, lang: str) -> dict:

    company = params.get("company", "apple")
    date = params.get("date", "2025-05-01")
    _AI_model = params.get("_AI_model", "gemini-2.5-flash")
    lang_snippet = build_lang_directive(lang)

    from pathlib import Path

    current_dir = Path(__file__).resolve().parent

    config_path = current_dir.parent.parent / "OAI_CONFIG_LIST"
    config_api_keys_path = current_dir.parent.parent / "config_api_keys"

    llm_config = {
        "config_list": autogen.config_list_from_json(
            str(config_path),
            filter_dict={"model": [_AI_model]},
        ),
        "timeout": 120,
        "temperature": 0,
        "max_tokens": 1024,  # 控制生成长度
    }

    register_keys_from_json(str(config_api_keys_path))

    analyst = AssistantAgent(
        name="Market_Analyst",
        llm_config=llm_config,
    )

    user_proxy = UserProxyAgent(
        "user_proxy",
        code_execution_config=False,
        max_consecutive_auto_reply=3,
        is_termination_msg=lambda x: x.get("content", "")
        and "TERMINATE" in x.get("content", ""),
        human_input_mode="NEVER",
    )

    from finrobot.toolkits import register_toolkits

    tools = [
        {
            "function": YFinanceUtils.get_stock_data,
            # "function": FinnHubUtils.get_company_news,
            "name": "get_stock_news",
            "description": "retrieve stock information related to designated company",
        }
    ]
    register_toolkits(tools, analyst, user_proxy)

    user_proxy.initiate_chat(
        analyst,
        message=f"What is stock price available for {company} from {date} upon {get_current_date()}. Please analyze possible causes of the recent trend and predict short-term movement (e.g. next 5 trading days).Please summarize the trend and say TERMINATE when done."
        f"{lang_snippet}",
    )

    messages = extract_conversation(user_proxy)

    return {"result": messages}
