const translations = {
  common: {
    loading: '分析中...',
    error: '错误',
    noChart: '暂无分析结果',
    symbol: '股票代码',
    startDate: '开始日期',
    endDate: '结束日期',
    strategies: '脚本',
    english: '英文',
    chinese: '中文',
    japanese: '日文',
    submit: '提交',
    submitting: '提交中...',
    switchscript: '切换脚本',
    summary: '会话',
    elapsedTime: '耗时',
    scriptIntroTitle: '脚本说明',
    paramTitle: '参数',
    conversationHistory: '对话历史',
    currentResult: '当前结果',
    historyResult: '历史结果',
    generatedImages: '生成的图片',
    generatedFiles: '生成的文件',
    download: '下载',
    pdfPreview: 'PDF预览',
    hint: '提示',
    deleteHistory: '删除历史记录',
    confirmDelete: '确定要删除这条历史记录吗？',
    deleteSuccess: '历史记录删除成功',
    deleteFailed: '删除历史记录失败',
    params: {
      company: '公司',
      date: '日期',
      year: '年',
      ticker: '股票代码',
      fyear: '会计年度',
      question: '问题',
      question1: '问题 1',
      question2: '问题 2',
      include_amends: '包含修订版',
      build_marker_pdf: '生成PDF',
      from_markdown: '从Markdown生成',
      filing_types: '申报类型',
    },
    descriptions: {
      beginner: {
        agent_annual_report:
          '生成“年度研究报告” Agent：自动读取公司 10-K，按固定提纲写 400-450 字分析，再把结果排版成 PDF。流程里展示了文件工具链、图像预览与 PDF 保存。',
        agent_fingpt_forecaster:
          '把原 FinGPT-Forecaster 用 FinRobot 重写：拉取价格+新闻→用多轮对话提取因子→预测未来 5 日涨跌并给出推理，演示了单一 Assistant 的“Chain-of-Thought”式市场预测。',
        agent_rag_earnings_call_sec_filings:
          'RAG（检索增强生成）多数据库示例：同时向 Earnings Call 转录稿、SEC 10-K/10-Q（文本 / Markdown）三套向量库检索，并用工具函数动态选择最合适的库来回答财报问题。',
        agent_rag_qa:
          '最简版 RAG-QA：把单份 PDF 切块→存 Chroma→用 RetrieveChat 代理做问答，展示了 FinRobot 与 Autogen 的最小可行整合。',
        agent_rag_qa_up:
          '上一脚本的“加强版”：支持多文档、可配置 chunk size / collection 名，演示如何持久化向量库并复用。',
        ollama_function_call:
          '函数调用 demo： 请求结构化 JSON，再由代码执行; 展示了 FinRobot 托管自定义工具、解析 JSON-schema 的流程。',
        ollama_stock_chart:
          '用 Ollama 在 Notebook 内对话生成股票分析指令 → 后端 Python 拉行情绘图 → 返回图像并 Markdown 总结，体现“LLM+代码”协作绘制可视化的完整闭环。',
      },
    },
  },
};

export default translations;
