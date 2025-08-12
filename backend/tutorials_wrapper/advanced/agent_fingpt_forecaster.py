from __future__ import annotations

from pathlib import Path

import autogen
from autogen.cache import Cache
from common.utils import build_lang_directive, setup_and_chat_with_raw_agents
from finrobot.data_source import FinnHubUtils, YFinanceUtils
from finrobot.utils import get_current_date, register_keys_from_json


def run(params: dict, lang: str):
    """
    兼容本项目的脚本入口：
    - params: {"company": "APPLE", ...}
    - lang: 未使用（保持签名一致）
    返回 {"result": messages}
    """
    company = params.get("company", "APPLE")
    _AI_model = params.get("_AI_model", "gemini-2.5-flash")
    lang_snippet = build_lang_directive(lang)

    current_dir = Path(__file__).resolve().parent
    config_path = current_dir.parent.parent / "OAI_CONFIG_LIST"
    config_api_keys_path = current_dir.parent.parent / "config_api_keys"

    config_list = autogen.config_list_from_json(
        str(config_path),
        filter_dict={"model": [_AI_model]},
    )
    llm_config = {"config_list": config_list, "timeout": 120, "temperature": 0}

    register_keys_from_json(str(config_api_keys_path))

    analyst = autogen.AssistantAgent(
        name="Market_Analyst",
        system_message=(
            "As a Market Analyst, one must possess strong analytical and problem-solving abilities, "
            "collect necessary financial information and aggregate them based on client's requirement."
            "For coding tasks, only use the functions you have been provided with. "
            "Reply TERMINATE when the task is done."
        ),
        llm_config=llm_config,
    )

    user_proxy = autogen.UserProxyAgent(
        name="User_Proxy",
        is_termination_msg=lambda x: x.get("content", "")
        and x.get("content", "").endswith("TERMINATE"),
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        code_execution_config={
            "work_dir": "coding",
            "use_docker": False,
        },  # 若可用 docker，可改为 True
    )

    # Register toolkits（保持原有工具注册）
    from finrobot.toolkits import register_toolkits

    tools = [
        {
            "function": FinnHubUtils.get_company_profile,
            "name": "get_company_profile",
            "description": "get a company's profile information",
        },
        {
            "function": FinnHubUtils.get_company_news,
            "name": "get_company_news",
            "description": "retrieve market news related to designated company",
        },
        {
            "function": FinnHubUtils.get_basic_financials,
            "name": "get_financial_basics",
            "description": "get latest financial basics for a designated company",
        },
        {
            "function": YFinanceUtils.get_stock_data,
            "name": "get_stock_data",
            "description": "retrieve stock price data for designated ticker symbol",
        },
    ]
    register_toolkits(tools, analyst, user_proxy)

    # 使用共通方法处理原生 agents 对话
    prompt = (
        f"Use all the tools provided to retrieve information available for {company} upon {get_current_date()}. "
        f"Analyze the positive developments and potential concerns of {company} "
        "with 2-4 most important factors respectively and keep them concise. Most factors should be inferred from company related news. "
        f"Then make a rough prediction (e.g. up/down by 2-3%) of the {company} stock price movement for next week. "
        "Provide a summary analysis to support your prediction."
        f"{lang_snippet}"
    )

    # 注意：这里需要传递 cache 参数
    with Cache.disk() as cache:
        messages = setup_and_chat_with_raw_agents(
            user_proxy, analyst, prompt, cache=cache
        )
    return {"result": messages}
