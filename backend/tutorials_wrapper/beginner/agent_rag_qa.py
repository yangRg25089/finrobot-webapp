# # RetrieveChat based FinRobot-RAG

# In this demo, we showcase the RAG usecase of our finrobot, which inherits from autogen's RetrieveChat implementation.
#
#
# Instead of using `RetrieveUserProxyAgent` directly, we register the context retrieval as a function for our bots.
# For detailed implementation, refer to [rag function](../finrobot/functional/rag.py) and [rag workflow](../finrobot/agents/workflow.py) of `SingleAssistantRAG`

import autogen
from finrobot.agents.workflow import SingleAssistantRAG
from tutorials_wrapper.utils import build_lang_directive, extract_all

# for openai configuration, rename OAI_CONFIG_LIST_sample to OAI_CONFIG_LIST and replace the api keys


def run(params: dict, lang: str) -> dict:

    company = params.get("company", "apple")

    question1 = params.get(
        "question1", "How's msft's 2023 income? Provide with some analysis."
    )

    question2 = params.get(
        "question2", "How's msft's 2023 income? Provide with some analysis."
    )
    _AI_model = params.get("_AI_model", "gemini-2.5-flash")
    lang_snippet = build_lang_directive(lang)

    from pathlib import Path

    current_dir = Path(__file__).resolve().parent
    config_path = current_dir.parent.parent / "OAI_CONFIG_LIST"
    report_path1 = current_dir.parent.parent / "report/Microsoft_Annual_Report_2023.pdf"

    report_path2 = (
        current_dir.parent.parent / "report/2023-07-27_10-K_msft-20230630.htm.pdf"
    )

    # Read OpenAI API keys from a JSON file
    llm_config = {
        "config_list": autogen.config_list_from_json(
            str(config_path),
            filter_dict={"model": [_AI_model]},
        ),
        "timeout": 120,
        "temperature": 0,
        "max_tokens": 1024,  # 控制生成长度
    }

    # From `finrobot.agents.workflow` we import the `SingleAssistantRAG`, which takes a `retrieve_config` as input.
    # For `docs_path`, we first put our generated pdf report from [this notebook](./agent_annual_report.ipynb).
    #
    # For more configuration, refer to [autogen's documentation](https://microsoft.github.io/autogen/docs/reference/agentchat/contrib/retrieve_user_proxy_agent)
    #
    # Then, lets do a simple Q&A.

    assitant = SingleAssistantRAG(
        "Data_Analyst",
        llm_config,
        human_input_mode="NEVER",
        retrieve_config={
            "task": "qa",
            "vector_db": None,  # Autogen has bug for this version
            "docs_path": [
                str(report_path1),
            ],
            "chunk_token_size": 1000,
            "get_or_create": True,
            "collection_name": "msft_analysis",
            "must_break_at_empty_line": False,
        },
    )

    prompt = f"""{question1}
        {lang_snippet}""".strip()

    up = assitant.user_proxy
    aa = assitant.assistant

    if hasattr(up, "reset"):
        up.reset()
    if hasattr(aa, "reset"):
        aa.reset()

    if hasattr(up, "max_consecutive_auto_reply"):
        up.max_consecutive_auto_reply = 6

    up.initiate_chat(aa, message=prompt)

    messages1 = extract_all(up)

    # Here we come up with a more complex case, where we put the 10-k report of MSFT here.
    #
    # Let' see how the agent work this out.

    assitant = SingleAssistantRAG(
        "Data_Analyst",
        llm_config,
        human_input_mode="NEVER",
        retrieve_config={
            "task": "qa",
            "vector_db": None,  # Autogen has bug for this version
            "docs_path": [
                str(report_path2),
            ],
            "chunk_token_size": 2000,
            "collection_name": "msft_10k",
            "get_or_create": True,
            "must_break_at_empty_line": False,
        },
        rag_description="Retrieve content from MSFT's 2023 10-K report for detailed question answering.",
    )

    prompt = f"""{question2}
        {lang_snippet}""".strip()

    up = assitant.user_proxy
    aa = assitant.assistant

    if hasattr(up, "reset"):
        up.reset()
    if hasattr(aa, "reset"):
        aa.reset()

    if hasattr(up, "max_consecutive_auto_reply"):
        up.max_consecutive_auto_reply = 6

    up.initiate_chat(aa, message=prompt)

    messages2 = extract_all(up)
    return {"result": messages1 + messages2}
