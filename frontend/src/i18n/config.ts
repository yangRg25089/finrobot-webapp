import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './translations/en';
import ja from './translations/ja';
import zh from './translations/zh';

const savedLanguage = localStorage.getItem('preferredLanguage') || 'en';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      zh: { translation: zh },
      ja: { translation: ja },
    },
    lng: savedLanguage,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  })
  .then(() => {
    console.log('i18n initialized with language:', savedLanguage);
  });

export default i18n;
