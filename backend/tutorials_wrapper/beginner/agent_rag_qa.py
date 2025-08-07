# # RetrieveChat based FinRobot-RAG

# In this demo, we showcase the RAG usecase of our finrobot, which inherits from autogen's RetrieveChat implementation.
#
#
# Instead of using `RetrieveUserProxyAgent` directly, we register the context retrieval as a function for our bots.
# For detailed implementation, refer to [rag function](../finrobot/functional/rag.py) and [rag workflow](../finrobot/agents/workflow.py) of `SingleAssistantRAG`

import autogen
from finrobot.agents.workflow import SingleAssistantRAG

# for openai configuration, rename OAI_CONFIG_LIST_sample to OAI_CONFIG_LIST and replace the api keys


def run(params: dict) -> dict:

    # Read OpenAI API keys from a JSON file
    llm_config = {
        "config_list": autogen.config_list_from_json(
            "../../OAI_CONFIG_LIST",
            filter_dict={"model": ["openai/gpt-4o-mini"]},
        ),
        "timeout": 120,
        "temperature": 0,
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
                "../report/Microsoft_Annual_Report_2023.pdf",
            ],
            "chunk_token_size": 1000,
            "get_or_create": True,
            "collection_name": "msft_analysis",
            "must_break_at_empty_line": False,
        },
    )
    assitant.chat("How's msft's 2023 income? Provide with some analysis.")

    final_reply1 = (
        assitant.user_proxy.last_message()["content"]
        if assitant.user_proxy.last_message()
        else "No response from the analyst."
    )

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
                "../report/2023-07-27_10-K_msft-20230630.htm.pdf",
            ],
            "chunk_token_size": 2000,
            "collection_name": "msft_10k",
            "get_or_create": True,
            "must_break_at_empty_line": False,
        },
        rag_description="Retrieve content from MSFT's 2023 10-K report for detailed question answering.",
    )
    assitant.chat("How's msft's 2023 income? Provide with some analysis.")

    final_reply2 = (
        assitant.user_proxy.last_message()["content"]
        if assitant.user_proxy.last_message()
        else "No response from the analyst."
    )

    return {
        "result": [
            {"summary": final_reply1},
            {"summary": final_reply2},
        ]
    }
