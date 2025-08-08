import React, { useEffect, useRef, useState } from 'react';

export interface LogItem {
  type: 'stdout' | 'stderr';
  text: string;
}

interface LogsPanelProps {
  logs: LogItem[];
  running: boolean;
  maxLines?: number; // 默认 2000
  runKey?: string | number; // 每次新执行任务传一个新值
}

const LogsPanel: React.FC<LogsPanelProps> = ({
  logs,
  running,
  maxLines = 2000,
  runKey,
}) => {
  const [open, setOpen] = useState(true);
  const [follow, setFollow] = useState(true);
  const ref = useRef<HTMLDivElement>(null);
  const prevCountRef = useRef(logs.length);

  // 限制行数，避免超长
  const view = logs.length > maxLines ? logs.slice(-maxLines) : logs;

  // 自动滚动到底部
  useEffect(() => {
    if (!follow) return;
    const el = ref.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [view, follow]);

  // 新任务开始：重置计数 + 自动展开 + 开启 Follow
  useEffect(() => {
    if (runKey !== undefined) {
      prevCountRef.current = logs.length;
      setOpen(true);
      setFollow(true);
    }
  }, [runKey]);

  // 日志变化：长度减少 → 被清空/替换（任务切换时也可能出现）
  //          长度增加 → 有新内容 → 自动展开
  useEffect(() => {
    const prev = prevCountRef.current;
    const curr = logs.length;

    if (curr < prev) {
      // 被清空/替换
      prevCountRef.current = curr;
      return;
    }

    if (curr > prev) {
      setOpen(true);
      prevCountRef.current = curr;
    }
  }, [logs.length]);

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
          className="border rounded p-2 h-[32rem] overflow-auto font-mono text-sm bg-black text-green-300 mt-2"
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
