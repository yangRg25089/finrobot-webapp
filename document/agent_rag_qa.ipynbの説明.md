## agent_rag_qa.ipynb

このノートブックでは、Autogen の RAG（Retrieval-Augmented Generation）ワークフローを使って、PDF／HTML レポートからの QA（質問応答）を自動化する仕組みを構築しています。大まかな流れは以下のとおりです。

1. **ライブラリのインポート**

   ```python
   import autogen
   from finrobot.agents.workflow import SingleAssistantRAG
   ```

   * `autogen` フレームワーク本体
   * FinRobot 独自の RAG 用ワークフロークラス `SingleAssistantRAG`

2. **LLM 設定の準備**

   ```python
   llm_config = {
       "config_list": autogen.config_list_from_json(
           "../OAI_CONFIG_LIST",
           filter_dict={"model": ["openai/gpt-4o-mini"]},
       ),
       "timeout": 120,
       "temperature": 0,
   }
   ```

   * 外部 JSON から OpenAI の `gpt-4o-mini` モデルを読み込み
   * タイムアウトは120秒、出力の確率分布は温度 0（確定的返答）

3. **最初の RAG エージェント生成と QA 実行**

   ```python
   assitant = SingleAssistantRAG(
       "Data_Analyst",
       llm_config,
       human_input_mode="NEVER",
       retrieve_config={
           "task": "qa",
           "vector_db": None,  # 現バージョンではベクトルDB連携にバグあり
           "docs_path": ["../report/Microsoft_Annual_Report_2023.pdf"],
           "chunk_token_size": 1000,
           "get_or_create": True,
           "collection_name": "msft_analysis",
           "must_break_at_empty_line": False,
       },
   )
   assitant.chat("How's msft's 2023 income? Provide with some analysis.")
   ```

   * `SingleAssistantRAG` を使い、

     * `docs_path` に年次報告書 PDF を指定
     * トークンサイズ 1000 で分割
     * 内部で（コロンなし）メモリキャッシュ or インデックスを作成
   * `chat` メソッドで “2023年の収益はどうだったか、分析つきで教えて” と質問し、
     モデルが該当箇所を検索→要約→応答

4. **別の資料（10-K レポート）での再利用**

   ```python
   assitant = SingleAssistantRAG(
       "Data_Analyst",
       llm_config,
       human_input_mode="NEVER",
       retrieve_config={
           "task": "qa",
           "vector_db": None,
           "docs_path": ["../report/2023-07-27_10-K_msft-20230630.htm.pdf"],
           "chunk_token_size": 2000,
           "collection_name": "msft_10k",
           "get_or_create": True,
           "must_break_at_empty_line": False,
       },
       rag_description=(
           "Retrieve content from MSFT's 2023 10-K report for detailed question answering."
       ),
   )
   assitant.chat("How's msft's 2023 income? Provide with some analysis.")
   ```

   * 同じエージェント名・設定で、今度は 10-K レポート PDF を利用
   * `chunk_token_size` を 2000 に増やし、大きめのテキストブロックからも効率的に RAG
   * `rag_description` でエージェントの振る舞いを補足説明

5. **ポイントまとめ**

   * **SingleAssistantRAG**：ドキュメント→ベクトル化→インデックス作成→検索→LLM 応答、を一連で実行
   * **retrieve\_config**：資料パス、チャンクサイズ、コレクション名などを指定
   * **human\_input\_mode="NEVER"**：API 呼び出しだけで完結し、人の追加入力を不要に
   * 何度でも別資料で再インスタンス化するだけで、同じフローを繰り返せる

6. **補足ユーモア**

   > これで「Annual Report 読むの飽きた～」なんて言わせない！RAG がサクッと要点だけ教えてくれる頼もしい相棒が完成です。

---

**まとめ**：
agent\_rag\_qa.ipynb は、Annual Report や 10-K などの重いドキュメントを RAG で読み込ませ、LLM による要約・分析・QA を快適に行うテンプレートを示しています。設定さえ整えれば、あとは質問を投げるだけで即レスポンスが返ってきます！


### 実行結果：

3. **最初の RAG エージェント生成と QA 実行**　の実行結果：

```
[33mUser_Proxy[0m (to Data_Analyst):

How's msft's 2023 income? Provide with some analysis.

--------------------------------------------------------------------------------
[autogen.oai.client: 08-06 10:32:03] {696} WARNING - Model openai/gpt-4o-mini is not found. The cost will be 0. In your config_list, add field {"price" : [prompt_price_per_1k, completion_token_price_per_1k]} for customized pricing.
[33mData_Analyst[0m (to User_Proxy):


[32m***** Suggested tool call (call_Cf1b63jqEl7i2bUfMMVzpJaV): retrieve_content *****[0m
Arguments: 
{"message":"Microsoft's 2023 income analysis","n_results":3}
[32m*********************************************************************************[0m

--------------------------------------------------------------------------------
[35m
>>>>>>>> EXECUTING FUNCTION retrieve_content...
Call ID: call_Cf1b63jqEl7i2bUfMMVzpJaV
Input arguments: {'message': "Microsoft's 2023 income analysis", 'n_results': 3}[0m
Trying to create collection.
/Users/ronny/miniconda3/envs/finrobot/lib/python3.10/site-packages/tqdm/auto.py:21: TqdmWarning: IProgress not found. Please update jupyter and ipywidgets. See https://ipywidgets.readthedocs.io/en/stable/user_install.html
  from .autonotebook import tqdm as notebook_tqdm
doc_ids:  [['doc_0']]
[32mAdding content of doc doc_0 to context.[0m
[33mUser_Proxy[0m (to Data_Analyst):

[32m***** Response from calling tool (call_Cf1b63jqEl7i2bUfMMVzpJaV) *****[0m
Below is the context retrieved from the required file based on your query.
If you can't answer the question with or without the current context, you should try using a more refined search query according to your requirements, or ask for more contexts.

Your current query is: Microsoft's 2023 income analysis

Retrieved context is: Equity Research Report: Microsoft Corporation
FinRobot
https://ai4finance.org/
Income Summarization The company experienced a 7% Year-over-Year increase in revenue, driven by significant contributions from its Intelligent Cloud and Productivity and Business Processes segments, indicating a strong demand for cloud-based solutions and productivity software. Despite the revenue growth, the Cost of Goods Sold (COGS) increased by 5%, suggesting a need for closer cost control measures to improve cost efficiency and maintain profitability. The gross margin increased by 8%, while operating income grew by 6%, highlighting effective cost management and operational efficiency. However, net income slightly decreased by 1%, underscoring challenges in sustaining net profitability against operational costs and investments. The Diluted EPS remained stable at $9.68, reflecting a balanced investor outlook but indicating the need for strategic initiatives to enhance shareholder value.
https://github.com/AI4Finance-Foundation/FinRobot
Report date: 2023-07-27
Key data
Rating
strongBuy
Target Price
400 - 400 (md. 400.0)
6m avg daily vol (USDmn)
29.99
Closing Price (USD)
335.15
Market Cap (USDmn)
2456918.88
52 Week Price Range (USD)
217.07 - 349.70
BVPS (USD)
27.70
Business Highlights Productivity and Business Processes segment saw a notable revenue increase, driven by Office 365 Commercial and LinkedIn. This growth highlights the robust demand for Microsoft's productivity tools and professional networking platform, reflecting the company's ability to meet evolving workplace needs. More Personal Computing segment experienced a decrease in revenue, primarily due to declines in Windows and Devices. This downturn underscores the challenges faced by the segment, including shifting consumer preferences and the competitive landscape in PC and device markets.
Share Performance
Company Situation Microsoft Corporation operates in the technology industry, focusing on empowering individuals and organizations globally through a wide array of products and services. Its core strengths lie in its diverse portfolio, including cloud-based solutions, software, devices, and services that leverage artificial intelligence (AI) to enhance productivity and business processes. Microsoft's competitive advantages include its innovation in AI, cloud infrastructure, and collaboration tools, such as Microsoft Teams and Office 365. Current industry trends emphasize digital transformation, cloud computing, and AI innovation. Opportunities for Microsoft include expanding its cloud services and integrating AI across its product suite. Challenges involve navigating a highly competitive technology landscape and adapting to changing consumer and business needs. Recent strategic initiatives include investing in AI capabilities, expanding its cloud infrastructure, and acquiring companies like Nuance to bolster its healthcare AI solutions. Microsoft's response to market conditions includes focusing on cloud and AI technologies to drive future growth. Microsoft's strategic focus on AI and cloud computing, coupled with its ability to innovate and adapt, positions it well for continued success in the dynamic technology industry.
PE & EPS
Risk Assessment Microsoft Corporation faces significant challenges primarily from strategic and competitive risks due to intense competition and rapid technological changes in the tech sector. The company's increasing focus on cloud-based services introduces execution and competitive risks, including the need to innovate and manage costs effectively. Additionally, Microsoft is subject to various legal, regulatory, and litigation risks that could impact its business operations and financial performance. These include government scrutiny under U.S. and foreign competition laws, as well as potential liabilities from claims of intellectual property infringement. Financial Metrics
FY (USD mn)
2019
2020
2021
2022
2023
Operating Revenue 125843.0
143015.0
168088.0
198270.0
211915.0
Adjusted Net Profit 39240.0
44281.0
61271.0
72738.0
72361.0
Adjusted EPS
5.11
5.82
8.12
9.7
9.72
EBIT Margin
0.34
0.37
0.42
0.42
0.42
ROE
0.38
0.37
0.43
0.44
0.35
PE Ratio
26.53
34.97
33.37
26.47
35.04
EV/EBITDA
19.32
23.48
25.03
19.74
24.35
PB Ratio
10.17
13.09
14.4
11.56
12.3


[32m**********************************************************************[0m

--------------------------------------------------------------------------------
/Users/ronny/miniconda3/envs/finrobot/lib/python3.10/site-packages/torch/nn/modules/module.py:1747: FutureWarning: `encoder_attention_mask` is deprecated and will be removed in version 4.55.0 for `BertSdpaSelfAttention.forward`.
  return forward_call(*args, **kwargs)
[autogen.oai.client: 08-06 10:32:46] {696} WARNING - Model openai/gpt-4o-mini is not found. The cost will be 0. In your config_list, add field {"price" : [prompt_price_per_1k, completion_token_price_per_1k]} for customized pricing.
[33mData_Analyst[0m (to User_Proxy):

In 2023, Microsoft Corporation reported a revenue of approximately $211.92 billion, reflecting a 7% Year-over-Year (YoY) increase. This growth was primarily driven by strong performance in its Intelligent Cloud and Productivity and Business Processes segments, indicating a robust demand for cloud-based solutions and productivity software.

### Key Financial Metrics:
- **Revenue Growth**: 7% YoY increase
- **Cost of Goods Sold (COGS)**: Increased by 5%
- **Gross Margin**: Increased by 8%
- **Operating Income**: Grew by 6%
- **Net Income**: Slightly decreased by 1% to approximately $72.36 billion
- **Diluted EPS**: Remained stable at $9.68

### Analysis:
1. **Revenue Drivers**: The significant revenue increase in the Productivity and Business Processes segment was largely attributed to Office 365 Commercial and LinkedIn, showcasing the strong demand for Microsoft's productivity tools. However, the More Personal Computing segment faced challenges, with a decline in revenue due to decreased sales in Windows and Devices, reflecting shifting consumer preferences and competitive pressures in the PC market.

2. **Cost Management**: Despite the revenue growth, the increase in COGS suggests that Microsoft needs to implement tighter cost control measures to enhance cost efficiency and maintain profitability. The increase in gross margin indicates that the company is managing its costs effectively, but the slight decrease in net income highlights the challenges in sustaining profitability amidst rising operational costs and investments.

3. **Market Position and Strategy**: Microsoft continues to leverage its strengths in AI and cloud computing, which are critical in the current technology landscape. The company's strategic initiatives, including investments in AI capabilities and expanding its cloud infrastructure, position it well for future growth. However, it must navigate intense competition and adapt to rapidly changing consumer and business needs.

4. **Risk Factors**: Microsoft faces significant strategic and competitive risks, particularly in the cloud services sector. The need for continuous innovation and effective cost management is crucial. Additionally, legal and regulatory risks could impact its operations and financial performance.

### Conclusion:
Overall, Microsoft's financial performance in 2023 reflects a strong demand for its cloud and productivity solutions, although challenges in the More Personal Computing segment and slight declines in net income indicate areas for improvement. The company's focus on AI and cloud technologies, along with its ability to innovate, positions it favorably for continued success in the technology industry.

--------------------------------------------------------------------------------
[33mUser_Proxy[0m (to Data_Analyst):



--------------------------------------------------------------------------------
[autogen.oai.client: 08-06 10:32:47] {696} WARNING - Model openai/gpt-4o-mini is not found. The cost will be 0. In your config_list, add field {"price" : [prompt_price_per_1k, completion_token_price_per_1k]} for customized pricing.
[33mData_Analyst[0m (to User_Proxy):

TERMINATE

--------------------------------------------------------------------------------
[31m
>>>>>>>> TERMINATING RUN (3a891826-f3f8-45c8-b0f1-532535e06197): Termination message condition on agent 'User_Proxy' met[0m
Current chat finished. Resetting agents ...
```

ChatGptで以下は、Microsoftの2023年度の財務実績とその分析を日本語で整理した内容です：

---

### ✅ **Microsoft 2023年度の収益ハイライト**

* **売上高**：2,119億ドル（前年比 +7%）
* **売上原価（COGS）**：前年比 +5%
* **粗利益率**：+8%
* **営業利益**：+6%
* **純利益**：723億6,100万ドル（前年比 **-1%**）
* **希薄化後EPS**（1株当たり利益）：**\$9.68（横ばい）**

---

### 🔍 **分析ポイント**

#### ① **主な収益源**

* **インテリジェントクラウド部門** と
* **プロダクティビティ＆ビジネスプロセス部門**（例：Office 365、LinkedIn）が大きく貢献。
* 一方で、**More Personal Computing部門**（Windowsやデバイス関連）は売上減。消費者の嗜好変化とPC市場の競争激化が背景。

#### ② **コスト構造と利益**

* 原価上昇に対し、粗利益率が改善 → 効率的なコスト管理の成果。
* ただし、純利益がわずかに減少 → 研究開発投資や運用コスト増が影響か。

#### ③ **企業戦略と市場位置**

* Microsoftは**AIとクラウド技術への注力**を継続。
* Nuance買収など、AIによるヘルスケア領域の強化も進行中。
* 将来の成長に向けた布石を多数打っており、クラウド需要やデジタル変革の流れに乗っている。

#### ④ **リスク要因**

* **競争激化**（特にクラウド領域）、**技術革新のスピード**への対応が必要。
* **法的・規制リスク**（独禁法や知的財産に関する訴訟リスクなど）にも注意が必要。

---

### 📌 **総評**

Microsoftの2023年は、**堅調なクラウドおよび生産性ソリューションへの需要**を背景に売上は増加。しかし、**個人向けPC関連の減速**や**純利益の微減**など課題も一部存在。
それでも、**AI・クラウドにフォーカスした戦略**と**堅固な財務体質**により、今後の成長ポテンシャルは依然として高いと評価できます。

---


4. **別の資料（10-K レポート）での再利用**　の実行結果：
```
[33mUser_Proxy[0m (to Data_Analyst):

How's msft's 2023 income? Provide with some analysis.

--------------------------------------------------------------------------------
[autogen.oai.client: 08-06 10:32:49] {696} WARNING - Model openai/gpt-4o-mini is not found. The cost will be 0. In your config_list, add field {"price" : [prompt_price_per_1k, completion_token_price_per_1k]} for customized pricing.
[33mData_Analyst[0m (to User_Proxy):


[32m***** Suggested tool call (call_jrlop6yvu1ylxncQci9aHVZ7): retrieve_content *****[0m
Arguments: 
{"message":"MSFT's 2023 income analysis and figures","n_results":3}
[32m*********************************************************************************[0m

--------------------------------------------------------------------------------
[35m
>>>>>>>> EXECUTING FUNCTION retrieve_content...
Call ID: call_jrlop6yvu1ylxncQci9aHVZ7
Input arguments: {'message': "MSFT's 2023 income analysis and figures", 'n_results': 3}[0m
Trying to create collection.
doc_ids:  [['doc_34', 'doc_32', 'doc_36']]
[32mAdding content of doc doc_34 to context.[0m
[32mAdding content of doc doc_32 to context.[0m
[32mAdding content of doc doc_36 to context.[0m
[33mUser_Proxy[0m (to Data_Analyst):

[32m***** Response from calling tool (call_jrlop6yvu1ylxncQci9aHVZ7) *****[0m
Below is the context retrieved from the required file based on your query.
If you can't answer the question with or without the current context, you should try using a more refined search query according to your requirements, or ask for more contexts.

Your current query is: MSFT's 2023 income analysis and figures

Retrieved context is: November 18, 2021 December 9, 2021 $ March 10, 2022 June 9, 2022 August 18, 2022 September 8, 2022
0.62 $ 0.62 0.62 0.62
4,652 4,645 4,632 4,621
December 7, 2021 March 14, 2022 June 14, 2022
February 17, 2022 May 19, 2022
Total
$
2.48 $
18,550
The dividend declared on June 13, 2023 was included in other current liabilities as of June 30, 2023.
90
PART II Item 8
NOTE 17 — ACCUMULATED OTHER COMPREHENSIVE INCOME (LOSS)
The following table summarizes the changes in accumulated other comprehensive income (loss) by component:
(In millions)
Year Ended June 30,
2023
2022
2021
Derivatives
Balance, beginning of period Unrealized gains (losses), net of tax of $9, $(15), and $9 Reclassiﬁcation adjustments for (gains) losses included in other
$
(13 ) $ 34
(19 ) $ (57 )
(38 ) 34
income (expense), net
(61 ) 13
79 (16 )
(17 ) 2
Tax expense (beneﬁt) included in provision for income taxes
Amounts reclassiﬁed from accumulated other comprehensive
income (loss)
(48 )
63
(15 )
Net change related to derivatives, net of tax of $(4), $1, and $7
(14 )
6
19
Balance, end of period
$
(27 ) $
(13 ) $
(19 )
Investments
Balance, beginning of period
(2,13
$
8 ) $ 3,222 $ 5,478
Unrealized losses, net of tax of $(393), $(1,440), and $(589)
(1,52
3 ) (5,405 ) (2,216 )
Reclassiﬁcation adjustments for (gains) losses included in other
income (expense), net
99 (20 )
57 (12 )
(63 ) 13
Tax expense (beneﬁt) included in provision for income taxes
Amounts reclassiﬁed from accumulated other comprehensive
income (loss)
79
45
(50 )
Net change related to investments, net of tax of $(373), $(1,428), and
(1,44
$(602)
4 ) (5,360 ) (2,266 ) 0 0
Cumulative eﬀect of accounting changes
10
Balance, end of period
(3,58
$
2 ) $ (2,138 ) $ 3,222
Translation Adjustments and Other
Balance, beginning of period
(2,52
(2,25
$
7 ) $ (1,381 ) $ (207 ) (1,146 )
4 ) 873
Translation adjustments and other, net of tax of $0, $0, and $(9)
Balance, end of period
(2,73
$
4 ) $ (2,527 ) $ (1,381 )
Accumulated other comprehensive income (loss), end of period
(6,34
$
3 ) $ (4,678 ) $ 1,822
NOTE 18 — EMPLOYEE STOCK AND SAVINGS PLANS
We grant stock-based compensation to employees and directors. Awards that expire or are canceled without delivery of shares generally become available for issuance under the plans. We issue new shares of Microsoft common stock to satisfy vesting of awards granted under our stock plans. We also have an ESPP for all eligible employees.
Stock-based compensation expense and related income tax beneﬁts were as follows:
(In millions)
Year Ended June 30,
2023
2022
2021
Stock-based compensation expense Income tax beneﬁts related to stock-based compensation
$ 9,611 $ 7,502 $ 6,118 1,651 1,293 1,065
Stock Plans
Stock awards entitle the holder to receive shares of Microsoft common stock as the award vests. Stock awards generally vest over a service period of four years or ﬁve years.
91
PART II Item 8
Executive Incentive Plan
Under the Executive Incentive Plan, the Compensation Committee approves stock awards to executive oﬃcers and certain senior executives. RSUs generally vest ratably over a service period of four years. PSUs generally vest over a performance period of three years. The number of shares the PSU holder receives is based on the extent to which the corresponding performance goals have been achieved.
Activity for All Stock Plans
The fair value of stock awards was estimated on the date of grant using the following assumptions:
Year ended June 30,
2023
2022
2021
Dividends per share (quarterly amounts) Interest rates
$ 0.62 – 0.68 $
0.56 – 0.62 $ 0.51 – 0.56 0.01% – 1.5%
2.0% – 5.4% 0.03% – 3.6%
During ﬁscal year 2023, the following activity occurred under our stock plans:
Weighted Average Grant-Date Fair
Shares
Value
(In millions)
Stock Awards
Nonvested balance, beginning of year
93 $ 56 (44 ) (9 )
227.59 252.59 206.90 239.93
(a)
Granted Vested Forfeited
Nonvested balance, end of year
96 $
(174 ) (4,291 ) (1,602 ) (3,104 ) (103 )
Deferred income tax liabilities
(10,18
$
1 ) $ (9,274 )
Net deferred income tax assets
$ 19,730
$ 13,285
Reported As
Other long-term assets Long-term deferred income tax liabilities
$ 20,163 $ 13,515 (230 )
(433 )
Net deferred income tax assets
$ 19,730
$ 13,285
(a) Provisions enacted in the TCJA related to the capitalization for tax purposes of research and development expenditures became eﬀective on July 1, 2022. These provisions require us to capitalize research and development expenditures and amortize them on our U.S. tax return over ﬁve or ﬁfteen years, depending on where research is conducted.
Deferred income tax balances reﬂect the eﬀects of temporary diﬀerences between the carrying amounts of assets and liabilities and their tax bases and are stated at enacted tax rates expected to be in eﬀect when the taxes are paid or recovered.
As of June 30, 2023, we had federal, state, and foreign net operating loss carryforwards of $509 million, $1.2 billion, and $2.3 billion, respectively. The federal and state net operating loss carryforwards have varying expiration dates ranging from ﬁscal year 2024 to 2043 or indeﬁnite carryforward periods, if not utilized. The majority of our foreign net operating loss carryforwards do not expire. Certain acquired net operating loss carryforwards are subject to an annual limitation but are expected to be realized with the exception of those which have a valuation allowance. As of June 30, 2023, we had $456 million federal capital loss carryforwards for U.S. tax purposes from our acquisition of Nuance. The federal capital loss carryforwards are subject to an annual limitation and will expire in ﬁscal year 2025.
84
PART II Item 8
The valuation allowance disclosed in the table above relates to the foreign net operating loss carryforwards, federal capital loss carryforwards, and other net deferred tax assets that may not be realized.
Income taxes paid, net of refunds, were $23.1 billion, $16.0 billion, and $13.4 billion in ﬁscal years 2023, 2022, and 2021, respectively.
Uncertain Tax Positions
Gross unrecognized tax beneﬁts related to uncertain tax positions as of June 30, 2023, 2022, and 2021, were $17.1 billion, $15.6 billion, and $14.6 billion, respectively, which were primarily included in long- term income taxes in our consolidated balance sheets. If recognized, the resulting tax beneﬁt would aﬀect our eﬀective tax rates for ﬁscal years 2023, 2022, and 2021 by $14.4 billion, $13.3 billion, and $12.5 billion, respectively.
As of June 30, 2023, 2022, and 2021, we had accrued interest expense related to uncertain tax positions of $5.2 billion, $4.3 billion, and $4.3 billion, respectively, net of income tax beneﬁts. The provision for income taxes for ﬁscal years 2023, 2022, and 2021 included interest expense related to uncertain tax positions of $918 million, $36 million, and $274 million, respectively, net of income tax beneﬁts.
The aggregate changes in the gross unrecognized tax beneﬁts related to uncertain tax positions were as follows:
(In millions)
Year Ended June 30,
2023
2022
2021
Beginning unrecognized tax beneﬁts Decreases related to settlements Increases for tax positions related to the current year Increases for tax positions related to prior years Decreases for tax positions related to prior years Decreases due to lapsed statutes of limitations
$ 15,593 $ 14,550 $ 13,792 (195 ) 790 461 (297 ) (1 )
(329 ) 1,051 870 (60 ) (5 )
(317 ) 1,145 461 (246 ) 0
Ending unrecognized tax beneﬁts
$ 17,120 $ 15,593 $ 14,550
We settled a portion of the Internal Revenue Service (“IRS”) audit for tax years 2004 to 2006 in ﬁscal year 2011. In February 2012, the IRS withdrew its 2011 Revenue Agents Report related to unresolved issues for tax years 2004 to 2006 and reopened the audit phase of the examination. We also settled a portion of the IRS audit for tax years 2007 to 2009 in ﬁscal year 2016, and a portion of the IRS audit for tax years 2010 to 2013 in ﬁscal year 2018. In the second quarter of ﬁscal year 2021, we settled an additional portion of the IRS audits for tax years 2004 to 2013 and made a payment of $1.7 billion, including tax and interest. We remain under audit for tax years 2004 to 2017.
As of June 30, 2023, the primary unresolved issues for the IRS audits relate to transfer pricing, which could have a material impact in our consolidated ﬁnancial statements when the matters are resolved. We believe our allowances for income tax contingencies are adequate. We have not received a proposed assessment for the unresolved key transfer pricing issues. We do not expect a ﬁnal resolution of these issues in the next 12 months. Based on the information currently available, we do not anticipate a signiﬁcant increase or decrease to our tax contingencies for these issues within the next 12 months.
We are subject to income tax in many jurisdictions outside the U.S. Our operations in certain jurisdictions remain subject to examination for tax years 1996 to 2022, some of which are currently under audit by local tax authorities. The resolution of each of these audits is not expected to be material to our consolidated ﬁnancial statements.
85
PART II Item 8
NOTE 13 — UNEARNED REVENUE
Unearned revenue by segment was as follows:
(In millions)
June 30,
2023
2022
Productivity and Business Processes Intelligent Cloud More Personal Computing
$ 27,572 $ 24,558 19,371 21,563 4,479 4,678
Total
$ 53,813 $ 48,408
Changes in unearned revenue were as follows:
(In millions)
Year Ended June 30, 2023
Balance, beginning of period
$ 48,408 123,93 5 (118,53
Deferral of revenue
Recognition of unearned revenue
0 )
Balance, end of period
$ 53,813
Revenue allocated to remaining performance obligations, which includes unearned revenue and amounts that will be invoiced and recognized as revenue in future periods, was $229 billion as of June 30, 2023, of which $224 billion is related to the commercial portion of revenue. We expect to recognize approximately 45% of this revenue over the next 12 months and the remainder thereafter.
NOTE 14 — LEASES
We have operating and ﬁnance leases for datacenters, corporate oﬃces, research and development facilities, Microsoft Experience Centers, and certain equipment. Our leases have remaining lease terms of less than 1 year to 18 years, some of which include options to extend the leases for up to 5 years, and some of which include options to terminate the leases within 1 year.
The components of lease expense were as follows:
(In millions)
Year Ended June 30,
2023
2022
2021
Operating lease cost
$
2,875 $
2,461 $
2,127
Finance lease cost:
Amortization of right-of-use assets Interest on lease liabilities
$
1,352 $ 501
980 $ 429
921 386
Total ﬁnance lease cost
$
1,853 $
1,409 $
1,307
Supplemental cash ﬂow information related to leases was as follows:
(In millions)
Year Ended June 30,
2023
2022
2021
Cash paid for amounts included in the measurement of lease
liabilities: Operating cash ﬂows from operating leases Operating cash ﬂows from ﬁnance leases Financing cash ﬂows from ﬁnance leases
$
2,706 $ 501 1,056
2,368 $ 429 896
2,052 386 648
Right-of-use assets obtained in exchange for lease
obligations: Operating leases Finance leases
3,514 3,128
5,268 4,234
4,380 3,290
86
PART II Item 8
Supplemental balance sheet information related to leases was as follows:
(In millions, except lease term and discount rate)
June 30,
2023
2022
Operating Leases
Operating lease right-of-use assets
$
14,346 $
13,148
Other current liabilities Operating lease liabilities
$
2,409 $
2,228 11,489
12,728
Total operating lease liabilities
$
15,137 $
13,717
Finance Leases
Property and equipment, at cost Accumulated depreciation
$
20,538 $ (4,647 )
Our Microsoft Cloud revenue, which includes Azure and other cloud services, Oﬃce 365 Commercial, the commercial portion of LinkedIn, Dynamics 365, and other commercial cloud properties, was $111.6 billion, $91.4 billion, and $69.1 billion in ﬁscal years 2023, 2022, and 2021, respectively. These amounts are primarily included in Server products and cloud services, Oﬃce products and cloud services, LinkedIn, and Dynamics in the table above.
Assets are not allocated to segments for internal reporting presentations. A portion of amortization and depreciation is included with various other costs in an overhead allocation to each segment. It is impracticable for us to separately identify the amount of amortization and depreciation by segment that is included in the measure of segment proﬁt or loss.
Long-lived assets, excluding ﬁnancial instruments and tax assets, classiﬁed by the location of the controlling statutory company and with countries over 10% of the total shown separately, were as follows:
(In millions)
June 30,
2023
2022
2021
United States Ireland Other countries
$114,380 $ 106,430 $ 76,153 13,303 16,359 38,858 56,500
15,505 44,433
Total
$187,239 $ 166,368 $ 128,314
95
PART II Item 8
REPORT OF INDEPENDENT REGISTERED PUBLIC ACCOUNTING FIRM
To the Stockholders and the Board of Directors of Microsoft Corporation
Opinion on the Financial Statements
We have audited the accompanying consolidated balance sheets of Microsoft Corporation and subsidiaries (the "Company") as of June 30, 2023 and 2022, the related consolidated statements of income, comprehensive income, cash ﬂows, and stockholders' equity, for each of the three years in the period ended June 30, 2023, and the related notes (collectively referred to as the "ﬁnancial statements"). In our opinion, the ﬁnancial statements present fairly, in all material respects, the ﬁnancial position of the Company as of June 30, 2023 and 2022, and the results of its operations and its cash ﬂows for each of the three years in the period ended June 30, 2023, in conformity with accounting principles generally accepted in the United States of America.
We have also audited, in accordance with the standards of the Public Company Accounting Oversight Board (United States) (PCAOB), the Company's internal control over ﬁnancial reporting as of June 30, 2023, based on criteria established in Internal Control — Integrated Framework (2013) issued by the Committee of Sponsoring Organizations of the Treadway Commission and our report dated July 27, 2023, expressed an unqualiﬁed opinion on the Company's internal control over ﬁnancial reporting.
Basis for Opinion
These ﬁnancial statements are the responsibility of the Company's management. Our responsibility is to express an opinion on the Company's ﬁnancial statements based on our audits. We are a public accounting ﬁrm registered with the PCAOB and are required to be independent with respect to the Company in accordance with the U.S. federal securities laws and the applicable rules and regulations of the Securities and Exchange Commission and the PCAOB.
We conducted our audits in accordance with the standards of the PCAOB. Those standards require that we plan and perform the audit to obtain reasonable assurance about whether the ﬁnancial statements are free of material misstatement, whether due to error or fraud. Our audits included performing procedures to assess the risks of material misstatement of the ﬁnancial statements, whether due to error or fraud, and performing procedures that respond to those risks. Such procedures included examining, on a test basis, evidence regarding the amounts and disclosures in the ﬁnancial statements. Our audits also included evaluating the accounting principles used and signiﬁcant estimates made by management, as well as evaluating the overall presentation of the ﬁnancial statements. We believe that our audits provide a reasonable basis for our opinion.
Critical Audit Matters
The critical audit matters communicated below are matters arising from the current-period audit of the ﬁnancial statements that were communicated or required to be communicated to the audit committee and that (1) relate to accounts or disclosures that are material to the ﬁnancial statements and (2) involved our especially challenging, subjective, or complex judgments. The communication of critical audit matters does not alter in any way our opinion on the ﬁnancial statements, taken as a whole, and we are not, by communicating the critical audit matters below, providing separate opinions on the critical audit matters or on the accounts or disclosures to which they relate.
Revenue Recognition – Refer to Note 1 to the ﬁnancial statements
Critical Audit Matter Description
The Company recognizes revenue upon transfer of control of promised products or services to customers in an amount that reﬂects the consideration the Company expects to receive in exchange for those products or services. The Company oﬀers customers the ability to acquire multiple licenses of software products and services, including cloud-based services, in its customer agreements through its volume licensing programs.
96
PART II Item 8
Signiﬁcant judgment is exercised by the Company in determining revenue recognition for these customer agreements, and includes the following:
Determination of whether products and services are considered distinct performance obligations that should be accounted for separately versus together, such as software licenses and related services that are sold with cloud-based services.
The pattern of delivery (i.e., timing of when revenue is recognized) for each distinct
performance obligation.
Identiﬁcation and treatment of contract terms that may impact the timing and amount of
revenue recognized (e.g., variable consideration, optional purchases, and free services).
Determination of stand-alone selling prices for each distinct performance obligation and for
products and services that are not sold separately.
Given these factors and due to the volume of transactions, the related audit eﬀort in evaluating management's judgments in determining revenue recognition for these customer agreements was extensive and required a high degree of auditor judgment.
How the Critical Audit Matter Was Addressed in the Audit
Our principal audit procedures related to the Company's revenue recognition for these customer agreements included the following:
We tested the eﬀectiveness of controls related to the identiﬁcation of distinct performance obligations, the determination of the timing of revenue recognition, and the estimation of variable consideration.
We evaluated management's signiﬁcant accounting policies related to these customer
agreements for reasonableness.
We selected a sample of customer agreements and performed the following procedures:
Obtained and read contract source documents for each selection, including master agreements,
and other documents that were part of the agreement.

Tested management's identiﬁcation and treatment of contract terms.
Assessed the terms in the customer agreement and evaluated the appropriateness of management's application of their accounting policies, along with their use of estimates, in the determination of revenue recognition conclusions.
We evaluated the reasonableness of management's estimate of stand-alone selling prices for
products and services that are not sold separately.
We tested the mathematical accuracy of management's calculations of revenue and the
associated timing of revenue recognized in the ﬁnancial statements.
Income Taxes – Uncertain Tax Positions – Refer to Note 12 to the ﬁnancial statements
Critical Audit Matter Description
The Company's long-term income taxes liability includes uncertain tax positions related to transfer pricing issues that remain unresolved with the Internal Revenue Service ("IRS"). The Company remains under IRS audit, or subject to IRS audit, for tax years subsequent to 2003. While the Company has settled a portion of the IRS audits, resolution of the remaining matters could have a material impact on the Company's ﬁnancial statements.
Conclusions on recognizing and measuring uncertain tax positions involve signiﬁcant estimates and management judgment and include complex considerations of the Internal Revenue Code, related regulations, tax case laws, and prior-year audit settlements. Given the complexity and the subjective nature of the transfer pricing issues that remain unresolved with the IRS, evaluating management's estimates relating to their determination of uncertain tax positions required extensive audit eﬀort and a high degree of auditor judgment, including involvement of our tax specialists.
97
PART II Item 8
How the Critical Audit Matter Was Addressed in the Audit
Our principal audit procedures to evaluate management's estimates of uncertain tax positions related to unresolved transfer pricing issues included the following:
We evaluated the appropriateness and consistency of management's methods and assumptions used in the identiﬁcation, recognition, measurement, and disclosure of uncertain tax positions, which included testing the eﬀectiveness of the related internal controls.
We read and evaluated management's documentation, including relevant accounting policies and information obtained by management from outside tax specialists, that detailed the basis of the uncertain tax positions.
We tested the reasonableness of management's judgments regarding the future resolution of the uncertain tax positions, including an evaluation of the technical merits of the uncertain tax positions.
For those uncertain tax positions that had not been eﬀectively settled, we evaluated whether management had appropriately considered new information that could signiﬁcantly change the recognition, measurement or disclosure of the uncertain tax positions.
We evaluated the reasonableness of management's estimates by considering how tax law,
including statutes, regulations and case law, impacted management's judgments.
/s/ DELOITTE & TOUCHE LLP
Seattle, Washington July 27, 2023
We have served as the Company's auditor since 1983.
98
PART II Item 9, 9A


[32m**********************************************************************[0m

--------------------------------------------------------------------------------
[autogen.oai.client: 08-06 10:33:17] {696} WARNING - Model openai/gpt-4o-mini is not found. The cost will be 0. In your config_list, add field {"price" : [prompt_price_per_1k, completion_token_price_per_1k]} for customized pricing.
[33mData_Analyst[0m (to User_Proxy):

Microsoft's financial performance for the fiscal year ending June 30, 2023, shows significant growth and stability. Here are some key highlights and analysis based on the retrieved data:

### Key Financial Figures:
1. **Total Revenue**: Microsoft reported a substantial increase in revenue, particularly in its cloud services, which generated $111.6 billion in 2023, up from $91.4 billion in 2022. This growth reflects the increasing demand for cloud computing and related services.
   
2. **Income Taxes**: The company paid $23.1 billion in income taxes in 2023, compared to $16.0 billion in 2022. This increase indicates higher profitability and possibly a broader tax base due to expanded operations.

3. **Stock-Based Compensation**: Microsoft reported stock-based compensation expenses of $9.6 billion in 2023, up from $7.5 billion in 2022. This increase suggests a focus on retaining talent through equity incentives, which is common in tech companies.

4. **Unearned Revenue**: The total unearned revenue as of June 30, 2023, was $53.8 billion, an increase from $48.4 billion in 2022. This indicates a strong pipeline of future revenue, as unearned revenue represents payments received for services not yet delivered.

### Analysis:
- **Cloud Growth**: The significant increase in cloud revenue highlights Microsoft's successful transition to a cloud-first strategy. The growth in Azure and other cloud services is a critical driver of overall revenue and profitability, positioning Microsoft as a leader in the cloud computing market.

- **Tax Obligations**: The rise in income taxes paid reflects the company's robust financial performance. However, the presence of uncertain tax positions, particularly related to transfer pricing issues with the IRS, indicates potential risks that could impact future financial results.

- **Stock Compensation**: The increase in stock-based compensation aligns with industry trends where companies incentivize employees with equity. This strategy can enhance employee retention and align their interests with shareholders.

- **Future Revenue**: The growth in unearned revenue suggests that Microsoft has a solid foundation for future earnings. The expectation to recognize approximately 45% of this revenue over the next 12 months indicates a healthy revenue stream that can support ongoing operations and investments.

### Conclusion:
Overall, Microsoft's financial performance in 2023 demonstrates strong growth, particularly in its cloud services, while also highlighting areas of potential risk related to tax positions. The company's strategic focus on cloud computing and employee retention through stock compensation appears to be effective in driving both current and future success. 

If you need further analysis or specific metrics, feel free to ask! 

TERMINATE

--------------------------------------------------------------------------------
[31m
>>>>>>>> TERMINATING RUN (48bf02b6-4fd5-4e59-85c6-25dcf988a5f9): Termination message condition on agent 'User_Proxy' met[0m
Current chat finished. Resetting agents ...
```

以下是 Microsoft 2023 財年（截至 2023 年 6 月 30 日）的財務表現整理與分析（日文版）：

---

## ✅ Microsoft 2023年度 財務ハイライト

### 🌐 **売上・事業成長**

* **クラウド売上**：1,116億ドル（前年：914億ドル、前年比 **+22%**）
  　↳ *Azure、Office 365、LinkedIn、Dynamics 365 などを含む商用クラウドサービス*

* **繰延収益（Unearned Revenue）**：538億ドル（前年：484億ドル、**+11%**）
  　↳ *今後のサービス提供に紐づく将来の売上の見込み*

---

### 💰 **利益とコスト**

* **所得税支払額**：231億ドル（前年：160億ドル）
  　↳ *利益増加とともに税負担も上昇*

* **株式報酬費用（Stock-Based Compensation）**：96億ドル（前年：75億ドル）
  　↳ *優秀な人材の維持・確保に注力している傾向*

---

## 🔍 分析ポイント

### ① **クラウドドリブンな成長**

* Microsoft は「クラウドファースト戦略」を強化しており、商用クラウド部門が急成長。
* 特に Azure（クラウドインフラ）の存在感が増し、企業のDX（デジタルトランスフォーメーション）需要をしっかり取り込んでいる。

### ② **収益の質と持続性**

* **繰延収益の増加** は、安定的かつ予測可能な収益基盤を示唆。
* 今後12ヶ月間で約45%を売上として認識予定 → 継続的な成長の余地あり。

### ③ **リスク要因（税務）**

* アメリカ国税庁（IRS）との**移転価格に関する未解決の課税問題**を抱える。
* 不確実な税務ポジション（Uncertain Tax Positions）に関して、将来の財務数値に影響を与える可能性も。

### ④ **人的資本投資**

* 株式報酬の増加は、従業員モチベーションの向上や離職率低下に繋がる。
* GAFAをはじめとしたグローバル企業では一般的な報酬戦略。

---

## ✅ 総合評価

* **クラウド部門の力強い成長**と、**安定した将来の収益見込み**がMicrosoftの強み。
* 一方で、**税務面の不確実性や法的リスク**には注意が必要。
* 今後もクラウド＋AIを中心とした成長が見込まれるが、グローバル展開による複雑な規制対応とコスト管理が引き続き鍵となる。

---

さらに特定の財務指標や事業部ごとの分析が必要であれば、お気軽にどうぞ。
