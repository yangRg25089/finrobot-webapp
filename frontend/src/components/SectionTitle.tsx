import React from 'react';

interface SectionTitleProps {
  children: React.ReactNode;
  className?: string;
  level?: 'h1' | 'h2' | 'h3';
}

/**
 * 统一的章节标题组件
 * 提供一致的标题样式：粗体大字
 */
export const SectionTitle: React.FC<SectionTitleProps> = ({
  children,
  className = '',
  level = 'h2',
}) => {
  const baseClasses = 'text-gray-800 font-bold text-lg';
  const combinedClasses = `${baseClasses} ${className}`.trim();

  switch (level) {
    case 'h1':
      return <h1 className={combinedClasses}>{children}</h1>;
    case 'h2':
      return <h2 className={combinedClasses}>{children}</h2>;
    case 'h3':
      return <h3 className={combinedClasses}>{children}</h3>;
    default:
      return <h2 className={combinedClasses}>{children}</h2>;
  }
};
