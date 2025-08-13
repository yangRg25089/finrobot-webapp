import React from 'react';
import { useTranslation } from 'react-i18next';
import { TutorialScript } from '../hooks/useAnalysisApi';

interface SidebarProps {
  isOpen: boolean;
  strategies: TutorialScript[];
  onscriptSelect: (s: TutorialScript) => void;
  selectedScript: TutorialScript | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  strategies,
  onscriptSelect,
  selectedScript,
}) => {
  const { t } = useTranslation();

  // 1) 先按 folder 分组
  const groups = React.useMemo(() => {
    const map = new Map<string, TutorialScript[]>();
    for (const s of strategies) {
      if (!map.has(s.folder)) map.set(s.folder, []);
      map.get(s.folder)!.push(s);
    }
    // （可选）分组内按脚本名排序，便于浏览
    for (const [k, arr] of map) {
      arr.sort((a, b) => a.script_name.localeCompare(b.script_name));
      map.set(k, arr);
    }
    return map;
  }, [strategies]);

  // 2) 折叠状态：默认全部闭合
  const [openFolders, setOpenFolders] = React.useState<Record<string, boolean>>(
    {},
  );

  // 3) 当选中脚本变化时，自动展开该脚本所在的一级目录
  React.useEffect(() => {
    if (selectedScript?.folder) {
      setOpenFolders((prev) => ({ ...prev, [selectedScript.folder]: true }));
    }
  }, [selectedScript?.folder]);

  const toggleFolder = (folder: string) => {
    setOpenFolders((prev) => ({ ...prev, [folder]: !prev[folder] }));
  };

  return (
    <div
      className={`w-80 bg-gray-800 text-white h-screen transition-all ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      <div className="p-4">
        <h2 className="text-xl font-bold mb-4">{t('common.strategies')}</h2>

        {/* 2 级目录：一级=folder，二级=该组下脚本 */}
        <ul className="space-y-2">
          {Array.from(groups.entries()).map(([folder, items]) => {
            const isOpenFolder = !!openFolders[folder];
            return (
              <li key={folder} className="rounded">
                {/* 一级目录行 */}
                <button
                  type="button"
                  onClick={() => toggleFolder(folder)}
                  className="w-full flex items-center justify-between px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded"
                >
                  <span className="font-semibold">{folder}</span>
                  <span className="text-sm opacity-80">
                    {isOpenFolder ? '▾' : '▸'}
                  </span>
                </button>

                {/* 二级目录（脚本列表） */}
                {isOpenFolder && (
                  <ul className="mt-2 ml-2 space-y-1">
                    {items.map((s) => {
                      const active =
                        selectedScript?.script_name === s.script_name &&
                        selectedScript?.folder === s.folder;
                      return (
                        <li key={s.script_name}>
                          <button
                            type="button"
                            onClick={() => onscriptSelect(s)}
                            className={`w-full text-left px-3 py-2 rounded hover:bg-gray-700 ${
                              active ? 'bg-gray-700' : ''
                            }`}
                          >
                            {t(s.script_name)}
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
};
