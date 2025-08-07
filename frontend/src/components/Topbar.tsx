import React from 'react';
import { useTranslation } from 'react-i18next';

interface TopbarProps {
  onUserClick: () => void;
  onscriptSwitch: () => void;
}

const Topbar: React.FC<TopbarProps> = ({ onUserClick, onscriptSwitch }) => {
  const { t, i18n } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('preferredLang', lng);
  };

  return (
    <div className="w-full bg-gray-800 text-white p-4 flex justify-between items-center">
      <button
        className="text-lg font-bold hover:underline"
        onClick={onscriptSwitch}
      >
        {t('common.switchscript')}
      </button>

      <div>
        <select
          className="bg-gray-700 text-white p-2 rounded"
          value={i18n.language}
          onChange={(e) => changeLanguage(e.target.value)}
        >
          <option value="en">{t('common.english')}</option>
          <option value="zh">{t('common.chinese')}</option>
          <option value="ja">{t('common.japanese')}</option>
        </select>
      </div>
    </div>
  );
};

export default Topbar;
