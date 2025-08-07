const translations = {
  common: {
    loading: '分析中...',
    error: 'エラー',
    noChart: '分析結果がありません',
    symbol: 'シンボル',
    startDate: '開始日',
    endDate: '終了日',
    strategies: 'スクリプト',
    english: '英語',
    chinese: '中国語',
    japanese: '日本語',
    submit: '送信',
    submitting: '送信中...',
    switchscript: 'スクリプトを切り替える',
    summary: '会話',
    elapsedTime: '実行時間',
    scriptIntroTitle: 'スクリプト説明',
    paramTitle: 'パラメタ',
    params: {
      company: '会社',
      date: '日付',
      year: '年',
      ticker: 'ティッカー',
      fyear: '会計年度',
      question: '質問',
    },
    descriptions: {
      agent_annual_report:
        '年次レポート作成エージェント。企業の10-Kを自動で読み取り、固定のアウトラインに沿って400〜450語の分析を書き、PDFにレイアウトします。ファイルツールチェーン、画像プレビュー、PDF保存の流れを示します。',
      agent_fingpt_forecaster:
        'FinGPT-Forecaster を FinRobot で再実装。価格とニュースを取得し、複数ターンの対話で要因を抽出、次の5営業日の値動きを予測して理由を説明します。単一アシスタントによるチェイン・オブ・ソート型の市場予測を示します。',
      agent_rag_earnings_call_sec_filings:
        '複数データベース RAG の例。決算説明会のトランスクリプトと SEC 10-K/10-Q（テキスト／Markdown）の3つのベクトルストアを検索し、ツール関数で最適なデータベースを選択して財務報告の質問に答えます。',
      agent_rag_qa:
        '最小構成の RAG-QA。1つのPDFをチャンク化してChromaに保存し、RetrieveChat エージェントでQAを行います。FinRobot と Autogen の最小実装例です。',
      agent_rag_qa_up:
        '前スクリプトの強化版。複数ドキュメントに対応し、チャンクサイズやコレクション名を設定可能。ベクトルストアの永続化と再利用方法を示します。',
      ollama_function_call:
        '関数呼び出しデモ。構造化 JSON を取得し、コードで実行。FinRobot によるカスタムツールのホスティングと JSON スキーマ解析を示します。',
      ollama_stock_chart:
        'Ollama ストックチャートのノートブック。Ollama と対話して株式分析コマンドを作成し、Python バックエンドでデータを取得してプロット、画像とMarkdown要約を返します。LLM＋コード協調による可視化ループを示します。',
    },
  },
};

export default translations;
