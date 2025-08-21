from __future__ import annotations

"""
FinRobot WebApp — tutorials_wrapper/advanced/lmm_agent_opt_smacross.py
---------------------------------------------------------------------
Two cooperating agents based on the original notebook roles:
- Backtesting_Analyst: Plans the SMACROSS optimization task.
- Backtesting_Analyst_Executor: Writes & runs code, saves artifacts.
"""

from pathlib import Path
from textwrap import dedent
from typing import Any, Dict

import autogen
import matplotlib
from autogen.cache import Cache

matplotlib.use("Agg")

from common.utils import (
    build_lang_directive,
    collect_generated_files,
    create_llm_config,
    create_output_directory,
    extract_all,
    get_script_result,
)
from finrobot.functional.charting import MplFinanceUtils
from finrobot.functional.quantitative import BackTraderUtils
from finrobot.toolkits import register_toolkits

try:
    from finrobot.functional.reportlab import ReportWriter  # noqa: F401
except Exception:
    ReportWriter = None  # type: ignore


def run(params: Dict[str, Any], lang: str) -> Dict[str, Any]:

    company: str = params.get("company", "Microsoft")
    start_date: str = params.get("start_date", "2024-06-01")
    end_date: str = params.get("end_date", "2025-01-01")
    _AI_model: str = params.get("_AI_model", "gemini-2.5-flash")

    lang_snippet: str = build_lang_directive(lang)

    repo_root = Path(__file__).resolve().parent.parent.parent
    config_list_path = repo_root / "OAI_CONFIG_LIST"

    # NOTE: per your request, keep the default create_output_directory() usage.
    run_dir = create_output_directory()

    llm_config = create_llm_config(
        config_path=str(config_list_path),
        model_name=_AI_model,
        temperature=0,
    )

    llm_config_v4 = create_llm_config(
        config_path=str(config_list_path),
        model_name="meta/llama-3.1-70b-instruct",
        temperature=0,
    )

    Trade_Strategist = autogen.AssistantAgent(
        name="Trade_Strategist",
        llm_config=llm_config,  # 不用 gemini
        human_input_mode="NEVER",
        system_message=dedent(
            """
      You are a trading strategist for an SMA Crossover strategy.

      Protocol:
      1) Ask the analyst to PLOT first (mav [20, 50]).
      2) Then IMMEDIATELY request a BACKTEST with default SMA lengths fast=20, slow=50 for the first run.
         Do NOT wait for user-provided numbers.
      3) Optionally iterate once more to improve.
      4) Reply exactly: TERMINATE when done.

      Tool-call rules:
      - Tools ONLY. Do NOT write Python code blocks. Do NOT use <execute_ipython>.
      - Never pass null/None. Use "" for optional string fields.
      - Keys must match the schema exactly.

      plot_stock_price_chart schema:
      { "ticker_symbol": str, "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD",
        "mav": [int, ...], "save_path": str }

      back_test schema:
      { "ticker_symbol": str, "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD",
        "cash": int, "strategy": "SMA_Crossover",
        "strategy_params": "{\"fast\":<int>,\"slow\":<int>}",
        "indicator": "", "indicator_params": "",
        "sizer": "", "sizer_params": "",
        "save_fig": str }

      Example back_test call (first run, default):
      back_test({
        "ticker_symbol": "MSFT",
        "start_date": "2024-06-01",
        "end_date":   "2025-01-01",
        "cash": 10000,
        "strategy": "SMA_Crossover",
        "strategy_params": "{\"fast\":20,\"slow\":50}",
        "indicator": "",
        "indicator_params": "",
        "sizer": "",
        "sizer_params": "",
        "save_fig": "MSFT_SMACrossover_20_50_backtest.png"
      })
    """
        ),
    )

    Backtesting_Analyst = autogen.AssistantAgent(
        name="Backtesting_Analyst",
        llm_config=llm_config,
        human_input_mode="NEVER",
        system_message=dedent(
            """
        You are a backtesting analyst. On each request, choose EXACTLY ONE action and call the corresponding tool:
        - PLOT: use plot_stock_price_chart with the required schema.
        - BACKTEST: use back_test with the required schema.

        Hard constraints:
        - Tools ONLY. Do NOT write Python code blocks; do NOT use <execute_ipython>.
        - Never pass null/None. Use empty string "" for optional string fields.
        - Keep keys EXACT as specified below.

        plot_stock_price_chart schema:
        { "ticker_symbol": str, "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD",
          "mav": [int, ...], "save_path": str }

        back_test schema:
        { "ticker_symbol": str, "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD",
          "cash": int, "strategy": "SMA_Crossover",
          "strategy_params": "{\"fast\":<int>,\"slow\":<int>}",
          "indicator": "", "indicator_params": "",
          "sizer": "", "sizer_params": "", "save_fig": str }

        Termination:
        - If a tool response contains "Error:", stop further attempts and reply TERMINATE.
        - Otherwise, summarize in one sentence and proceed to the next step as requested.

        You have two actions ONLY: PLOT or BACKTEST (tools only).
        If the strategist message does not explicitly contain SMA lengths,
        you MUST use the default fast=20, slow=50 for the first backtest.
        (Schema and rules same as above; never pass null.)
        """
        ),
    )

    Backtesting_Analyst_Executor = autogen.AssistantAgent(
        name="Backtesting_Analyst_Executor",
        llm_config=llm_config,
        human_input_mode="NEVER",
        is_termination_msg=lambda x: (x.get("content") or "").strip() == "TERMINATE",
        system_message=dedent(
            """
            You are the execution agent. Do NOT write or run standalone Python scripts.
            Execute ONLY via tool calls using the registered function names: `plot_stock_price_chart`, `back_test`.
            When all artifacts are generated and best parameters summarized, reply exactly: TERMINATE
            """
        ),
        code_execution_config={
            "last_n_messages": 1,
            "work_dir": str(run_dir),
            "use_docker": False,
        },
    )

    # Register toolkits: allow ONLY these functions to be used programmatically
    register_toolkits(
        [
            BackTraderUtils.back_test,
            MplFinanceUtils.plot_stock_price_chart,
        ],
        Backtesting_Analyst,
        Backtesting_Analyst_Executor,
    )

    def reflection_message_analyst(recipient, messages, sender, config):
        print("Reflecting strategist's response ...")
        last_msg = recipient.chat_messages_for_summary(sender)[-1]["content"]
        return (
            "Message from Trade Strategist is as follows:"
            + last_msg
            + "\n\nBased on his information, conduct a backtest on the specified stock and strategy, and report your backtesting results back to the strategist."
        )

    User_Proxy = autogen.UserProxyAgent(
        name="User_Proxy",
        is_termination_msg=lambda x: (x.get("content") or "").strip() == "TERMINATE",
        human_input_mode="NEVER",
        code_execution_config={
            "last_n_messages": 1,
            "work_dir": str(run_dir),
            "use_docker": False,
        },
        max_consecutive_auto_reply=5,
    )

    User_Proxy.register_nested_chats(
        [
            {
                "sender": Backtesting_Analyst_Executor,
                "recipient": Backtesting_Analyst,
                "message": reflection_message_analyst,
                "max_turns": 5,
            }
        ],
        trigger=Trade_Strategist,
    )

    # Kickoff: explicitly enumerate the ONLY allowed tools to avoid hallucinated imports
    kickoff = dedent(
        f"""
        Based on {company}'s stock data from {start_date} to {end_date}, determine the possible optimal parameters for an SMACrossover Strategy over this period. 
        First, ask the analyst to plot a candlestick chart of the stock price data to visually inspect the price movements and make an initial assessment.
        Then, ask the analyst to backtest the strategy parameters using the backtesting tool, and report results back for further optimization.
        Backtesting_Analyst_Executor: implement, run, and save artifacts under {run_dir.as_posix()}; reply only TERMINATE when done.
        {lang_snippet}
        """
    )

    with Cache.disk() as cache:
        User_Proxy.initiate_chat(
            recipient=Trade_Strategist,
            message=kickoff,
            max_turns=5,
            summary_method="last_msg",
        )
    # User_Proxy.initiate_chat(
    #     recipient=Trade_Strategist,
    #     message=kickoff,
    #     max_turns=5,
    #     summary_method="last_msg",
    # )

    # NOTE: per your request, keep the original single-source extraction.
    messages = extract_all(User_Proxy)

    generated = collect_generated_files(run_dir)

    # NOTE: per your request, keep the original get_script_result signature.
    return get_script_result(
        messages=messages,
        additional_data={
            "generated_files": generated,
        },
        prompt=kickoff,
    )
