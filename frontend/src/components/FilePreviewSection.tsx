import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { buildStaticUrl } from '../config/api';

interface FilePreviewSectionProps {
  generatedFiles: any[];
}

const PdfPreview: React.FC<{ src: string; title: string }> = ({
  src,
  title,
}) => {
  return (
    <div className="mt-3">
      <iframe
        src={src}
        className="w-full h-[1200px] border rounded"
        title={title}
        loading="lazy"
      />
    </div>
  );
};

const FilePreviewSection: React.FC<FilePreviewSectionProps> = ({
  generatedFiles,
}) => {
  const [textContents, setTextContents] = useState<Record<number, string>>({});
  const [txtOpen, setTxtOpen] = useState<Record<number, boolean>>({});
  const { t } = useTranslation();

  useEffect(() => {
    generatedFiles.forEach((file, index) => {
      const ext = file.extension?.toLowerCase();
      if (['.txt', '.md'].includes(ext)) {
        fetch(buildStaticUrl(file.url))
          .then((res) => res.text())
          .then((content) => {
            setTextContents((prev) => ({ ...prev, [index]: content }));
          })
          .catch(() => {
            setTextContents((prev) => ({
              ...prev,
              [index]: 'Failed to load content',
            }));
          });
      }
    });
  }, [generatedFiles]);

  const toggleTxt = (index: number) => {
    setTxtOpen((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  const renderFilePreview = (file: any, index: number) => {
    const extension = file.extension?.toLowerCase();

    if (
      ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'].includes(extension)
    ) {
      return (
        <div className="mt-3">
          <img
            src={buildStaticUrl(file.url)}
            alt={file.name}
            className="max-w-full h-auto rounded border"
            loading="lazy"
          />
        </div>
      );
    }

    if (extension === '.pdf') {
      return <PdfPreview src={buildStaticUrl(file.url)} title={file.name} />;
    }

    if (extension === '.md') {
      return (
        <div className="mt-3 p-4 bg-gray-50 rounded border prose prose-sm max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {textContents[index] || 'Loading...'}
          </ReactMarkdown>
        </div>
      );
    }

    if (extension === '.txt') {
      const open = !!txtOpen[index];
      return (
        <>
          {open && (
            <div className="mt-2 p-4 bg-gray-50 rounded border">
              <pre className="text-sm whitespace-pre-wrap font-mono">
                {textContents[index] || 'Loading...'}
              </pre>
            </div>
          )}
        </>
      );
    }

    return null;
  };

  const allFiles = [...generatedFiles];
  if (allFiles.length === 0) return null;

  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold mb-3 text-gray-800">
        {t('common.generatedFiles')} ({allFiles.length})
      </h3>
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="space-y-4">
          {allFiles.map((file: any, idx: number) => {
            const extension = file.extension?.toLowerCase();
            const isPreviewable = [
              '.pdf',
              '.png',
              '.jpg',
              '.jpeg',
              '.gif',
              '.webp',
              '.svg',
              '.txt',
              '.md',
            ].includes(extension);
            const isTxt = extension === '.txt';

            return (
              <div key={idx} className="bg-white rounded border">
                {/* 头部：文件信息 + toggle按钮 */}
                <div className="flex items-center justify-between p-3">
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <div className="flex-shrink-0">
                      {extension === '.pdf' && (
                        <span className="text-red-500 text-xl">📄</span>
                      )}
                      {[
                        '.png',
                        '.jpg',
                        '.jpeg',
                        '.gif',
                        '.webp',
                        '.svg',
                      ].includes(extension) && (
                        <span className="text-blue-500 text-xl">🖼️</span>
                      )}
                      {['.txt', '.md'].includes(extension) && (
                        <span className="text-gray-500 text-xl">📝</span>
                      )}
                      {!isPreviewable && (
                        <span className="text-gray-400 text-xl">📁</span>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        <a
                          href={buildStaticUrl(file.url)}
                          target="_blank"
                          rel="noreferrer"
                          className="hover:underline"
                          title={file.name}
                        >
                          {file.name}
                        </a>
                      </p>
                      {!file.isImageOnly && (
                        <p className="text-xs text-gray-500">
                          {file.size_human} •{' '}
                          {new Date(file.modified_time).toLocaleString()}
                        </p>
                      )}
                    </div>
                  </div>
                  {/* Toggle按钮在最右侧 */}
                  {isTxt && (
                    <button
                      onClick={() => toggleTxt(idx)}
                      className="inline-flex items-center px-2 py-1 text-base text-gray-700 hover:bg-gray-100 rounded"
                      title={
                        txtOpen[idx]
                          ? t('common.collapse') || 'Collapse'
                          : t('common.expand') || 'Expand'
                      }
                    >
                      {txtOpen[idx] ? '▲' : '▼'}
                    </button>
                  )}
                </div>
                {/* 预览内容 */}
                {isPreviewable && renderFilePreview(file, idx)}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default FilePreviewSection;
