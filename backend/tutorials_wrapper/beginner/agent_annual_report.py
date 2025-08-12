# # Financial Analyst Agent for Annual Report Writing

# In this demo, we introduce an agent that can analyze financial report.

import os
from textwrap import dedent

import autogen
from common.utils import (
    build_lang_directive,
    extract_all,
    get_script_result,
    pdf_first_page_to_base64,
)
from finrobot.agents.workflow import SingleAssistantShadow
from finrobot.utils import register_keys_from_json

# After importing all the necessary packages and functions, we also need the config for OpenAI & SecApi & FMPApi here.
# - for openai configuration, rename OAI_CONFIG_LIST_sample to OAI_CONFIG_LIST and replace the api keys
# - for Sec_api & FMP_api configuration, rename config_api_keys_sample to config_api_keys and replace the api keys


def run(params: dict, lang: str) -> dict:

    company = params.get("company", "apple")
    fyear = params.get("fyear", "2023")
    _AI_model = params.get("_AI_model", "gemini-2.5-flash")
    lang_snippet = build_lang_directive(lang)

    from pathlib import Path

    current_dir = Path(__file__).resolve().parent
    config_path = current_dir.parent.parent / "OAI_CONFIG_LIST"
    config_api_keys_path = current_dir.parent.parent / "config_api_keys"
    report_path = current_dir.parent.parent / "report"

    llm_config = {
        "config_list": autogen.config_list_from_json(
            str(config_path),
            filter_dict={"model": [_AI_model]},
        ),
        "timeout": 120,
        "temperature": 0.5,
        "max_tokens": 1024,
    }

    register_keys_from_json(str(config_api_keys_path))

    # Intermediate results will be saved in this directory
    work_dir = str(report_path)
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
    """
    )

    assistant.chat(prompt, use_cache=True, max_turns=50, summary_method="last_msg")

    messages = extract_all(assistant.user_proxy)

    pdf_files = sorted(
        [p for p in report_path.glob("*.pdf")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not pdf_files:
        return get_script_result(
            messages=messages, error="PDF not generated. Check agent execution."
        )

    latest_pdf = pdf_files[0]
    preview_b64 = pdf_first_page_to_base64(latest_pdf)

    return get_script_result(
        messages=messages,
        preview=preview_b64,
        additional_data={"pdf_path": str(latest_pdf)},
    )
