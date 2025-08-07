import { useState, useRef, useCallback } from 'react';

type ScriptPayload = {
  script_name: string;
  folder: string;
  params: any;
};

type ApiSuccess<T = any> = { result: T };
type ApiErrorBody = { detail?: unknown; message?: string };

export const useScriptApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  /** 将前端表单数据转成后端需要的请求体 */
  const transformToScriptRequest = useCallback(
    (data: ScriptPayload, language: string) => ({
      script_path: `${data.folder}/${data.script_name}`,
      params: data.params,
      lang: language,
    }),
    [],
  );

  /** 解析后端错误体，尽量拿到可读的信息 */
  const parseError = useCallback(
    async (response: Response): Promise<string> => {
      let message = `${response.status} ${response.statusText}`;
      try {
        const text = await response.text();
        if (!text) return message;

        try {
          const body: ApiErrorBody = JSON.parse(text);
          const detail =
            typeof body?.detail === 'string'
              ? body.detail
              : body?.detail
                ? JSON.stringify(body.detail)
                : undefined;
          message = body?.message ?? detail ?? message;
        } catch {
          // 非 JSON：直接用纯文本
          message = text;
        }
      } catch {
        // ignore
      }
      return message;
    },
    [],
  );

  /**
   * 调用后端运行脚本
   * 返回 { result: ... }；失败返回 null，并在 error 中给出原因
   */
  const runscript = useCallback(
    async <T = any>(
      data: ScriptPayload,
      language: string,
    ): Promise<ApiSuccess<T> | null> => {
      setLoading(true);
      setError(null);

      // 取消上一次未完成的请求（防抖/避免污染）
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const base =
          (import.meta as any).env?.VITE_API_BASE_URL ??
          'http://localhost:8000';
        const response = await fetch(`${base}/api/run-script`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(transformToScriptRequest(data, language)),
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(await parseError(response));
        }

        // 某些接口可能返回 204
        if (response.status === 204) {
          return { result: null as unknown as T };
        }

        const json = (await response.json()) as ApiSuccess<T>;
        return json;
      } catch (err: unknown) {
        // 被主动取消的请求，不当做错误提示
        if ((err as any)?.name === 'AbortError') {
          return null;
        }
        const message =
          err instanceof Error
            ? err.message
            : typeof err === 'string'
              ? err
              : 'Unknown error';
        setError(message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [parseError, transformToScriptRequest],
  );

  const resetError = useCallback(() => setError(null), []);

  return { runscript, loading, error, resetError };
};
