import React, { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { HistoryRecord, useHistoryApi } from '../hooks/useHistoryApi';
import { SectionTitle } from './SectionTitle';

interface HistorySelectorProps {
  scriptName?: string;
  onHistorySelect: (record: HistoryRecord | null) => void;
  currentResponse?: any;
  running?: boolean;
}

export const HistorySelector: React.FC<HistorySelectorProps> = ({
  scriptName,
  onHistorySelect,
  currentResponse,
  running = false,
}) => {
  const { t } = useTranslation();
  const { historyRecords, loading, hasHistory, deleteHistory, loadHistory } =
    useHistoryApi(scriptName);
  const [selectedHistoryId, setSelectedHistoryId] = useState<string>('');
  const [isDeleting, setIsDeleting] = useState(false);
  const isInitializedRef = useRef(false);

  // 当历史记录加载完成时，默认选中第一个
  useEffect(() => {
    // 加载或变更后，若有历史记录则默认选中最新一条（通常为当天）
    if (!isInitializedRef.current && historyRecords.length > 0) {
      const firstRecord = historyRecords[0];
      setSelectedHistoryId(firstRecord.id);
      onHistorySelect(firstRecord);
      isInitializedRef.current = true;
    }

    // 如果当前选中的记录不存在了（比如被删除了），选择第一个可用的记录
    if (
      selectedHistoryId &&
      historyRecords.length > 0 &&
      !historyRecords.find((r) => r.id === selectedHistoryId) &&
      !currentResponse?.result?.length
    ) {
      const firstRecord = historyRecords[0];
      setSelectedHistoryId(firstRecord.id);
      onHistorySelect(firstRecord);
    }
  }, [historyRecords, currentResponse, selectedHistoryId]);

  // 当脚本名称变化时，重置选择状态
  useEffect(() => {
    setSelectedHistoryId('');
    isInitializedRef.current = false; // 重置初始化标志
  }, [scriptName]);

  // 运行结束后，刷新历史记录，并让下拉自动选中新产生的最新一条
  useEffect(() => {
    if (!running && scriptName) {
      // 重置初始化标志以便后续 historyRecords 变化时自动选中第一条
      isInitializedRef.current = false;
      // 重新拉取历史列表，包含刚生成的会话
      loadHistory(scriptName);
    }
  }, [running, scriptName, loadHistory]);

  // 当新的结果到达（有 timestamp）时，主动刷新历史列表（避免仅等 running=false）
  useEffect(() => {
    const ts = (currentResponse as any)?.timestamp;
    if (ts && scriptName) {
      isInitializedRef.current = false;
      loadHistory(scriptName);
    }
  }, [currentResponse, scriptName, loadHistory]);

  const handleHistorySelect = (historyId: string) => {
    setSelectedHistoryId(historyId);

    if (historyId === '') {
      onHistorySelect(null);
    } else {
      const selectedRecord = historyRecords.find(
        (record) => record.id === historyId,
      );
      onHistorySelect(selectedRecord || null);
    }
  };

  const handleDeleteHistory = async () => {
    if (!selectedHistoryId || !scriptName) return;

    const selectedRecord = historyRecords.find(
      (record) => record.id === selectedHistoryId,
    );
    if (!selectedRecord) return;

    if (!window.confirm(t('common.confirmDelete'))) {
      return;
    }

    setIsDeleting(true);
    try {
      const success = await deleteHistory(scriptName, selectedRecord.timestamp);
      if (success) {
        // 删除成功，重置选择状态并重置初始化标志
        setSelectedHistoryId('');
        onHistorySelect(null);
        isInitializedRef.current = false; // 重置初始化标志，让新的历史记录列表能够自动选择第一个
        // 重新加载历史记录，确保下拉与内容同步
        await loadHistory(scriptName);
        console.log(t('common.deleteSuccess'));
      } else {
        // 删除失败
        console.error(t('common.deleteFailed'));
        alert(t('common.deleteFailed'));
      }
    } catch (error) {
      console.error('Delete history error:', error);
      alert(t('common.deleteFailed'));
    } finally {
      setIsDeleting(false);
    }
  };

  // 如果没有历史记录或正在运行，不显示组件
  if (!hasHistory || running) {
    return null;
  }

  return (
    <>
      <SectionTitle>{t('common.conversationHistory')}:</SectionTitle>
      <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
        <div className="flex items-center space-x-4">
          <select
            id="history-select"
            value={selectedHistoryId}
            onChange={(e) => handleHistorySelect(e.target.value)}
            className="flex-1 max-w-md px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={loading}
          >
            {historyRecords.map((record) => (
              <option key={record.id} value={record.id}>
                {record.display_name}
              </option>
            ))}
          </select>
          {selectedHistoryId && (
            <button
              onClick={handleDeleteHistory}
              disabled={isDeleting}
              className="px-2 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              title={t('common.deleteHistory')}
            >
              {isDeleting ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              )}
            </button>
          )}
        </div>

        {/* 显示选中历史记录的提示信息 */}
        {selectedHistoryId && (
          <div className="mt-2 text-xs text-gray-600">
            {(() => {
              const selectedRecord = historyRecords.find(
                (r) => r.id === selectedHistoryId,
              );
              return selectedRecord ? (
                <div>
                  <span className="font-medium">{t('common.hint')}:</span>{' '}
                  {selectedRecord.prompt?.substring(0, 100)}
                  {selectedRecord.prompt &&
                    selectedRecord.prompt.length > 100 &&
                    '...'}
                </div>
              ) : null;
            })()}
          </div>
        )}
      </div>
    </>
  );
};
