import React from 'react';
import { useTranslation } from 'react-i18next';
import analysis from '../config/analysis.json';

interface SidebarProps {
  isOpen: boolean;
  onscriptSelect: (script: { script_name: string; folder: string; params: any }) => void;
  selectedScript: { script_name: string; folder: string; params: any } | null;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onscriptSelect, selectedScript }) => {
  const { t } = useTranslation();
  const strategies = analysis.tutorials_wrapper;

  return (
    <div className={`w-64 bg-gray-800 text-white h-screen transition-all ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="p-4">
        <h2 className="text-xl font-bold mb-4">{t('common.strategies')}</h2>
        <ul>
          {strategies.map((script) => (
            <li
              key={script.script_name}
              className={`cursor-pointer p-2 hover:bg-gray-700 rounded ${selectedScript?.script_name === script.script_name ? 'bg-gray-700' : ''}`}
              onClick={() => onscriptSelect(script)}
            >
              {t(script.script_name)}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
