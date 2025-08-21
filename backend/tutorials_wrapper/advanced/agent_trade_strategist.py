from __future__ import annotations

import os
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict

import autogen
import matplotlib
from autogen.cache import Cache

matplotlib.use("Agg")

# project utilities
from common.utils import (
    build_lang_directive,
    collect_generated_files,
    create_llm_config,
    create_output_directory,
    extract_all,
    get_script_result,
)
from finrobot.functional.coding import IPythonUtils
from finrobot.functional.quantitative import BackTraderUtils
from finrobot.toolkits import register_code_writing, register_toolkits


# ------------------------------
# 终止条件 & 基础设施
# ------------------------------
def _has_image(work_dir: Path) -> bool:
    exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
    try:
        for name in os.listdir(work_dir):
            if (work_dir / name).is_file() and Path(name).suffix.lower() in exts:
                return True
    except Exception:
        pass
    return False


def is_term_msg_factory(work_dir: Path):
    """只有在消息包含 TERMINATE 且 work_dir 已产出图片文件时才允许结束。"""

    def _term(msg: Dict[str, Any]) -> bool:
        content = (msg.get("content") or "").strip()
        if not isinstance(content, str):
            return False
        if "TERMINATE" not in content:
            return False
        return _has_image(work_dir)

    return _term


def _seed_strategy_if_absent(work_dir: Path):
    """写入最小可运行策略 + CustomSizer 作为兜底。"""
    seed_path = work_dir / "my_strategy.py"
    if seed_path.exists():
        return
    seed_code = dedent(
        """
        import backtrader as bt

        class MyStrategy(bt.Strategy):
            params = (('fast_length', 10), ('slow_length', 30), )

            def __init__(self):
                self.fast = bt.indicators.SMA(self.data.close, period=self.p.fast_length)
                self.slow = bt.indicators.SMA(self.data.close, period=self.p.slow_length)
                self.crossover = bt.indicators.CrossOver(self.fast, self.slow)
                self.order = None

            def next(self):
                if self.order:
                    return
                if not self.position:
                    if self.crossover > 0:
                        self.order = self.buy()
                else:
                    if self.crossover < 0:
                        self.order = self.close()

            def log(self, txt, dt=None):
                dt = dt or self.datas[0].datetime.date(0)
                print(f'{dt.isoformat()}, {txt}')

        class CustomSizer(bt.Sizer):
            params = (('shares', 100),)

            def _getsizing(self, comminfo, cash, data, isbuy):
                if isbuy:
                    return self.p.shares
                else:
                    return self.broker.getposition(data).size
        """
    ).strip()
    seed_path.write_text(seed_code, encoding="utf-8")


def _is_transient_or_gemini_error(exc: Exception) -> bool:
    msg = str(exc)
    return (
        "Error code: 500" in msg
        or "INTERNAL" in msg
        or "generativeai.google" in msg
        or "Please retry" in msg
        or "try again" in msg.lower()
    )


def _initiate_with_fallback(user_proxy, strategist, task: str, max_turns: int = 10):
    """优先当前 llm_config；若遇 Gemini/5xx，自动降级到确定支持 function-calling 的模型。"""
    last_err = None
    try:
        with Cache.disk():
            user_proxy.initiate_chat(
                recipient=strategist,
                message=task,
                max_turns=max_turns,
                summary_method="last_msg",
            )
        return
    except Exception as e:
        last_err = e
        if not _is_transient_or_gemini_error(e):
            raise

    # 降级候选：按需调整顺序，确保 OAI_CONFIG_LIST 里有配置
    fallbacks = [
        {"model": "openai/gpt-4o-mini", "api_type": "openai"},
        {
            "model": "openai/gpt-4o-mini",
            "base_url": "https://openrouter.ai/api/v1",
            "api_type": "openai",
        },
    ]
    base_cfg = strategist.llm_config.copy()
    exist_list = list(base_cfg.get("config_list") or [])
    for fb in fallbacks:
        if any(d.get("model") == fb["model"] for d in exist_list):
            continue
        exist_list.insert(0, fb)
    strategist.llm_config["config_list"] = exist_list

    with Cache.disk():
        user_proxy.initiate_chat(
            recipient=strategist,
            message=task,
            max_turns=max_turns,
            summary_method="last_msg",
        )


# ------------------------------
# 关键新增：对写文件类工具做“文件名去路径”护栏
# ------------------------------
def _patch_code_tools():
    """
    强制让 create/append/see 只接受“纯文件名”（basename）。
    Agent 如果塞绝对路径或带目录，我们会自动取 basename 写到 work_dir 根目录。
    """
    import finrobot.functional.coding as coding_mod

    # 缓存原始函数
    orig_create = getattr(coding_mod, "create_file_with_code", None)
    orig_append = getattr(coding_mod, "append_file_with_code", None)
    orig_see = getattr(coding_mod, "see_file", None)

    def _bn(name: str) -> str:
        # 只保留文件名部分，去掉任何路径/盘符
        return Path(name).name

    if orig_create:

        def wrapped_create_file_with_code(*, code: str, filename: str):
            return orig_create(code=code, filename=_bn(filename))

        coding_mod.create_file_with_code = wrapped_create_file_with_code  # type: ignore

    if orig_append:

        def wrapped_append_file_with_code(*, code: str, filename: str):
            return orig_append(code=code, filename=_bn(filename))

        coding_mod.append_file_with_code = wrapped_append_file_with_code  # type: ignore

    if orig_see:

        def wrapped_see_file(*, filename: str):
            return orig_see(filename=_bn(filename))

        coding_mod.see_file = wrapped_see_file  # type: ignore


# ------------------------------
# 主入口
# ------------------------------
def run(params: dict, lang: str) -> dict:
    # 基本参数
    company = params.get("company", "MSFT")
    start_date = params.get("start_date", "2024-06-01")
    end_date = params.get("end_date", "2025-01-01")
    _AI_model = params.get(
        "_AI_model", "openai/gpt-4o-mini"
    )  # 可改为 "gemini-2.5-flash-lite"
    lang_snippet = build_lang_directive(lang)

    # 配置模型
    current_dir = Path(__file__).resolve().parent
    config_path = current_dir.parent.parent / "OAI_CONFIG_LIST"
    llm_config = create_llm_config(
        config_path=str(config_path),
        model_name=_AI_model,
        temperature=0,  # 降低自由发挥
        timeout=120,
    )

    # 工作目录
    result_path = create_output_directory()
    work_dir = Path(result_path)
    os.makedirs(work_dir, exist_ok=True)

    # ✅ 强制 code-writing 工具把文件写进本轮 work_dir
    import finrobot.functional.coding as coding_mod

    coding_mod.default_path = str(work_dir) + os.sep
    os.makedirs(coding_mod.default_path, exist_ok=True)

    # 关键：先打补丁再注册“写文件”工具
    _patch_code_tools()

    # 让 {work_dir.strip('/')}.<module> 可被 import：
    # 1) 把工作目录加入 sys.path
    if str(work_dir) not in sys.path:
        sys.path.insert(0, str(work_dir))
    # 2) 把根目录加入 sys.path（借助 PEP 420 namespace package）
    root_dir = Path("/").resolve()
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))
    # 3) 计算模块路径前缀
    module_prefix = work_dir.as_posix().lstrip("/").replace("/", ".")

    # 兜底策略：先写一个最小可运行策略（含 CustomSizer）
    _seed_strategy_if_absent(work_dir)

    # Agent 定义
    strategist = autogen.AssistantAgent(
        name="Trade_Strategist",
        system_message=dedent(
            f"""
            You are a trading strategist known for your expertise in developing sophisticated trading algorithms. 
            Your task is to leverage your coding skills to create a customized trading strategy using the BackTrader Python library, and save it as a Python module. 
            Remember to log necessary information in the strategy so that further analysis could be done.
            You can also write custom sizer / indicator and save them as modules, which would allow you to generate more sophisticated strategies.
            After creating the strategy, you may backtest it with the tool you're provided to evaluate its performance and make any necessary adjustments.

            File & Path rules (NO EXCEPTIONS):
            - All files you create will automatically be saved under: "{str(work_dir)}".
            - When creating files with the coding tools, the filename MUST be a bare filename like "my_strategy.py".
              DO NOT include any path separators. Any path you provide will be stripped to basename.
            - When calling the backtest function, the module path MUST be "{module_prefix}.<module_name_without_py>".
              Example: strategy MUST be "{module_prefix}.my_strategy:MyStrategy".
            - For save_fig, pass an absolute path under work_dir, e.g. "{str(work_dir)}/{company.lower()}_backtest.png".
              After backtest, call the display-image tool with the SAME absolute path.

            Tool policy:
            - You may use exactly two tools:
              1) BackTraderUtils.back_test
            - Allowed parameters for back_test: ticker_symbol, start_date, end_date, strategy, save_fig,
              strategy_params (JSON or k=v), sizer (optional), sizer_params (JSON or k=v), cash (optional).
            - DO NOT pass any other parameters (e.g., commission, slippage, etc.).

            Reply TERMINATE when the strategy is ready to be tested or when you have successfully run back_test, displayed the chart, and reported your findings.
            """
        ),
        llm_config=llm_config,
    )

    user_proxy = autogen.UserProxyAgent(
        name="User_Proxy",
        is_termination_msg=is_term_msg_factory(work_dir),
        human_input_mode="NEVER",
        code_execution_config={
            "last_n_messages": 1,
            "work_dir": str(work_dir),
            "use_docker": False,
        },
    )

    # 注册“写文件”工具（现在已被我们打过“只保留 basename”的补丁）
    register_code_writing(strategist, user_proxy)

    register_toolkits(
        [
            BackTraderUtils.back_test,
        ],
        strategist,
        user_proxy,
    )

    # ---------- 阶段 1：写/改策略 ----------
    coding_task = dedent(
        f"""
        Implement or refine your trading strategy module as needed under "{str(work_dir)}".
        Use a filename like "my_strategy.py" and define class "MyStrategy" (and optional "CustomSizer").
        When the module is ready to be tested, reply only: TERMINATE
        {lang_snippet}
        """
    )
    _initiate_with_fallback(user_proxy, strategist, coding_task, max_turns=6)

    # ---------- 阶段 2：回测 + 展示图 + 报告 ----------
    backtest_task = dedent(
        f"""
        Based on {company}'s stock data from {start_date} to {end_date}, develop a trading strategy that would performs well on this stock.
        Write your own custom indicator/sizer if needed. Other backtest settings like initial cash are all up to you to decide.
        After each backtest, display the saved backtest result chart, then report the current situation and your thoughts towards optimization.
        Modify the code to optimize your strategy or try more different indicators / sizers into account for better performance.
        Your strategy should at least outperform the benchmark strategy of buying and holding the stock.

        STRICT reminders:
        - strategy MUST be "{module_prefix}.my_strategy:MyStrategy" (no folder prefix beyond this)
        - sizer (optional) MUST be "{module_prefix}.my_strategy:CustomSizer"
        - save_fig MUST be an absolute path under work_dir, e.g., "{str(work_dir)}/{company.lower()}_backtest.png"
        - Allowed back_test params ONLY: ticker_symbol, start_date, end_date, strategy, save_fig, strategy_params, sizer, sizer_params, cash
        - strategy_params / sizer_params MUST be JSON like {{"fast_length":10,"slow_length":30}} or key-value string like fast_length=10,slow_length=30
        - After you have successfully run back_test and displayed the chart, reply only: TERMINATE
        {lang_snippet}
        """
    )
    _initiate_with_fallback(user_proxy, strategist, backtest_task, max_turns=10)

    # 收集结果
    messages = extract_all(user_proxy)
    generated = collect_generated_files(result_path)
    return get_script_result(
        messages=messages,
        additional_data={"generated_files": generated},
        prompt=backtest_task,
    )
