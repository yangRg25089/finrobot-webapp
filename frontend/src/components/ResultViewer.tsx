import React from 'react';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ResultViewerProps {
  response: any;
}

const ResultViewer: React.FC<ResultViewerProps> = ({ response }) => {
  const { t } = useTranslation();

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

  if (!response?.result?.length) {
    return <p className="text-gray-500">{t('common.noChart')}</p>;
  }

  return (
    <>
      {response.result
        .filter((item: any) => hasContent(item?.content))
        .map((item: any, idx: number) => (
          <div key={idx} className="p-4 bg-white shadow rounded mb-4 min-w-0">
            <h2 className="text-gray-800 font-bold">
              {t('common.summary')} {idx + 1}:
            </h2>

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
    </>
  );
};

export default ResultViewer;
