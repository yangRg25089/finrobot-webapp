"""
Financial-RAG demo  ·  Earnings calls + SEC filings
---------------------------------------------------
主要步骤
1. 读取 earnings call、SEC Filings（两种格式）
2. 构建三套向量库：earnings_call / sec_filings_text / sec_filings_markdown
3. 注册三类查询函数到 AutoGen Tool Proxy
4. 通过 Planner-Tool 两个代理实现智能检索
5. 返回完整对话历史，方便前端渲染
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import autogen
from autogen import ConversableAgent, register_function
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)

# ---------- 常量 ----------
PROJECT_ROOT = Path(__file__).resolve().parent  # 调整到你的根目录
DATA_REPO = PROJECT_ROOT / "finance_llm_data"  # ← 确保已 git clone
OUTPUT_DIR = DATA_REPO / "output"  # 生成的 pdf / md 会在这里

EMBED_FN = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
TXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1024, chunk_overlap=100, length_function=len
)


# ---------- 工具函数 ----------
def ensure_repo() -> None:
    if not DATA_REPO.exists():
        raise FileNotFoundError(
            f"{DATA_REPO} 不存在，请先 `git clone https://github.com/Athe-kunal/finance_llm_data.git`"
        )


def build_vector_db(docs, path: Path, name: str):
    """若已持久化，则直接加载；否则新建并保存"""
    if path.exists():
        return Chroma(
            persist_directory=str(path),
            embedding_function=EMBED_FN,
            collection_name=name,
        )
    return Chroma.from_documents(
        docs,
        EMBED_FN,
        persist_directory=str(path),
        collection_name=name,
    )


# ---------- 核心入口 ----------
def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    params:
      {
        "ticker": "GOOG",
        "year"  : "2023",
        "lang"  : "en" | "zh" | ...
      }
    """
    ensure_repo()

    # ------------------------------------------------------------
    # 1. 获取数据（调用 finance_llm_data.get_data）
    # ------------------------------------------------------------
    from finance_llm_data.finance_data import (
        get_data,
    )  # noqa: E402 (local import after env check)

    ticker = params.get("ticker", "GOOG")
    year = params.get("year", "2023")
    filing_types = ["10-K", "10-Q"]

    # Earnings call
    (
        earnings_docs,
        quarter_vals,
        spk_q1,
        spk_q2,
        spk_q3,
        spk_q4,
    ) = get_data(ticker=ticker, year=year, data_source="earnings_calls")
    quarter_speakers = {"Q1": spk_q1, "Q2": spk_q2, "Q3": spk_q3, "Q4": spk_q4}

    # Unstructured SEC filings
    sec_docs, sec_form_names = get_data(
        ticker=ticker,
        year=year,
        data_source="unstructured",
        include_amends=True,
        filing_types=filing_types,
    )

    # Markdown SEC filings
    # （已有 get_data 生成的 markdown 存放在 output/SEC_EDGAR_FILINGS_MD）
    md_dir = OUTPUT_DIR / f"SEC_EDGAR_FILINGS_MD/{ticker}-{year}"
    md_docs = []
    if md_dir.exists():
        from langchain_text_splitters import MarkdownHeaderTextSplitter

        hdr_split = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "H1"), ("##", "H2"), ("###", "H3")]
        )
        for md_subdir in md_dir.iterdir():
            md_path = md_subdir / f"{md_subdir.name}.md"
            content = md_path.read_text()
            filing_type = "-".join(md_subdir.name.split("-")[-2:])
            docs = hdr_split.split_text(content)
            for d in docs:
                d.metadata.update({"filing_type": filing_type})
            md_docs.extend(docs)

    # ------------------------------------------------------------
    # 2. 构建 / 加载向量库
    # ------------------------------------------------------------
    ec_db = build_vector_db(
        TXT_SPLITTER.split_documents(earnings_docs),
        PROJECT_ROOT / "earnings-call-db",
        "earnings_call",
    )
    sec_text_db = build_vector_db(
        TXT_SPLITTER.split_documents(sec_docs),
        PROJECT_ROOT / "sec-filings-db",
        "sec_filings",
    )
    sec_md_db = build_vector_db(
        md_docs,
        PROJECT_ROOT / "sec-filings-md-db",
        "sec_filings_md",
    )

    # ------------------------------------------------------------
    # 3. 定义查询函数
    # ------------------------------------------------------------
    def query_earnings(question: str, quarter: str) -> str:
        assert quarter in quarter_vals, f"quarter 必须是 {quarter_vals}"
        relevant = ec_db.similarity_search(
            question,
            k=5,
            filter={"quarter": {"$eq": quarter}},
        )
        return "\n\n".join([doc.page_content for doc in relevant])

    def query_sec(question: str, form_name: str) -> str:
        assert form_name in sec_form_names, f"form 必须是 {sec_form_names}"
        db = (
            sec_md_db
            if form_name.startswith("10-K") or "10-Q" in form_name
            else sec_text_db
        )
        relevant = db.similarity_search(
            question,
            k=5,
            filter={
                "filing_type" if db is sec_md_db else "form_name": {"$eq": form_name}
            },
        )
        return "\n\n".join([doc.page_content for doc in relevant])

    # ------------------------------------------------------------
    # 4. AutoGen 代理：Planner ↔ ToolProxy
    # ------------------------------------------------------------
    llm_cfg = {"model": "gpt-4o-mini"}
    planner = ConversableAgent(
        name="Planner",
        system_message=(
            "You are a helpful financial assistant. "
            "Decide whether to use earnings_call_db (query_earnings) or sec_filings_db (query_sec) "
            f"to answer. Possible SEC forms: {sec_form_names}. Quarters: {quarter_vals}. "
            "When done, say TERMINATE."
        ),
        llm_config=llm_cfg,
        human_input_mode="NEVER",
        is_termination_msg=lambda m: "TERMINATE" in m.get("content", ""),
    )
    tool_proxy = ConversableAgent(
        name="ToolProxy",
        system_message="You execute tool calls.",
        llm_config=False,
        human_input_mode="ALWAYS",
        default_auto_reply="Please choose a proper tool.",
    )

    register_function(query_earnings, caller=planner, executor=tool_proxy)
    register_function(query_sec, caller=planner, executor=tool_proxy)

    # ------------------------------------------------------------
    # 5. 触发对话
    # ------------------------------------------------------------
    user_question = params.get(
        "question", "What risk factors did Google mention in its latest 10-K?"
    )
    planner.initiate_chat(recipient=tool_proxy, message=user_question, max_turns=10)

    # 提取对话全过程
    from tutorials_wrapper.utils import extract_all

    messages = extract_all(planner)

    return {"result": messages}
