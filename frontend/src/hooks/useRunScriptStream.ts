import { useCallback, useEffect, useRef, useState } from 'react';

export type StreamEvent =
  | { type: 'stdout'; text: string }
  | { type: 'stderr'; text: string }
  | { type: 'phase'; step?: string; msg?: string }
  | { type: 'event'; name?: string; payload?: any }
  | { type: 'result'; result: any }
  | { type: 'error'; error: string }
  | { type: 'exit' };

export interface UseRunScriptStreamState {
  logs: { type: 'stdout' | 'stderr'; text: string }[];
  phase?: { step?: string; msg?: string };
  result: any | null;
  error: string | null;
  images: string[];
  resultFolder: string | null;
  running: boolean;
}

export function useRunScriptStream() {
  const [state, setState] = useState<UseRunScriptStreamState>({
    logs: [],
    result: null,
    error: null,
    images: [],
    resultFolder: null,
    running: false,
  });

  const esRef = useRef<EventSource | null>(null);

  const appendLog = useCallback((type: 'stdout' | 'stderr', text: string) => {
    setState((s) => ({ ...s, logs: [...s.logs, { type, text }] }));
  }, []);

  const start = useCallback(
    (opts: {
      scriptPath: string;
      folder: string;
      lang?: string;
      payload?: Record<string, any>;
    }) => {
      const { scriptPath, folder, lang = 'jp', payload = {} } = opts;
      // 关闭旧流
      if (esRef.current) {
        esRef.current.close();
        esRef.current = null;
      }

      const base =
        (import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000';

      const qs = new URLSearchParams({
        script_path: `${folder}/${scriptPath}`,
        lang,
        // 注意：SSE 查询串只能用字符串，这里用 JSON + encodeURIComponent
        params: encodeURIComponent(JSON.stringify(payload)),
      });

      const url = `${base}/api/run-script/stream?${qs.toString()}`;
      const es = new EventSource(url, { withCredentials: false });
      esRef.current = es;

      setState({
        logs: [],
        result: null,
        error: null,
        images: [],
        resultFolder: null,
        running: true,
      });

      es.onmessage = (evt) => {
        try {
          const ev: StreamEvent = JSON.parse(evt.data as any);

          switch (ev.type) {
            case 'stdout':
            case 'stderr':
              appendLog(ev.type, ev.text);
              break;

            case 'phase':
              setState((s) => ({
                ...s,
                phase: { step: ev.step, msg: ev.msg },
              }));
              // 同时把阶段也打到“终端”
              if (ev.step || ev.msg) {
                appendLog(
                  'stdout',
                  `[phase] ${ev.step ?? ''} ${ev.msg ?? ''}`.trim(),
                );
              }
              break;

            case 'event':
              // 后端 guard_run 的异常事件
              if (ev.name === 'exception') {
                setState((s) => ({
                  ...s,
                  error: ev.payload?.msg ?? 'Unknown error',
                }));
                appendLog('stderr', `EXCEPTION: ${ev.payload?.msg ?? ''}`);
              }
              break;

            case 'result':
              {
                const r = (ev as any).result ?? null;
                const images: string[] = Array.isArray(r?.result_images)
                  ? r.result_images
                  : [];
                const folder: string | null = r?.result_folder ?? null;
                const err: string | null = r?.error ?? null;
                setState((s) => ({
                  ...s,
                  result: r,
                  images,
                  resultFolder: folder,
                  error: err ?? s.error,
                }));
              }
              break;

            case 'error':
              setState((s) => ({ ...s, error: ev.error || 'Server error' }));
              appendLog('stderr', `ERROR: ${ev.error}`);
              break;

            case 'exit':
              setState((s) => ({ ...s, running: false }));
              es.close();
              esRef.current = null;
              break;

            default:
              break;
          }
        } catch (e) {
          console.error('SSE parse failed:', e, evt.data);
        }
      };

      es.addEventListener('error', (e) => {
        console.error('SSE connection error', e);
        setState((s) => ({
          ...s,
          running: false,
          error: s.error ?? 'SSE connection error',
        }));
        if (esRef.current) {
          esRef.current.close();
          esRef.current = null;
        }
      });
    },
    [appendLog],
  );

  const stop = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
    setState((s) => ({ ...s, running: false }));
  }, []);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      if (esRef.current) {
        esRef.current.close();
        esRef.current = null;
      }
    };
  }, []);

  return { ...state, start, stop };
}
