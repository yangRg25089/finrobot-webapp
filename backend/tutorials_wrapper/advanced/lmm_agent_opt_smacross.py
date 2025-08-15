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
from typing import Any, Dict, Tuple

import autogen
import matplotlib
from autogen.agentchat.contrib.multimodal_conversable_agent import (
    MultimodalConversableAgent,
)
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
    matplotlib.use("Agg")

    symbol: str = params.get("symbol", "AAPL")
    start_date: str = params.get("start_date", "2025-01-01")
    end_date: str = params.get("end_date", "2025-06-30")
    init_cash: float = float(params.get("init_cash", 100000.0))
    commission: float = float(params.get("commission", 0.001))
    slippage: float = float(params.get("slippage", 0.0))
    sma_fast_range: Tuple[int, int] = tuple(params.get("sma_fast_range", (5, 20)))
    sma_slow_range: Tuple[int, int] = tuple(params.get("sma_slow_range", (30, 120)))
    benchmark: str | None = params.get("benchmark", "SPY")

    _AI_model: str = params.get("_AI_model", "openai/gpt-oss-20b:free")

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

    Trade_Strategist = MultimodalConversableAgent(
        name="Trade_Strategist",
        llm_config=llm_config,
        human_input_mode="NEVER",
        system_message=dedent(
            f"""
            You are a trading strategist who inspects financial charts and optimizes trading strategies for {symbol}.
            Goal: develop and validate an SMA Crossover strategy.

            Collaboration protocol:
            - Ask Backtesting_Analyst to PLOT candlestick chart(s) using ONLY the registered tool
              `MplFinanceUtils.plot_stock_price_chart`.
            - Inspect the chart(s), decide SMA fast/slow ranges, then ask Backtesting_Analyst
              to BACKTEST using ONLY `BackTraderUtils.back_test` with the designated parameters and dates.
            - Iterate until performance is satisfactory, then reply EXACTLY `TERMINATE`.

            Hard constraints (anti-hallucination):
            - DO NOT import or call any unregistered modules or APIs (e.g. `finrobot_api_client`, `default_api`).
            - Use only these registered tool functions: BackTraderUtils.back_test,
              MplFinanceUtils.plot_stock_price_chart.
            - Save artifacts under the executor's working directory.
            """
        ),
    )

    # Trade_Strategist = autogen.AssistantAgent(
    #     name="Trade_Strategist",
    #     llm_config=llm_config,
    #     human_input_mode="NEVER",
    #     system_message=dedent(
    #         f"""
    #         You are a trading strategist who inspects financial charts and optimizes trading strategies for {symbol}.
    #         Goal: develop and validate an SMA Crossover strategy.

    #         Collaboration protocol (TOOLS-ONLY):
    #         - Ask Backtesting_Analyst to PLOT candlestick chart(s) using ONLY the registered tool
    #           `plot_stock_price_chart`.
    #         - Inspect the chart(s), then ask Backtesting_Analyst to BACKTEST using ONLY `back_test`.
    #         - Request a GRID SEARCH across fast/slow ranges: fast in {sma_fast_range}, slow in {sma_slow_range}, skipping fast >= slow.
    #           The analyst must call `back_test` multiple times (one pair per call) and track the best by final portfolio value,
    #           tie-break by Sharpe.
    #         - After best params are found, have the analyst DISPLAY the best plot and summarize results, then reply EXACTLY `TERMINATE`.

    #         Hard constraints (anti-hallucination):
    #         - DO NOT import/call unregistered modules/APIs (e.g., `finrobot_api_client`, `default_api`).
    #         - DO NOT write Python code blocks. Trigger ONLY the registered tools by their names: `plot_stock_price_chart`, `back_test`.
    #         - Save artifacts under the executor's working directory.
    #         """
    #     ),
    # )

    Backtesting_Analyst = autogen.AssistantAgent(
        name="Backtesting_Analyst",
        llm_config=llm_config,
        human_input_mode="NEVER",
        system_message=dedent(
            f"""
            You are a backtesting analyst with strong quant tooling.
            Choose exactly one action per request and use TOOLS ONLY (no Python code blocks):
            1) PLOT historical price with MA overlays using `plot_stock_price_chart`.
            2) BACKTEST SMA crossover using `back_test`.

            Grid-search protocol:
            - Use fast in {sma_fast_range} and slow in {sma_slow_range}, skip fast >= slow.
            - Call `back_test` once per (fast, slow) pair, track metrics (final value; tie-break by Sharpe).
            - When finished, summarize metrics and best params.

            Reply rules:
            - Do NOT include `TERMINATE` until ALL artifacts are done and best params are reported.
            - Final message should be EXACTLY `TERMINATE`.

            Hard constraints (anti-hallucination):
            - Do NOT import or reference `MplFinanceUtils`, `BackTraderUtils`, `IPythonUtils` directly in Python code.
              Always invoke tools by name: `plot_stock_price_chart`, `back_test`.
            - Do NOT invent modules like `finrobot_api_client` or objects like `default_api`.
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

    User_Proxy = autogen.UserProxyAgent(
        name="User_Proxy",
        is_termination_msg=lambda x: (x.get("content") or "").strip() == "TERMINATE",
        human_input_mode="NEVER",
        code_execution_config={
            "last_n_messages": 1,
            "work_dir": str(run_dir),
            "use_docker": False,
        },
        max_consecutive_auto_reply=10,
    )

    groupchat = autogen.GroupChat(
        agents=[
            User_Proxy,
            Trade_Strategist,
            Backtesting_Analyst,
            Backtesting_Analyst_Executor,
        ],
        messages=[],
        max_round=30,
    )
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Kickoff: explicitly enumerate the ONLY allowed tools to avoid hallucinated imports
    kickoff = dedent(
        f"""
        Trade_Strategist: Coordinate the team to optimize an SMA crossover strategy for {symbol}.
        Backtesting_Analyst: first PLOT with `MplFinanceUtils.plot_stock_price_chart`, then BACKTEST with
        `BackTraderUtils.back_test`. Do NOT use any
        other modules or APIs.
        Backtesting_Analyst_Executor: implement, run, and save artifacts under {run_dir.as_posix()}; reply only TERMINATE when done.
        Inputs: start={start_date}, end={end_date}, init_cash={init_cash}, commission={commission}, slippage={slippage},
        fast_range={sma_fast_range}, slow_range={sma_slow_range}, benchmark={benchmark}. {lang_snippet}
        """
    )
    User_Proxy.initiate_chat(manager, message=kickoff)

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
