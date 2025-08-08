import React, { useEffect, useRef, useState } from 'react';

export interface LogItem {
  type: 'stdout' | 'stderr';
  text: string;
}

interface LogsPanelProps {
  logs: LogItem[];
  running: boolean;
  maxLines?: number; // 默认 2000
}

const LogsPanel: React.FC<LogsPanelProps> = ({
  logs,
  running,
  maxLines = 2000,
}) => {
  const [open, setOpen] = useState(true);
  const [follow, setFollow] = useState(true);
  const ref = useRef<HTMLDivElement>(null);

  // 限制行数，避免超长
  const view = logs.length > maxLines ? logs.slice(-maxLines) : logs;

  // 自动滚动到底部
  useEffect(() => {
    if (!follow) return;
    const el = ref.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [view, follow]);

  // ✅ 有新内容时自动打开
  const prevCountRef = useRef(logs.length);
  useEffect(() => {
    if (logs.length > prevCountRef.current) {
      setOpen(true); // 自动打开
      prevCountRef.current = logs.length;
    }
  }, [logs]);

  // 跑完后默认收起
  useEffect(() => {
    if (!running) setOpen(false);
  }, [running]);

  return (
    <div className="w-full">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Logs {running ? '(running...)' : ''}</h3>
        <div className="flex items-center gap-2">
          <label className="text-sm cursor-pointer">
            <input
              type="checkbox"
              className="mr-1 align-middle"
              checked={follow}
              onChange={(e) => setFollow(e.target.checked)}
            />
            Follow
          </label>
          <button
            className="px-2 py-1 border rounded text-sm"
            onClick={() => setOpen((o) => !o)}
          >
            {open ? 'Hide' : 'Show'}
          </button>
        </div>
      </div>

      {open && (
        <div
          ref={ref}
          className="border rounded p-2 h-64 overflow-auto font-mono text-sm bg-black text-green-300 mt-2"
        >
          {view.map((l, i) => (
            <div key={i} className={l.type === 'stderr' ? 'text-red-400' : ''}>
              {l.text}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LogsPanel;
