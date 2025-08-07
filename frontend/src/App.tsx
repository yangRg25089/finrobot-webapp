import React, { useState, useEffect } from "react";
import Topbar from "./components/Topbar";
import { Sidebar } from "./components/Sidebar";
import ScriptForm from "./components/ScriptForm";
import ResultViewer from "./components/ResultViewer";
import { useScriptApi } from "./hooks/useScriptApi";
import { useTranslation } from "react-i18next";
import analysis from "./config/analysis.json"; // 导入 analysis 数据

const App: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [selectedScript, setSelectedScript] = useState<any>(analysis.tutorials_wrapper[0]); // Default to the first script
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
    // 刷新频率 50ms 足够流畅，也更省 CPU
    const id = window.setInterval(() => {
      setElapsedMs(Math.round(performance.now() - start));
    }, 50);

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

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      {isSidebarOpen && (
        <Sidebar
          isOpen={isSidebarOpen}
          onscriptSelect={handlescriptSelect}
          selectedScript={selectedScript}
        />
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Topbar */}
        <Topbar
          onUserClick={() => alert("User clicked")}
          onscriptSwitch={() => setIsSidebarOpen(!isSidebarOpen)}
        />

        {/* Content Area */}
        <div className="flex-1 flex p-4 gap-4 bg-gray-100">
          {/* Script Form */}
          <div className="w-1/3">
            <ScriptForm
              selectedScript={selectedScript}
              onSubmit={handleFormSubmit}
              loading={loading}   // ← 传给表单，提交时禁用按钮
            />
          </div>

          {/* Result Viewer */}
          <div className="flex-1">
            <p className="text-gray-500">{t("common.elapsedTime")}: {(elapsedMs / 1000).toFixed(2)}s</p>
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
                <p>{t("common.loading")}</p>
              </div>
            ) : error ? (
              <p className="text-red-500">
                {t("common.error")}: {error}
              </p>
            ) :
             (
              <ResultViewer response={result} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;