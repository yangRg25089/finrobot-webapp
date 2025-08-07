import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import ResultViewer from './components/ResultViewer';
import ScriptForm from './components/ScriptForm';
import { Sidebar } from './components/Sidebar';
import Topbar from './components/Topbar';
import { useAnalysisApi } from './hooks/useAnalysisApi';
import { useScriptApi } from './hooks/useScriptApi';

const App: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const {
    data: strategies,
    loading: loadingStrategies,
    error: errorStrategies,
  } = useAnalysisApi();
  const [selectedScript, setSelectedScript] = useState<any>(null);

  const [result, setResult] = useState<any>(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const { runscript, loading, error } = useScriptApi();

  useEffect(() => {
    // Set default language based on user agent
    const userLangFull = navigator.language;
    const userLang = userLangFull.split('-')[0];
    const supportedLanguages = ['en', 'zh', 'ja'];
    const defaultLang = supportedLanguages.includes(userLang) ? userLang : 'en';
    i18n.changeLanguage(defaultLang);
  }, [i18n]);

  useEffect(() => {
    if (!loading) return;

    const start = performance.now();
    const id = window.setInterval(() => {
      setElapsedMs(Math.round(performance.now() - start));
    }, 100);

    return () => window.clearInterval(id);
  }, [loading]);

  const handlescriptSelect = (script: any) => {
    setSelectedScript(script);
  };

  const handleFormSubmit = async (data: any) => {
    const result = await runscript(data, i18n.language);
    if (result) {
      setResult(result);
    }
  };

  useEffect(() => {
    if (!selectedScript && strategies.length) {
      setSelectedScript(strategies[0]);
    }
  }, [strategies, selectedScript]);

  if (loadingStrategies) {
    return <p className="p-6">{t('common.loading')}</p>;
  }
  if (errorStrategies) {
    return <p className="p-6 text-red-500">{errorStrategies}</p>;
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      {isSidebarOpen && (
        <Sidebar
          isOpen={isSidebarOpen}
          strategies={strategies}
          onscriptSelect={handlescriptSelect}
          selectedScript={selectedScript}
        />
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Topbar */}
        <Topbar
          onUserClick={() => alert('User clicked')}
          onscriptSwitch={() => setIsSidebarOpen(!isSidebarOpen)}
        />

        {/* Content Area */}
        <div className="flex-1 flex flex-col p-4 gap-4 bg-gray-100 items-center">
          {/* Script Form */}
          <div>
            <ScriptForm
              selectedScript={selectedScript}
              onSubmit={handleFormSubmit}
              loading={loading} // ← 传给表单，提交时禁用按钮
            />
          </div>

          {/* Result Viewer */}
          <div className="flex-1 flex flex-col overflow-y-auto min-w-0">
            <div className="max-w-[1500px] mx-auto w-full">
              <p className="text-gray-500 w-100">
                {t('common.elapsedTime')}: {(elapsedMs / 1000).toFixed(2)}s
              </p>
              {loading ? (
                <div className="flex items-center justify-center">
                  <svg
                    className="animate-spin h-5 w-5 mr-3 text-gray-500"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                    ></path>
                  </svg>
                  <p>{t('common.loading')}</p>
                </div>
              ) : error ? (
                <p className="text-red-500">
                  {t('common.error')}: {error}
                </p>
              ) : (
                <ResultViewer response={result} />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
