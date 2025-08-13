from __future__ import annotations

import os
from pathlib import Path
from textwrap import dedent

import autogen
import matplotlib
from autogen.cache import Cache

# project utilities
from common.utils import (
    build_lang_directive,
    collect_generated_files,
    create_llm_config,
    create_output_directory,
    extract_all,
    get_script_result,
)
from finrobot.data_source import FMPUtils
from finrobot.functional import (
    IPythonUtils,
    ReportAnalysisUtils,
    ReportChartUtils,
    ReportLabUtils,
    TextUtils,
)
from finrobot.toolkits import register_toolkits
from finrobot.utils import register_keys_from_json


def run(params: dict, lang: str) -> dict:
    # 强制使用非 GUI 的 Matplotlib 后端，避免在后台线程中启动 GUI 导致中断
    matplotlib.use("Agg")

    os.environ.setdefault("FMP_API_DELAY", "1")  # API 调用间隔1秒

    company = params.get("company", "NextEra")
    competitors = params.get("competitors", ["DUK", "CEG", "AEP"])
    fyear = params.get("fyear", "2024")
    _AI_model = params.get("_AI_model", "gemini-2.5-flash")
    lang_snippet = build_lang_directive(lang)

    current_dir = Path(__file__).resolve().parent
    config_path = current_dir.parent.parent / "OAI_CONFIG_LIST"
    config_api_keys_path = current_dir.parent.parent / "config_api_keys"

    # 使用共通方法创建 LLM 配置，自动适配不同模型类型
    llm_config = create_llm_config(
        config_path=str(config_path), model_name=_AI_model, temperature=0.5, timeout=120
    )
    register_keys_from_json(str(config_api_keys_path))

    # Intermediate results will be saved in this directory (project utility)
    result_path = create_output_directory()
    work_dir = str(result_path)
    os.makedirs(work_dir, exist_ok=True)

    # For this task, we need:
    # - A user proxy to execute python functions and control the conversations.
    # - An expert agent who is proficient in financial analytical writing.
    # - A shadow/inner-assistant to handle isolated long-context Q&As.

    system_message = dedent(
        f"""
        Role: Expert Investor
        Department: Finance
        Primary Responsibility: Generation of Customized Financial Analysis Reports

        Role Description:
        As an Expert Investor within the finance domain, your expertise is harnessed to develop bespoke Financial Analysis Reports that cater to specific client requirements. This role demands a deep dive into financial statements and market data to unearth insights regarding a company's financial performance and stability. Engaging directly with clients to gather essential information and continuously refining the report with their feedback ensures the final product precisely meets their needs and expectations.

        Key Objectives:

        Analytical Precision: Employ meticulous analytical prowess to interpret financial data, identifying underlying trends and anomalies.
        Effective Communication: Simplify and effectively convey complex financial narratives, making them accessible and actionable to non-specialist audiences.
        Client Focus: Dynamically tailor reports in response to client feedback, ensuring the final analysis aligns with their strategic objectives.
        Adherence to Excellence: Maintain the highest standards of quality and integrity in report generation, following established benchmarks for analytical rigor.
        Performance Indicators:
        The efficacy of the Financial Analysis Report is measured by its utility in providing clear, actionable insights. This encompasses aiding corporate decision-making, pinpointing areas for operational enhancement, and offering a lucid evaluation of the company's financial health. Success is ultimately reflected in the report's contribution to informed investment decisions and strategic planning.

        Reply TERMINATE when everything is settled.
        """
    )

    expert = autogen.AssistantAgent(
        name="Expert_Investor",
        system_message=system_message,
        llm_config=llm_config,
        is_termination_msg=lambda x: x.get("content", "")
        and x.get("content", "").endswith("TERMINATE"),
    )
    expert_shadow = autogen.AssistantAgent(
        name="Expert_Investor_Shadow",
        system_message=system_message,
        llm_config=llm_config,
    )
    user_proxy = autogen.UserProxyAgent(
        name="User_Proxy",
        is_termination_msg=lambda x: x.get("content", "")
        and x.get("content", "").endswith("TERMINATE"),
        human_input_mode="NEVER",
        code_execution_config={
            "last_n_messages": 1,
            "work_dir": work_dir,
            "use_docker": False,
        },
    )

    register_toolkits(
        [
            FMPUtils.get_sec_report,  # Retrieve SEC report url and filing date
            IPythonUtils.display_image,  # Display image in IPython
            TextUtils.check_text_length,  # Check text length
            ReportLabUtils.build_annual_report,  # Build annual report in designed pdf format
            ReportAnalysisUtils,  # Expert Knowledge for Report Analysis
            ReportChartUtils,  # Expert Knowledge for Report Chart Plotting
        ],
        expert,
        user_proxy,
    )

    def order_trigger(sender):
        # Check if the last message contains the path to the instruction text file
        return "instruction & resources saved to" in sender.last_message()["content"]

    def order_message(recipient, messages, sender, config):
        # Extract the path to the instruction text file from the last message
        full_order = recipient.chat_messages_for_summary(sender)[-1]["content"]
        txt_path = full_order.replace("instruction & resources saved to ", "").strip()

        # 处理文件名过长或路径错误的情况
        try:
            # 检查路径是否合理（不包含换行符等异常字符）
            if "\n" in txt_path or len(txt_path) > 255:
                # 如果路径异常，尝试从工作目录中找到指令文件
                import glob

                instruction_files = glob.glob(f"{work_dir}/*instruction*.txt")
                if instruction_files:
                    txt_path = instruction_files[0]
                else:
                    return "Error: Could not find instruction file. Please try again."

            with open(txt_path, "r") as f:
                instruction = (
                    f.read() + "\n\nReply TERMINATE at the end of your response."
                )
            return instruction
        except (OSError, FileNotFoundError) as e:
            return f"Error reading instruction file: {str(e)}. Please try again."

    expert.register_nested_chats(
        [
            {
                "sender": expert,
                "recipient": expert_shadow,
                "message": order_message,
                "summary_method": "last_msg",
                "max_turns": 2,
                "silent": True,  # mute the chat summary
            }
        ],
        trigger=order_trigger,
    )

    # Resources list (kept as comments for reference)
    # 1. income statement: https://online.hbs.edu/blog/post/income-statement-analysis
    # 2. balance sheet: https://online.hbs.edu/blog/post/how-to-read-a-balance-sheet
    # 3. cash flow statement: https://online.hbs.edu/blog/post/how-to-read-a-cash-flow-statement
    # 4. Annual report: https://online.hbs.edu/blog/post/how-to-read-an-annual-report

    task = dedent(
        f"""
        With the tools you've been provided, write an annual report based on {company}'s and{competitors}'s{fyear} 10-k report, format it into a pdf.
        Pay attention to the followings:
        - Explicitly explain your working plan before you kick off.
        - Use tools one by one for clarity, especially when asking for instructions.
        - All your file operations should be done in "{work_dir}".
        - Display any image in the chat once generated.
        - For competitors analysis, strictly follow my prompt and use data only from the financial metics table, do not use similar sentences in other sections, delete similar setence, classify it into either of the two. The last sentence always talks about the Discuss how {company}’s performance over these years and across these metrics might justify or contradict its current market valuation (as reflected in the EV/EBITDA ratio).
        - Each paragraph in the first page(business overview, market position and operating results) should be between 150 and 160 words, each paragraph in the second page(risk assessment and competitors analysis) should be between 500 and 600 words, don't generate the pdf until this is explicitly fulfilled.
        {lang_snippet}
        """
    )

    with Cache.disk():
        user_proxy.initiate_chat(
            recipient=expert, message=task, max_turns=50, summary_method="last_msg"
        )

    # collect messages if helper exists
    if extract_all is not None:
        try:
            messages = extract_all(user_proxy)
        except Exception:  # pragma: no cover
            messages = []
    else:
        messages = []

    # Collect generated files and prepare preview
    generated = collect_generated_files(result_path)

    return get_script_result(
        messages=messages,
        additional_data={
            "generated_files": generated,
        },
        prompt=task,
    )
