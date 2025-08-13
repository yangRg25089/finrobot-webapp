# # FinGPT-Forecaster Re-implemented with FinRobot

# In this demo, we set up an agent to emulate the behavior of model in the fingpt-forecaster project with AutoGen, which takes a company's ticker symbol, recent basic financials and market news as input and predict its stock movements.
#
# For detail of the original project, check out  [FinGPT-Forecaster](https://github.com/AI4Finance-Foundation/FinGPT/tree/master/fingpt/FinGPT_Forecaster)!  🔥[Demo](https://huggingface.co/spaces/FinGPT/FinGPT-Forecaster), [Medium Blog](https://medium.datadriveninvestor.com/introducing-fingpt-forecaster-the-future-of-robo-advisory-services-50add34e3d3c) & [Model](https://huggingface.co/FinGPT/fingpt-forecaster_dow30_llama2-7b_lora) on Huggingface🤗!
#
# This is a default bot, for more configurable demo, see [advanced tutorial](../tutorials_advanced/agent_fingpt_forecaster.ipynb)

import autogen
from common.utils import (
    build_lang_directive,
    create_llm_config,
    get_script_result,
    setup_and_chat_with_agents,
)
from finrobot.agents.workflow import SingleAssistant
from finrobot.utils import get_current_date, register_keys_from_json

# After importing all the necessary packages and functions, we instantiate a SingleAssistant workflow "Market_Analyst".
# We also need the config for OpenAI & Finnhub here.
# - for openai configuration, rename OAI_CONFIG_LIST_sample to OAI_CONFIG_LIST and replace the api keys
# - for finnhub configuration, rename config_api_keys_sample to config_api_keys and replace the api keys


def run(params: dict, lang: str) -> dict:

    company = params.get("company", "apple")
    _AI_model = params.get("_AI_model", "gemini-2.5-flash")
    lang_snippet = build_lang_directive(lang)

    from pathlib import Path

    current_dir = Path(__file__).resolve().parent
    config_path = current_dir.parent.parent / "OAI_CONFIG_LIST"
    config_api_keys_path = current_dir.parent.parent / "config_api_keys"

    # 使用共通方法创建 LLM 配置，自动适配不同模型类型
    llm_config = create_llm_config(
        config_path=str(config_path),
        model_name=_AI_model,
        temperature=0,
        timeout=120,
        max_tokens=1024,
    )

    # Register FINNHUB API keys
    register_keys_from_json(str(config_api_keys_path))

    # Define the assistant, and simply start chatting!

    assitant = SingleAssistant(
        "Market_Analyst",
        llm_config,
        # set to "ALWAYS" if you want to chat instead of simply receiving the prediciton
        human_input_mode="NEVER",
    )
    prompt = (
        f"Use all the tools provided to retrieve information available for {company} upon {get_current_date()}. Analyze the positive developments and potential concerns of {company} "
        "with 2-4 most important factors respectively and keep them concise. Most factors should be inferred from company related news. "
        f"Then make a rough prediction (e.g. up/down by 2-3%) of the {company} stock price movement for next week. Provide a summary analysis to support your prediction."
        f"{lang_snippet}"
    )

    # 使用共通方法处理对话，自动保存历史记录
    messages = setup_and_chat_with_agents(
        assistant_or_user_proxy=assitant,
        prompt=prompt,
        script_name="agent_fingpt_forecaster",
        save_history=True,
    )
    return get_script_result(
        messages=messages,
        prompt=prompt,
    )
