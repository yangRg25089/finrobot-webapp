import React from 'react';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';


interface ResultViewerProps {
  response: any; // Updated to accept the full response object
}

const ResultViewer: React.FC<ResultViewerProps> = ({ response }) => {
  const { t } = useTranslation();

  const hasContent = (val: unknown): boolean => {
    if (val == null) return false;
    if (typeof val === "string") return val.trim().length > 0;
    if (Array.isArray(val)) return val.some(v => hasContent(v));
    if (typeof val === "object") {
      const anyVal = val as any;
      // 兼容 {text: "..."} 或 {content: "..."}
      return hasContent(anyVal.text ?? anyVal.content ?? "");
    }
    return true; // 其它类型一律认为有内容
  };

  if (!response || !response.result || response.result.length === 0) {
    return <p className="text-gray-500">{t('common.noChart')}</p>;
  }

  return (
  <>
    {(response?.result ?? [])
      .filter((item: any) => hasContent(item?.content))
      .map((item: any, index: number) => (
        <div key={index} className="p-4 bg-white shadow rounded mb-4">
          <h2 className="text-gray-800 font-bold">{t("common.summary")}:</h2>
          <div className="overflow-x-auto max-w-full">
            <div className="prose prose-slate dark:prose-invert max-w-none w-full break-words">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {typeof item.content === "string"
                  ? item.content
                  : item.content?.text ?? item.content?.content ?? ""}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      ))}
  </>
);
};

export default ResultViewer;
