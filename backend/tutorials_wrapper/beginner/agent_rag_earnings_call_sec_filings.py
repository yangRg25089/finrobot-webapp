from __future__ import annotations

"""
Refactor of the notebook `agent_rag_earnings_call_sec_filings.ipynb` into a
single Python module compatible with this project's script entry pattern.

Notes:
- Cell boundaries are preserved via section comments to keep left-right diffs small.
- Shell commands (git/pip/apt) are kept as comments. Execute them externally if needed.
- Default values match the notebook and can be overridden via `params`.
- Entry point stays: run(params: dict, lang: str) -> dict
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from common.utils import (
    build_lang_directive,
    create_output_directory,
    get_script_result,
    save_output_files,
)


def _cd_finance_llm_data(base_dir: Path) -> Path:
    """Align with the notebook's `os.chdir("finance_llm_data")` step.
    Tries common relative locations; falls back to creating a working folder.
    """
    candidates = [
        base_dir / "finance_llm_data",
        base_dir.parent / "finance_llm_data",
        base_dir,
    ]
    for p in candidates:
        if (p / "finance_data.py").exists():
            os.chdir(p)
            return p
    # As a last resort, stay where we are (caller should ensure path)
    os.chdir(base_dir)
    return base_dir


# %% [markdown]
# ## INSTALL THE REQUIRED PACKAGES
# If you are in google colab, make sure to restart run-time

# %%
# !pip install -r requirements.txt

# %%
# The original notebook changed directory again:
# os.chdir("/tutorials_beginner/finance_llm_data")
# We will keep current working directory after `_cd_finance_llm_data`.

# %%
# from finance_data import get_data  # imported inside run() after chdir

# %% [markdown]
# ## The wkhtmltopdf wheel will help in converting html to pdfs

# %%
# %%capture
# !sudo apt-get install wkhtmltopdf


# -----------------------------
# Entry point
# -----------------------------


def run(params: Dict[str, Any], lang: str) -> Dict[str, Any]:
    """
    Script entry compatible with this project.

    params (overrides):
      - ticker: str (default 'GOOG')
      - year: str (default '2023')
      - filing_types: List[str] (default ['10-K','10-Q'])
      - include_amends: bool (default True)
      - build_marker_pdf: bool (default False)  # the PDF extraction is slow in notebook
      - from_markdown: bool (default True)

    Returns: {"result": messages}
    """
    # -----------------------------
    # Params & working dir setup
    # -----------------------------
    ticker = params.get("ticker", "IBM")
    year = params.get("year", "2024")
    filing_types = params.get("filing_types", ["10-K", "10-Q"])
    include_amends = params.get("include_amends", True)
    build_marker_pdf = params.get("build_marker_pdf", False)
    FROM_MARKDOWN = params.get("from_markdown", True)

    _AI_model = params.get("_AI_model", "gemini-2.5-flash")
    lang_snippet = build_lang_directive(lang)

    base_dir = Path.cwd()
    work_dir = _cd_finance_llm_data(base_dir)

    # Deferred imports that depend on CWD
    from finance_data import get_data  # type: ignore

    # -----------------------------
    # EARNINGS DATA
    # -----------------------------
    (
        earnings_docs,
        earnings_call_quarter_vals,
        speakers_list_1,
        speakers_list_2,
        speakers_list_3,
        speakers_list_4,
    ) = get_data(ticker=ticker, year=year, data_source="earnings_calls")

    # -----------------------------
    # UNSTRUCTURED SEC DATA (TEXT-ONLY)
    # -----------------------------
    sec_data, sec_form_names = get_data(
        ticker=ticker,
        year=year,
        data_source="unstructured",
        include_amends=include_amends,
        filing_types=filing_types,
    )

    # -----------------------------
    # MARKER PDF EXTRACTION (optional; slow)
    # -----------------------------
    if build_marker_pdf:
        # THE BELOW CELL TOOK ~13 MINUTES ON GOOGLE COLAB
        get_data(
            ticker=ticker,
            year=year,
            data_source="marker_pdf",
            batch_processing=False,
            batch_multiplier=1,
        )

    # -----------------------------
    # VECTOR DATABASE FOR RAG APPLICATIONS
    # -----------------------------
    # !pip install langchain-chroma -U -q
    # !pip install sentence-transformers -q

    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_chroma import Chroma
    from langchain_community.embeddings.sentence_transformer import (
        SentenceTransformerEmbeddings,
    )

    emb_fn = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1024,
        chunk_overlap=100,
        length_function=len,
    )

    earnings_calls_split_docs = text_splitter.split_documents(earnings_docs)

    # Generate IDs for documents
    import uuid

    # Create database directory path
    db_base_path = base_dir / "static" / "db"
    db_base_path.mkdir(parents=True, exist_ok=True)

    doc_ids = [str(uuid.uuid4()) for _ in earnings_calls_split_docs]

    earnings_call_db = Chroma.from_documents(
        earnings_calls_split_docs,
        emb_fn,
        persist_directory=str(db_base_path / "earnings-call-db"),
        collection_name="earnings_call",
        ids=doc_ids,
    )

    sec_filings_split_docs = text_splitter.split_documents(sec_data)

    # Generate IDs for documents
    sec_doc_ids = [str(uuid.uuid4()) for _ in sec_filings_split_docs]

    sec_filings_unstructured_db = Chroma.from_documents(
        sec_filings_split_docs,
        emb_fn,
        persist_directory=str(db_base_path / "sec-filings-db"),
        collection_name="sec_filings",
        ids=sec_doc_ids,
    )

    # -----------------------------
    # Markdown-based SEC filings DB
    # -----------------------------
    from langchain.schema import Document  # noqa: F401  # kept for minimal diff
    from langchain_text_splitters import MarkdownHeaderTextSplitter

    headers_to_split_on: List[Tuple[str, str]] = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on
    )

    markdown_dir = Path("output/SEC_EDGAR_FILINGS_MD")
    md_content_list: List[List[str]] = []
    tdir = markdown_dir / f"{ticker}-{year}"
    if tdir.exists():
        for md_dirs in os.listdir(tdir):
            md_file_path = tdir / md_dirs / f"{md_dirs}.md"
            if md_file_path.exists():
                content = md_file_path.read_text(encoding="utf-8", errors="ignore")
                md_content_list.append([content, "-".join(md_dirs.split("-")[-2:])])

    sec_markdown_docs: List[Document] = []
    for md_content in md_content_list:
        md_header_splits = markdown_splitter.split_text(md_content[0])
        for md_header_docs in md_header_splits:
            # Add a extra metadata of filing type
            md_header_docs.metadata.update({"filing_type": md_content[1]})
        sec_markdown_docs.extend(md_header_splits)

    # Only create the database if we have documents
    if sec_markdown_docs:
        # Generate IDs for markdown documents
        md_doc_ids = [str(uuid.uuid4()) for _ in sec_markdown_docs]

        sec_filings_md_db = Chroma.from_documents(
            sec_markdown_docs,
            emb_fn,
            persist_directory=str(db_base_path / "sec-filings-md-db"),
            collection_name="sec_filings_md",
            ids=md_doc_ids,
        )
    else:
        print("No SEC markdown documents found, skipping markdown database creation")
        sec_filings_md_db = None

    # -----------------------------
    # CHAT WITH DATA USING AUTOGEN
    # -----------------------------
    # !pip install -U -q pyautogen

    quarter_speaker_dict: Dict[str, List[str]] = {
        "Q1": speakers_list_1,
        "Q2": speakers_list_2,
        "Q3": speakers_list_3,
        "Q4": speakers_list_4,
    }

    # Tools kept identical to notebook (closures capture the DBs created above)
    def query_database_earnings_call(question: str, quarter: str) -> str:
        assert (
            quarter in earnings_call_quarter_vals
        ), "The quarter should be from Q1, Q2, Q3, Q4"

        req_speaker_list: List[str] = []
        quarter_speaker_list = quarter_speaker_dict[quarter]

        for sl in quarter_speaker_list:
            if sl in question or sl.lower() in question:
                req_speaker_list.append(sl)
        if len(req_speaker_list) == 0:
            req_speaker_list = quarter_speaker_list

        relevant_docs = earnings_call_db.similarity_search(
            question,
            k=5,
            filter={
                "$and": [
                    {"quarter": {"$eq": quarter}},
                    {"speaker": {"$in": req_speaker_list}},
                ]
            },
        )

        speaker_releavnt_dict: Dict[str, str] = {}
        for doc in relevant_docs:
            speaker = doc.metadata["speaker"]
            speaker_text = doc.page_content
            if speaker not in speaker_releavnt_dict:
                speaker_releavnt_dict[speaker] = speaker_text
            else:
                speaker_releavnt_dict[speaker] += " " + speaker_text

        relevant_speaker_text = ""
        for speaker, text in speaker_releavnt_dict.items():
            relevant_speaker_text += speaker + ": "
            relevant_speaker_text += text + "\n\n"

        return relevant_speaker_text

    def query_database_unstructured_sec(question: str, sec_form_name: str) -> str:
        assert (
            sec_form_name in sec_form_names
        ), f"The search form type should be in {sec_form_names}"

        relevant_docs = sec_filings_unstructured_db.similarity_search(
            question, k=5, filter={"form_name": {"$eq": sec_form_name}}
        )
        relevant_section_dict: Dict[str, str] = {}
        for doc in relevant_docs:
            section = doc.metadata["section_name"]
            section_text = doc.page_content
            if section not in relevant_section_dict:
                relevant_section_dict[section] = section_text
            else:
                relevant_section_dict[section] += " " + section_text

        relevant_section_text = ""
        for section, text in relevant_section_dict.items():
            relevant_section_text += section + ": "
            relevant_section_text += text + "\n\n"
        return relevant_section_text

    def query_database_markdown_sec(question: str, sec_form_name: str) -> str:
        assert (
            sec_form_name in sec_form_names
        ), f"The search form type should be in {sec_form_names}"

        if sec_filings_md_db is not None:
            relevant_docs = sec_filings_md_db.similarity_search(
                question, k=3, filter={"filing_type": {"$eq": sec_form_name}}
            )
        else:
            relevant_docs = []
        relevant_section_text = ""
        for relevant_text in relevant_docs:
            relevant_section_text += relevant_text.page_content + "\n\n"

        return relevant_section_text

    def query_database_sec(question: str, sec_form_name: str) -> str:
        """Unified SEC query function (toggles markdown/unstructured)"""
        if not FROM_MARKDOWN:
            return query_database_unstructured_sec(question, sec_form_name)
        else:
            return query_database_markdown_sec(question, sec_form_name)

    # Build system messages (unchanged logic)
    sec_form_system_msg = ""
    for sec_form in sec_form_names:
        if sec_form == "10-K":
            sec_form_system_msg += "10-K for yearly data, "
        elif "10-Q" in sec_form:
            quarter = sec_form[-1]
            sec_form_system_msg += f"{sec_form} for Q{quarter} data, "
    sec_form_system_msg = sec_form_system_msg[:-2] if sec_form_system_msg else ""

    earnings_call_system_message = ", ".join(earnings_call_quarter_vals)

    system_msg = (
        f"You are a helpful financial assistant and your task is to select the sec_filings or "
        f"earnings_call or financial_books to best answer the question.\n"
        f"You can use query_database_sec(question,sec_form) by passing question and relevant sec_form names like {sec_form_system_msg}\n"
        f"or you can use query_database_earnings_call(question,quarter) by passing question and relevant quarter names with possible values {earnings_call_system_message}\n"
        f"or you can use query_database_books(question) to get relevant documents from financial textbooks about valuation and investing philosophies. "
        f"When you are ready to end the coversation, reply TERMINATE"
    )

    # -----------------------------
    # Autogen agent setup (kept same)
    # -----------------------------
    from autogen import ConversableAgent, register_function

    llm_config = {"model": _AI_model}

    user_proxy = ConversableAgent(
        name="Planner Admin",
        system_message=system_msg,
        code_execution_config=False,
        llm_config=llm_config,
        human_input_mode="NEVER",
        is_termination_msg=lambda msg: "TERMINATE" in msg["content"],
    )

    tool_proxy = ConversableAgent(
        name="Tool Proxy",
        system_message=(
            "Analyze the response from user proxy and decide whether the suggested "
            "database is suitable . Answer in simple yes or no"
        ),
        llm_config=False,
        default_auto_reply="Please select the right database.",
        human_input_mode="ALWAYS",
    )

    tools_dict = {
        "sec": [query_database_sec, "Tool to query SEC filings database"],
        "earnings_call": [
            query_database_earnings_call,
            "Tool to query earnings call transcripts database",
        ],
    }

    for tool_name, tool in tools_dict.items():
        register_function(
            tool[0],
            caller=user_proxy,
            executor=tool_proxy,
            name=tool[0].__name__,
            description=tool[1],
        )

    # -----------------------------
    # Example queries (kept; can be overridden via params["inputs"])
    # -----------------------------
    queries = [
        "What is the strategy of Google for artificial intelligence?",
        "What are the risk factors that Google faced this year?",
        "What was forward estimates of Google for the year 2023?",
    ]

    messages: List[Any] = []
    for input_text in queries:
        chat_result = user_proxy.initiate_chat(
            recipient=tool_proxy, message=input_text, max_turns=10
        )
        messages.append(chat_result)

    # Save output files using common utilities
    result_path = create_output_directory(
        base_dir, "agent_rag_earnings_call_sec_filings"
    )

    # Prepare additional data
    additional_data = {
        "ticker": ticker,
        "year": year,
        "filing_types": filing_types,
        "include_amends": include_amends,
        "earnings_documents": len(earnings_docs) if "earnings_docs" in locals() else 0,
        "sec_documents": len(sec_data) if "sec_data" in locals() else 0,
    }

    # Save output files
    save_output_files(
        output_path=result_path,
        script_name="agent_rag_earnings_call_sec_filings",
        params=params,
        messages=messages,
        queries=queries,
        additional_data=additional_data,
    )

    # Return standardized result
    return get_script_result(messages=messages, output_path=result_path)
