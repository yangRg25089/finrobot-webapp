const translations = {
  common: {
    loading: 'Analysing...',
    error: 'Error',
    noChart: 'No analysied result available',
    symbol: 'Symbol',
    startDate: 'Start Date',
    endDate: 'End Date',
    strategies: 'Scripts',
    english: 'English',
    chinese: 'Chinese',
    japanese: 'Japanese',
    submit: 'Submit',
    submitting: 'Submitting...',
    switchscript: 'Switch Scripts',
    summary: 'Conversation',
    elapsedTime: 'Elapsed Time',
    scriptIntroTitle: 'Script Description',
    paramTitle: 'Parameters',
    conversationHistory: 'Conversation History',
    currentResult: 'Current Result',
    historyResult: 'History Result',
    generatedImages: 'Generated Images',
    generatedFiles: 'Generated Files',
    download: 'Download',
    pdfPreview: 'PDF Preview',
    hint: 'Hint',
    deleteHistory: 'Delete History',
    confirmDelete: 'Are you sure you want to delete this history record?',
    deleteSuccess: 'History deleted successfully',
    deleteFailed: 'Failed to delete history',
    params: {
      company: 'Company',
      date: 'Date',
      year: 'Year',
      ticker: 'Ticker',
      fyear: 'Fiscal Year',
      question: 'Question',
      question1: 'Question 1',
      question2: 'Question 2',
      include_amends: 'Include Amends',
      build_marker_pdf: 'Build Marker PDF',
      from_markdown: 'Generate from Markdown',
      filing_types: 'Filing Types',
      competitors: 'Competitors',
      start_date: 'Start Date',
      end_date: 'End Date',
      symbol: 'Symbol',
      benchmark: 'Benchmark',
      _AI_model: 'AI model',
    },
    descriptions: {
      beginner: {
        agent_annual_report:
          'Annual-report writer agent: automatically reads a company’s 10-K, writes a 400-450-word analysis following a fixed outline, and lays it out as a PDF while demonstrating the file tool-chain, image preview and PDF saving.',
        agent_fingpt_forecaster:
          'FinGPT-Forecaster re-implemented with FinRobot: pulls prices and news, uses multi-turn dialogue to extract factors, predicts the next five trading days’ movement and explains the reasoning, showcasing a single-assistant chain-of-thought market forecast.',
        agent_rag_earnings_call_sec_filings:
          'Multi-database RAG example: queries three vector stores—earnings-call transcripts and SEC 10-K/10-Q in both text and Markdown—then chooses the best one via tool functions to answer financial-report questions.',
        agent_rag_qa:
          'Minimal RAG-QA: splits one PDF into chunks, stores them in Chroma, and answers questions through a RetrieveChat agent, showing the smallest viable FinRobot + Autogen integration.',
        agent_rag_qa_up:
          'Enhanced version of the previous script: supports multiple documents, configurable chunk size and collection name, and demonstrates how to persist and reuse the vector store.',
        ollama_function_call:
          'function-calling demo: requests structured JSON, executes it with code, and shows FinRobot hosting custom tools and parsing a JSON schema.',
        ollama_stock_chart:
          'Ollama stock-chart notebook: chats with Ollama to generate stock-analysis commands, the Python backend fetches data and plots, then returns the image and a Markdown summary—illustrating a full LLM-plus-code visualization loop.',
      },
    },
  },
};

export default translations;
