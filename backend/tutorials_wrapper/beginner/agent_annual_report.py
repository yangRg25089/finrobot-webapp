# # Financial Analyst Agent for Annual Report Writing

# In this demo, we introduce an agent that can analyze financial report.

import os
from textwrap import dedent

from common.utils import (
    build_lang_directive,
    collect_generated_files,
    create_llm_config,
    create_output_directory,
    get_script_result,
    setup_and_chat_with_agents,
)
from finrobot.agents.workflow import SingleAssistantShadow
from finrobot.utils import register_keys_from_json

# After importing all the necessary packages and functions, we also need the config for OpenAI & SecApi & FMPApi here.
# - for openai configuration, rename OAI_CONFIG_LIST_sample to OAI_CONFIG_LIST and replace the api keys
# - for Sec_api & FMP_api configuration, rename config_api_keys_sample to config_api_keys and replace the api keys


def run(params: dict, lang: str) -> dict:

    company = params.get("company", "apple")
    fyear = params.get("fyear", "2025")
    _AI_model = params.get("_AI_model", "gemini-2.5-flash")
    lang_snippet = build_lang_directive(lang)

    from pathlib import Path

    current_dir = Path(__file__).resolve().parent
    config_path = current_dir.parent.parent / "OAI_CONFIG_LIST"
    config_api_keys_path = current_dir.parent.parent / "config_api_keys"

    llm_config = create_llm_config(
        config_path=str(config_path),
        model_name=_AI_model,
        temperature=0,
        timeout=120,
    )

    register_keys_from_json(str(config_api_keys_path))

    # Save output files using common utilities
    result_path = create_output_directory()
    work_dir = str(result_path)
    os.makedirs(work_dir, exist_ok=True)

    assistant = SingleAssistantShadow(
        "Expert_Investor",
        llm_config,
        max_consecutive_auto_reply=3,
        human_input_mode="NEVER",
    )

    prompt = dedent(
        f"""
        With the tools you've been provided, write an annual report based on {company}'s {fyear} 10-k report, format it into a pdf.
        Pay attention to the followings:
        - Explicitly explain your working plan before you kick off.
        - Use tools one by one for clarity, especially when asking for instructions. 
        - All your file operations should be done in "{work_dir}". 
        - Display any image in the chat once generated.
        - All the paragraphs should combine between 400 and 450 words, don't generate the pdf until this is explicitly fulfilled.
        {lang_snippet}
    """
    )

    # 使用共通方法处理对话
    messages = setup_and_chat_with_agents(
        assistant_or_user_proxy=assistant, prompt=prompt
    )

    generated_files = collect_generated_files(result_path)

    return get_script_result(
        messages=messages,
        additional_data={
            "generated_files": generated_files,
        },
        prompt=prompt,
    )
