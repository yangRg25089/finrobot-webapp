import { useCallback, useEffect, useState } from 'react';
import { API_ENDPOINTS, buildApiUrl } from '../config/api';

export interface HistoryRecord {
  id: string;
  timestamp: string;
  script_name: string;
  prompt: string;
  message_count: number;
  messages: any[];
  display_name: string;
  relative_path: string;
  generated_files?: { files: any[] } | null;
}

export interface HistoryApiResponse {
  success: boolean;
  script_name: string;
  total_records: number;
  records: HistoryRecord[];
  error?: string;
}

export interface AllHistoriesResponse {
  success: boolean;
  scripts: Record<
    string,
    {
      total_records: number;
      latest_timestamp: string;
      latest_display_name: string;
    }
  >;
  error?: string;
}

export const useHistoryApi = (scriptName?: string) => {
  const [historyRecords, setHistoryRecords] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 加载指定脚本的历史记录
  const loadHistory = useCallback(
    async (targetScriptName?: string) => {
      const scriptToLoad = targetScriptName || scriptName;
      if (!scriptToLoad) return;

      setLoading(true);
      setError(null);

      try {
        const url = buildApiUrl(API_ENDPOINTS.history(scriptToLoad));
        const response = await fetch(url);
        const data: HistoryApiResponse = await response.json();

        if (data.success) {
          setHistoryRecords(data.records || []);
        } else {
          setError(data.error || 'Failed to load history');
          setHistoryRecords([]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setHistoryRecords([]);
      } finally {
        setLoading(false);
      }
    },
    [scriptName],
  );

  // 删除历史记录
  const deleteHistory = useCallback(
    async (targetScriptName: string, timestamp?: string) => {
      setLoading(true);
      setError(null);

      try {
        const url = buildApiUrl(
          API_ENDPOINTS.deleteHistory(targetScriptName, timestamp),
        );

        const response = await fetch(url, { method: 'DELETE' });
        const data = await response.json();

        if (data.success) {
          // 重新加载历史记录
          await loadHistory(targetScriptName);
          return true;
        } else {
          setError(data.error || 'Failed to delete history');
          return false;
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        return false;
      } finally {
        setLoading(false);
      }
    },
    [loadHistory],
  );

  // 获取所有脚本的历史概览
  const loadAllHistories = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const url = buildApiUrl(API_ENDPOINTS.allHistories);
      const response = await fetch(url);
      const data: AllHistoriesResponse = await response.json();

      if (data.success) {
        return data.scripts;
      } else {
        setError(data.error || 'Failed to load all histories');
        return {};
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return {};
    } finally {
      setLoading(false);
    }
  }, []);

  // 当 scriptName 变化时自动加载历史记录
  useEffect(() => {
    if (scriptName) {
      loadHistory(scriptName);
    } else {
      // 清空历史记录
      setHistoryRecords([]);
      setError(null);
    }
  }, [scriptName, loadHistory]);

  // 重置状态
  const resetHistory = useCallback(() => {
    setHistoryRecords([]);
    setError(null);
    setLoading(false);
  }, []);

  return {
    historyRecords,
    loading,
    error,
    loadHistory,
    deleteHistory,
    loadAllHistories,
    resetHistory,
    // 便利属性
    hasHistory: historyRecords.length > 0,
    latestRecord: historyRecords[0] || null,
  };
};
