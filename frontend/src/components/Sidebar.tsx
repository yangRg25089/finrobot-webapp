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

  return (
    <div
      className={`w-80 bg-gray-800 text-white h-screen transition-all ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}
    >
      <div className="p-4">
        <h2 className="text-xl font-bold mb-4">{t('common.strategies')}</h2>
        <ul>
          {strategies.map((s) => (
            <li
              key={s.script_name}
              className={`cursor-pointer p-2 hover:bg-gray-700 rounded ${
                selectedScript?.script_name === s.script_name
                  ? 'bg-gray-700'
                  : ''
              }`}
              onClick={() => onscriptSelect(s)}
            >
              {t(s.script_name)}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
