import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { HistoryRecord } from '../hooks/useHistoryApi';
import FilePreviewSection from './FilePreviewSection';
import { HistorySelector } from './HistorySelector';
import { SectionTitle } from './SectionTitle';

interface ResultViewerProps {
  response: any;
  scriptName?: string;
  running?: boolean;
}

const ResultViewer: React.FC<ResultViewerProps> = ({
  response,
  scriptName,
  running = false,
}) => {
  const { t } = useTranslation();
  const [currentResponse, setCurrentResponse] = useState(response);
  const [collapsedMessages, setCollapsedMessages] = useState<
    Record<number, boolean>
  >({});

  useEffect(() => {
    if (running) {
      setCurrentResponse(null);
    }
  }, [running]);

  // 当 response 变化时更新当前响应（但不在脚本切换时）
  useEffect(() => {
    if (response) {
      setCurrentResponse(response);
    }
  }, [response]);

  const toggleMessageCollapse = (index: number) => {
    setCollapsedMessages((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  useEffect(() => {
    if (currentResponse?.result && Array.isArray(currentResponse.result)) {
      const initialCollapsedState: Record<number, boolean> = {};

      const visibleItems = currentResponse.result.filter((item: any) =>
        hasContent(item?.content),
      );

      visibleItems.forEach((item: any, idx: number) => {
        initialCollapsedState[idx] = item.role === 'assistant' ? false : true;
      });

      if (visibleItems.length > 0) {
        initialCollapsedState[visibleItems.length - 1] = false;
      }

      setCollapsedMessages(initialCollapsedState);
    }
  }, [currentResponse]);

  const handleHistorySelect = (selectedRecord: HistoryRecord | null) => {
    if (selectedRecord === null) {
      // 选择了 "当前结果"
      setCurrentResponse(response || null);
    } else {
      // 选择了历史记录，将其转换为 response 格式（包含历史中的文件信息）
      const historyResponse = {
        result: selectedRecord.messages || [],
        generated_files: selectedRecord.generated_files || { files: [] },
        timestamp: selectedRecord.timestamp,
        prompt: selectedRecord.prompt,
        isHistoryRecord: true,
      };
      setCurrentResponse(historyResponse);
    }
  };

  const hasContent = (val: unknown): boolean => {
    if (val == null) return false;
    if (typeof val === 'string') return val.trim().length > 0;
    if (Array.isArray(val)) return val.some((v) => hasContent(v));
    if (typeof val === 'object') {
      const anyVal = val as any;
      return hasContent(anyVal.text ?? anyVal.content ?? '');
    }
    return true;
  };

  // 如果没有当前结果，显示空状态
  if (!currentResponse?.result?.length) {
    return (
      <>
        <HistorySelector
          scriptName={scriptName}
          onHistorySelect={handleHistorySelect}
          currentResponse={response}
          running={running}
        />
        {!currentResponse && (
          <p className="text-gray-500">{t('common.noChart')}</p>
        )}
      </>
    );
  }

  const generatedFiles = currentResponse?.generated_files?.files || [];

  return (
    <>
      {/* 历史记录选择器 */}
      <HistorySelector
        scriptName={scriptName}
        onHistorySelect={handleHistorySelect}
        currentResponse={response}
        running={running}
      />

      <SectionTitle>
        {currentResponse?.isHistoryRecord
          ? t('common.historyResult')
          : t('common.summary')}
        :
      </SectionTitle>
      {currentResponse?.result &&
        Array.isArray(currentResponse.result) &&
        currentResponse.result
          .filter((item: any) => hasContent(item?.content))
          .map((item: any, idx: number) => {
            const isCollapsed = collapsedMessages[idx];

            return (
              <div
                key={idx}
                className="p-4 bg-white shadow rounded mb-4 min-w-0"
              >
                <div className="flex items-center justify-between">
                  <h2 className="text-gray-800 font-bold">
                    {item.name ?? ''}
                    {item.role && (
                      <span className="ml-2 text-sm font-normal text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {item.role}
                      </span>
                    )}
                    :
                  </h2>
                  <button
                    onClick={() => toggleMessageCollapse(idx)}
                    className="inline-flex items-center px-2 py-1 text-base text-gray-700 hover:bg-gray-100 rounded"
                    title={
                      isCollapsed
                        ? t('common.expand') || 'Expand'
                        : t('common.collapse') || 'Collapse'
                    }
                  >
                    {isCollapsed ? '▼' : '▲'}
                  </button>
                </div>

                {/* 只有未折叠时才显示内容 */}
                {!isCollapsed && (
                  <div className="overflow-x-auto max-w-full">
                    <div className="prose prose-slate dark:prose-invert max-w-none w-full break-words">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          /* 表格：跟随容器宽度，允许内部自动布局 */
                          table: ({ node, ...props }) => (
                            <table className="w-full table-auto" {...props} />
                          ),
                          /* 代码块：局部横向滚动 */
                          pre: ({ node, ...props }) => (
                            <pre
                              className="w-full overflow-x-auto"
                              {...props}
                            />
                          ),
                          /* 图片：不超容器 */
                          img: ({ node, ...props }) => (
                            <img className="max-w-full h-auto" {...props} />
                          ),
                        }}
                      >
                        {typeof item.content === 'string'
                          ? item.content
                          : (item.content?.text ?? item.content?.content ?? '')}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            );
          })}

      {/* 显示生成的文件列表（包含预览功能） */}
      {generatedFiles.length > 0 && (
        <FilePreviewSection generatedFiles={generatedFiles} />
      )}
    </>
  );
};

export default ResultViewer;
