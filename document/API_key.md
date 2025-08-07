
### “免费起步”且支持工具调用

| 提供方                         | 工具/函数调用支持                          | OpenAI 兼容       | 免费/试用政策（要不要绑卡）                     | 备注                                                                                |
| --------------------------- | ---------------------------------- | --------------- | ---------------------------------- | --------------------------------------------------------------------------------- |
| **Groq**                    | 支持（OpenAI 样式 `tools`/`tool_calls`） | 是               | “Get started for free”（无需绑卡）       | 有专门的 Tool Use 文档；模型如 `llama-3.3-70b-versatile` 等。([console.groq.com][1])          |
| **Mistral (La Plateforme)** | 支持 Function Calling                | 自家与 OpenAI 兼容都行 | 有 **Free API tier**，限速较严           | 官方有 function calling 教程与免费层说明。([docs.mistral.ai][2])                              |
| **Cohere (Command R/R+)**   | 支持 Tool Use（函数调用）                  | 自家接口            | 提供 **Trial/Evaluation Key**（免费、限流） | 文档明确“Trial key 调用免费”。([docs.cohere.com][3], [Cohere][4])                          |
| **Fireworks.ai**            | 支持 Function Calling（OpenAI 兼容）     | 是               | 新用户**自动获免费额度**（常见文案：\$1 起）         | 有 function calling 指南与兼容说明。([docs.fireworks.ai][5], [Fireworks AI][6])            |
| **NVIDIA NIM（API Catalog）** | 支持 Tool/Function Calling           | 是               | 注册送**1000 试用积分**，可申请至**5000**      | 文档与论坛都写了 function calling & 试用积分。([NVIDIA Docs][7], [NVIDIA Developer Forums][8]) |
| **Together.ai**             | 支持 Function Calling（OpenAI 兼容）     | 是               | 可申请 **Startup / Research** 免费额度    | 需提交申请表单。([docs.together.ai][9], [Together AI][10])                                |

> **关于 Gemini（AI Studio）**
>
> * **原生 Gemini API** 与 **Vertex AI** 均支持“Function calling / Tools”。([AI Google][11], [Google Cloud][12])
> * **OpenAI 兼容端点**仍处于 **beta**，特性逐步覆盖，官方页面也标注“当前有局限”。你遇到“tools 不工作”多半是走了兼容端点未完全覆盖；改用 **原生 Gemini API** 或 \*\*Vertex 的兼容样例（已示范 function calling）\*\*会更稳。([AI Google][13], [Google Cloud][14])

---

## 在 Autogen 里怎么切换到“可用工具调用”的免费商家？

### 选项 1：走 OpenAI 兼容（改 base\_url + key，最低改动）

以 **Groq** 为例（其它如 Fireworks、NIM、Together 也同理）：

```json
// OAI_CONFIG_LIST 里的一个条目
{
  "model": "llama-3.3-70b-versatile",
  "api_key": "${GROQ_API_KEY}",
  "base_url": "https://api.groq.com/openai/v1",
  "api_type": "openai"
}
```

Groq 明确支持 OpenAI 兼容与 **Tool Use**（`tools`/`tool_choice`），你的 Autogen 工具调用代码可原样沿用。([console.groq.com][1])

以 **Fireworks** 为例：

```json
{
  "model": "accounts/fireworks/models/llama-v3p1-70b-instruct",
  "api_key": "${FIREWORKS_API_KEY}",
  "base_url": "https://api.fireworks.ai/inference/v1",
  "api_type": "openai"
}
```

Fireworks 的 function calling 与 OpenAI **完全兼容**（有少量差异点，见文档），上来就能测。([docs.fireworks.ai][5])

以 **NVIDIA NIM** 为例（OpenAI 兼容）：

```json
{
  "model": "meta/llama-3.1-70b-instruct",
  "api_key": "${NVIDIA_API_KEY}",
  "base_url": "https://integrate.api.nvidia.com/v1",
  "api_type": "openai"
}
```

NIM 文档明确支持 `tools` 与 `tool_choice`。([NVIDIA Docs][7])


[1]: https://console.groq.com/docs/tool-use?utm_source=chatgpt.com "Introduction to Tool Use - GroqDocs"
[2]: https://docs.mistral.ai/capabilities/function_calling/?utm_source=chatgpt.com "Function calling"
[3]: https://docs.cohere.com/docs/tool-use-overview?utm_source=chatgpt.com "Basic usage of tool use (function calling)"
[4]: https://cohere.com/pricing?utm_source=chatgpt.com "Pricing | Secure and Scalable Enterprise AI"
[5]: https://docs.fireworks.ai/guides/function-calling?utm_source=chatgpt.com "Using function-calling"
[6]: https://fireworks.ai/blog/fireworks-raises-the-quality-bar-with-function-calling-model-and-api-release?utm_source=chatgpt.com "Fireworks Raises the Quality Bar with Function Calling ..."
[7]: https://docs.nvidia.com/nim/large-language-models/latest/function-calling.html?utm_source=chatgpt.com "Function (Tool) Calling with NVIDIA NIM for LLMs"
[8]: https://forums.developer.nvidia.com/t/nim-api-credits/305703?utm_source=chatgpt.com "NIM API Credits - Access/Accounts"
[9]: https://docs.together.ai/docs/function-calling?utm_source=chatgpt.com "Function Calling"
[10]: https://www.together.ai/forms/startups-program?utm_source=chatgpt.com "Together Startups Program"
[11]: https://ai.google.dev/gemini-api/docs/function-calling?utm_source=chatgpt.com "Function calling with the Gemini API | Google AI for Developers"
[12]: https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling?utm_source=chatgpt.com "Introduction to function calling | Generative AI on Vertex AI"
[13]: https://ai.google.dev/gemini-api/docs/openai "OpenAI compatibility  |  Gemini API  |  Google AI for Developers"
[14]: https://cloud.google.com/vertex-ai/generative-ai/docs/samples/generativeaionvertexai-gemini-chat-completions-function-calling-config?utm_source=chatgpt.com "Use function calling with Gemini using OpenAI SDK"
[15]: https://microsoft.github.io/autogen/0.2/docs/tutorial/tool-use?utm_source=chatgpt.com "Tool Use | AutoGen 0.2"
