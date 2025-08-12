import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { buildStaticUrl } from '../config/api';
import { HistoryRecord } from '../hooks/useHistoryApi';
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

  // 当脚本名称变化时，立即清空当前响应，避免显示上一个脚本的内容
  useEffect(() => {
    setCurrentResponse(null);
  }, [scriptName]);

  // 当 response 变化时更新当前响应（但不在脚本切换时）
  useEffect(() => {
    if (response) {
      setCurrentResponse(response);
    }
  }, [response]);

  const handleHistorySelect = (selectedRecord: HistoryRecord | null) => {
    if (selectedRecord === null) {
      // 选择了 "当前结果"
      setCurrentResponse(response || null);
    } else {
      // 选择了历史记录，将其转换为 response 格式
      const historyResponse = {
        result: selectedRecord.messages || [],
        result_images: [],
        generated_files: { files: [] },
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

  // 使用当前响应数据
  const displayResponse = currentResponse || response;

  // 如果没有当前结果，显示空状态
  if (!displayResponse?.result?.length) {
    return (
      <>
        <HistorySelector
          scriptName={scriptName}
          onHistorySelect={handleHistorySelect}
          currentResponse={response}
          running={running}
        />
        {!displayResponse && (
          <p className="text-gray-500">{t('common.noChart')}</p>
        )}
      </>
    );
  }

  const images: string[] = Array.isArray(displayResponse?.result_images)
    ? displayResponse.result_images
    : [];

  const generatedFiles = displayResponse?.generated_files?.files || [];

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
        {displayResponse?.isHistoryRecord
          ? t('common.historyResult')
          : t('common.summary')}
        :
      </SectionTitle>
      {displayResponse?.result &&
        Array.isArray(displayResponse.result) &&
        displayResponse.result
          .filter((item: any) => hasContent(item?.content))
          .map((item: any, idx: number) => (
            <div key={idx} className="p-4 bg-white shadow rounded mb-4 min-w-0">
              <h2 className="text-gray-800 font-bold">{item.name ?? ''}:</h2>

              {/* 容器：横向可滚动、宽度不超父级 */}
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
                        <pre className="w-full overflow-x-auto" {...props} />
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
            </div>
          ))}

      {/* 显示生成的图片 */}
      {images.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3 text-gray-800">
            {t('common.generatedImages')}
          </h3>
          <div className="gap-3">
            {images.map((url) => (
              <a
                key={url}
                href={buildStaticUrl(url)}
                target="_blank"
                rel="noreferrer"
                className="block w-full mb-3"
              >
                <img
                  src={buildStaticUrl(url)}
                  alt="result"
                  className="w-full h-auto rounded border block"
                  loading="lazy"
                />
              </a>
            ))}
          </div>
        </div>
      )}

      {/* 显示生成的文件列表 */}
      {generatedFiles.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3 text-gray-800">
            {t('common.generatedFiles')} ({generatedFiles.length})
          </h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="space-y-2">
              {generatedFiles.map((file: any, idx: number) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 bg-white rounded border hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <div className="flex-shrink-0">
                      {file.extension === '.pdf' && (
                        <span className="text-red-500 text-xl">📄</span>
                      )}
                      {[
                        '.png',
                        '.jpg',
                        '.jpeg',
                        '.gif',
                        '.webp',
                        '.svg',
                      ].includes(file.extension) && (
                        <span className="text-blue-500 text-xl">🖼️</span>
                      )}
                      {['.txt', '.md'].includes(file.extension) && (
                        <span className="text-gray-500 text-xl">📝</span>
                      )}
                      {![
                        '.pdf',
                        '.png',
                        '.jpg',
                        '.jpeg',
                        '.gif',
                        '.webp',
                        '.svg',
                        '.txt',
                        '.md',
                      ].includes(file.extension) && (
                        <span className="text-gray-400 text-xl">📁</span>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {file.size_human} •{' '}
                        {new Date(file.modified_time).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <a
                      href={buildStaticUrl(file.url)}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      {t('common.download')}
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* PDF 预览 */}
      {displayResponse?.preview && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3 text-gray-800">
            {t('common.pdfPreview')}
          </h3>
          <div className="border rounded-lg p-4 bg-white">
            <img
              src={`data:image/png;base64,${displayResponse.preview}`}
              alt="PDF Preview"
              className="w-full h-auto rounded border"
              loading="lazy"
            />
          </div>
        </div>
      )}
    </>
  );
};

export default ResultViewer;
