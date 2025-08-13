from __future__ import annotations

"""
FinRobot WebApp — tutorials_wrapper/advanced/lmm_agent_opt_smacross.py
---------------------------------------------------------------------
Two cooperating agents based on the original notebook roles:
- Backtesting_Analyst: Plans the SMACROSS optimization task.
- Backtesting_Analyst_Executor: Writes & runs code, saves artifacts.
"""

import json
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
    create_output_directory,
    extract_all,
    get_script_result,
)
from finrobot.functional.charting import MplFinanceUtils
from finrobot.functional.coding import IPythonUtils
from finrobot.functional.quantitative import BackTraderUtils
from finrobot.toolkits import register_toolkits

try:
    from finrobot.functional.reportlab import ReportWriter  # noqa: F401
except Exception:
    ReportWriter = None  # type: ignore


def create_llm_config(
    config_path: str,
    model_name: str,
    temperature: float = 0.5,
    timeout: int = 120,
    max_tokens: int = None,
) -> dict:
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file, "r") as f:
        all_configs = json.load(f)

    model_config = None
    for config in all_configs:
        if config.get("model") == model_name:
            model_config = config.copy()
            break

    if not model_config:
        raise ValueError(f"Model '{model_name}' not found in config file")

    api_type = model_config.get("api_type", "openai")

    if api_type == "ollama":
        config_list = [
            {
                "model": model_config["model"],
                "base_url": model_config["base_url"],
                "api_key": model_config["api_key"],
            }
        ]
        llm_config = {"config_list": config_list, "temperature": temperature}
        if timeout and timeout != 120:
            llm_config["timeout"] = timeout
    else:
        config_list = autogen.config_list_from_json(
            config_path,
            filter_dict={"model": [model_name]},
        )
        if not config_list:
            raise ValueError(f"No valid config found for model '{model_name}'")
        llm_config = {
            "config_list": config_list,
            "temperature": temperature,
            "timeout": timeout,
        }
        if max_tokens:
            llm_config["max_tokens"] = max_tokens
    return llm_config


def run(params: Dict[str, Any], lang: str) -> Dict[str, Any]:
    matplotlib.use("Agg")

    symbol: str = params.get("symbol", "AAPL")
    start_date: str = params.get("start_date", "2023-01-01")
    end_date: str = params.get("end_date", "2024-12-31")
    init_cash: float = float(params.get("init_cash", 100000.0))
    commission: float = float(params.get("commission", 0.001))
    slippage: float = float(params.get("slippage", 0.0))
    sma_fast_range: Tuple[int, int] = tuple(params.get("sma_fast_range", (5, 20)))
    sma_slow_range: Tuple[int, int] = tuple(params.get("sma_slow_range", (30, 120)))
    benchmark: str | None = params.get("benchmark", "SPY")

    _AI_model: str = params.get("_AI_model", "gemini-2.5-flash-lite")
    lang_snippet: str = build_lang_directive(lang)

    repo_root = Path(__file__).resolve().parent.parent.parent
    config_list_path = repo_root / "OAI_CONFIG_LIST"

    run_dir = create_output_directory()

    llm_config = create_llm_config(
        config_path=str(config_list_path),
        model_name=_AI_model,
        temperature=0,
        timeout=150,
    )

    Trade_Strategist = MultimodalConversableAgent(
        name="Trade_Strategist",
        llm_config=llm_config,
        human_input_mode="NEVER",
        system_message=dedent(
            """
            You are a trading strategist who inspect financial charts and optimize trading strategies.
            You have been tasked with developing a Simple Moving Average (SMA) Crossover strategy.
            You have the following main actions to take:
            1. Ask the backtesting analyst to plot historical stock price data with designated ma parameters.
            2. Inspect the stock price chart and determine fast/slow parameters.
            3. Ask the backtesting analyst to backtest the SMACrossover trading strategy with designated parameters to evaluate its performance. 
            4. Inspect the backtest result and optimize the fast/slow parameters based on the returned results.
            Reply TERMINATE when you think the strategy is good enough.
            """
        ),
    )

    Backtesting_Analyst = autogen.AssistantAgent(
        name="Backtesting_Analyst",
        llm_config=llm_config,
        human_input_mode="NEVER",
        system_message=dedent(
            """
            You are a backtesting analyst with a strong command of quantitative analysis tools. 
            You have two main tasks to perform, choose one each time you are asked by the trading strategist:
            1. Plot historical stock price data with designated ma parameters according to the trading strategist's need.
            2. Backtest the SMACross trading strategy with designated parameters and save the results as image file.
            For both tasks, after the tool calling, you should do as follows:
                1. display the created & saved image file using the `display_image` tool;
                2. Assume the saved image file is "test.png", reply as follows: "Optimize the fast/slow parameters based on this image <img test.png>. TERMINATE".
            """
        ),
    )

    Backtesting_Analyst_Executor = autogen.AssistantAgent(
        name="Backtesting_Analyst_Executor",
        llm_config=llm_config,
        human_input_mode="NEVER",
        is_termination_msg=lambda x: x.get("content", "")
        and x.get("content", "").find("TERMINATE") >= 0,
        code_execution_config={
            "last_n_messages": 1,
            "work_dir": str(run_dir),
            "use_docker": False,
        },
    )

    register_toolkits(
        [
            BackTraderUtils.back_test,
            MplFinanceUtils.plot_stock_price_chart,
            IPythonUtils.display_image,
        ],
        Backtesting_Analyst,
        Backtesting_Analyst_Executor,
    )

    User_Proxy = autogen.UserProxyAgent(
        name="User_Proxy",
        is_termination_msg=lambda x: x.get("content", "")
        and x.get("content", "").endswith("TERMINATE"),
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
        max_round=10,
    )
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    kickoff = (
        f"Trade_Strategist: Coordinate the following team to optimize an SMA crossover strategy for {symbol}.\n"
        f"Backtesting_Analyst: define search ranges, metrics, and report outline.\n"
        f"Backtesting_Analyst_Executor: implement, run, and save artifacts under {run_dir.as_posix()}; reply only TERMINATE when done.\n"
        f"Inputs: start={start_date}, end={end_date}, init_cash={init_cash}, commission={commission}, slippage={slippage}, \n"
        f"fast_range={sma_fast_range}, slow_range={sma_slow_range}, benchmark={benchmark}. {lang_snippet}"
    )
    User_Proxy.initiate_chat(manager, message=kickoff)

    messages = extract_all(User_Proxy)

    generated = collect_generated_files(run_dir)

    return get_script_result(
        messages=messages,
        additional_data={
            "generated_files": generated,
        },
        prompt=kickoff,
    )
