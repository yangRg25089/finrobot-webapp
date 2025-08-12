import React, { useState } from 'react';

interface TagInputProps {
  value: string[];
  onChange: (v: string[]) => void;
  placeholder?: string;
  disabled?: boolean;
  ariaLabel?: string;
}

export const TagInput: React.FC<TagInputProps> = ({
  value,
  onChange,
  placeholder = 'Press Enter or comma to add',
  disabled = false,
  ariaLabel = 'Tag input',
}) => {
  const [input, setInput] = useState('');

  const addMany = (raw: string) => {
    const parts = raw
      .split(/[,|\n]/) // 逗号或换行均可
      .map((s) => s.trim())
      .filter(Boolean);
    if (!parts.length) return;
    const next = Array.from(new Set([...value, ...parts]));
    onChange(next);
  };

  const commit = () => {
    if (!input.trim()) return;
    addMany(input);
    setInput('');
  };

  const removeAt = (idx: number) => {
    const next = value.filter((_, i) => i !== idx);
    onChange(next);
  };

  return (
    <div className="flex-1">
      {/* 标签区（独立盒子） */}
      <div
        className="min-h-3 rounded p-1 flex flex-wrap gap-1 overflow-auto"
        aria-label="Tags"
        role="list"
      >
        {value.length === 0 ? (
          <span className="text-gray-400 text-sm">No tags</span>
        ) : (
          value.map((tag, idx) => (
            <span
              key={`${tag}-${idx}`}
              role="listitem"
              className="px-2 py-1 text-sm bg-white rounded-full border flex items-center"
            >
              {tag}
              <button
                type="button"
                className="ml-2 text-gray-500 hover:text-gray-700"
                onClick={() => removeAt(idx)}
                aria-label={`Remove ${tag}`}
                title="Remove"
                disabled={disabled}
              >
                ×
              </button>
            </span>
          ))
        )}
      </div>

      {/* 输入框（单独一行） */}
      <input
        className="mt-2 w-full p-2 border rounded outline-none disabled:bg-gray-100"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            commit();
          } else if (e.key === 'Backspace' && !input && value.length) {
            // 输入为空时，Backspace 删除最后一个标签
            onChange(value.slice(0, -1));
          }
        }}
        onBlur={() => {
          // 失焦也可提交一次（可按需去掉）
          if (input.trim()) commit();
        }}
        onPaste={(e) => {
          const text = e.clipboardData.getData('text');
          if (text && /[,|\n]/.test(text)) {
            e.preventDefault();
            addMany(text);
          }
        }}
        placeholder={placeholder}
        aria-label={ariaLabel}
        disabled={disabled}
      />
    </div>
  );
};
