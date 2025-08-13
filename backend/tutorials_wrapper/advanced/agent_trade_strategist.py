from __future__ import annotations

import os
from pathlib import Path
from textwrap import dedent

import autogen
import matplotlib
from autogen.cache import Cache

# project utilities
from common.utils import create_llm_config  # 新增：与参考脚本保持一致
from common.utils import (
    build_lang_directive,
    collect_generated_files,
    create_output_directory,
    extract_all,
    get_script_result,
)
from finrobot.functional.coding import IPythonUtils
from finrobot.functional.quantitative import BackTraderUtils
from finrobot.toolkits import register_code_writing, register_toolkits


def run(params: dict, lang: str) -> dict:
    # 强制使用非 GUI 的 Matplotlib 后端，避免在后台线程中启动 GUI 导致中断
    matplotlib.use("Agg")

    company = params.get("company", "Microsoft")
    start_date = params.get("start_date", "2024-01-01")
    end_date = params.get("end_date", "2025-01-01")
    _AI_model = params.get("_AI_model", "gemini-2.5-flash")
    lang_snippet = build_lang_directive(lang)

    current_dir = Path(__file__).resolve().parent
    config_path = current_dir.parent.parent / "OAI_CONFIG_LIST"

    llm_config = create_llm_config(
        config_path=str(config_path),
        model_name=_AI_model,
        temperature=0.5,
        timeout=120,
    )

    # Intermediate strategy modules will be saved in this directory (use common project helper)
    result_path = create_output_directory()
    work_dir = str(result_path)
    os.makedirs(work_dir, exist_ok=True)

    # For this task, we need:
    # - A user proxy to execute python functions and control the conversations.
    # - A trade strategist who writes **BackTrader** style trade strategy and can optimize them through backtesting.

    strategist = autogen.AssistantAgent(
        name="Trade_Strategist",
        system_message=dedent(
            f"""
            You are a trading strategist known for your expertise in developing sophisticated trading algorithms. 
            Your task is to leverage your coding skills to create a customized trading strategy using the BackTrader Python library, and save it as a Python module. 
            Remember to log necessary information in the strategy so that further analysis could be done.
            You can also write custom sizer / indicator and save them as modules, which would allow you to generate more sophisticated strategies.
            After creating the strategy, you may backtest it with the tool you're provided to evaluate its performance and make any necessary adjustments.
            All files you created during coding will automatically be in `{work_dir}`, no need to specify the prefix. 
            But when calling the backtest function, module path should be like `{Path(work_dir).name}.<module_path>` and savefig path should consider `{work_dir}` as well.
            Reply TERMINATE to executer when the strategy is ready to be tested.
            """
        ),
        llm_config=llm_config,
    )

    user_proxy = autogen.UserProxyAgent(
        name="User_Proxy",
        is_termination_msg=lambda x: x.get("content", "")
        and x.get("content", "").endswith("TERMINATE"),
        human_input_mode="NEVER",  # change to "ALWAYS" if manual interaction is needed
        code_execution_config={
            "last_n_messages": 1,
            "work_dir": work_dir,
            "use_docker": False,
        },
    )

    register_code_writing(strategist, user_proxy)
    register_toolkits(
        [BackTraderUtils.back_test, IPythonUtils.display_image], strategist, user_proxy
    )

    # Now it's time to see what strategy can the agent provide.
    # Don't expect too high as indicators are limited and the agent sees limited analysis.

    task = dedent(
        f"""
        Based on {company}'s stock data from {start_date} to {end_date}, develop a trading strategy that would performs well on this stock.
        Write your own custom indicator/sizer if needed. Other backtest settings like initial cash are all up to you to decide.
        After each backtest, display the saved backtest result chart, then report the current situation and your thoughts towards optimization.
        Modify the code to optimize your strategy or try more different indicators / sizers into account for better performance.
        Your strategy should at least outperform the benchmark strategy of buying and holding the stock.
        """
    )

    with Cache.disk():
        user_proxy.initiate_chat(
            recipient=strategist,
            message=task,
            max_turns=30,
            summary_method="last_msg",
        )

    # Collect messages if helper exists
    if extract_all is not None:
        try:
            messages = extract_all(user_proxy)
        except Exception:  # pragma: no cover
            messages = []
    else:
        messages = []

    # Collect generated files (images, modules, etc.)
    generated = collect_generated_files(result_path)

    return get_script_result(
        messages=messages,
        additional_data={
            "generated_files": generated,
        },
        prompt=task,
    )
