import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import LogsPanel from './components/LogsPanel';
import ResultViewer from './components/ResultViewer';
import ScriptForm from './components/ScriptForm';
import { Sidebar } from './components/Sidebar';
import Topbar from './components/Topbar';
import { useAnalysisApi } from './hooks/useAnalysisApi';
import { useRunScriptStream } from './hooks/useRunScriptStream';

const App: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const {
    data: strategies,
    loading: loadingStrategies,
    error: errorStrategies,
  } = useAnalysisApi();
  const [selectedScript, setSelectedScript] = useState<any>(null);
  const { start, stop, logs, running, error, result } = useRunScriptStream();

  const [elapsedMs, setElapsedMs] = useState(0);

  useEffect(() => {
    // 1) 若用户有保存的语言 → 直接用
    const savedLang = localStorage.getItem('preferredLang');

    const supported = ['en', 'zh', 'ja'];
    if (savedLang && supported.includes(savedLang)) {
      i18n.changeLanguage(savedLang);
      return;
    }

    // 2) 否则根据浏览器语言推断
    const userLang = navigator.language.split('-')[0];
    const defaultLang = supported.includes(userLang) ? userLang : 'en';
    i18n.changeLanguage(defaultLang);
  }, [i18n]);

  useEffect(() => {
    if (!running) return;
    const startAt = performance.now();
    const id = window.setInterval(() => {
      setElapsedMs(Math.round(performance.now() - startAt));
    }, 100);
    return () => {
      window.clearInterval(id);
    };
  }, [running]);

  const handlescriptSelect = (script: any) => {
    setSelectedScript(script);
  };

  // ✅ 启动 SSE 流（替换原来的 runscript POST）
  const handleFormSubmit = async (data: any) => {
    // 重置计时
    setElapsedMs(0);

    start({
      scriptPath: data?.script_name,
      folder: data?.folder,
      lang: i18n.language,
      payload: data?.params,
    });
  };

  const formatElapsed = (ms: number) => {
    const totalSec = ms / 1000;
    const m = Math.floor(totalSec / 60);
    const s = totalSec - m * 60;
    return m > 0 ? `${m}m${s.toFixed(2)}s` : `${s.toFixed(2)}s`;
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
      <div className="flex-1 flex flex-col min-h-[700px] max-h-screen overflow-hidden">
        {/* Topbar */}
        <Topbar
          onUserClick={() => alert('User clicked')}
          onscriptSwitch={() => setIsSidebarOpen(!isSidebarOpen)}
        />

        {/* Content Area → 现在作为共同滚动容器 */}
        <div className="flex-1 min-h-0 overflow-y-auto bg-gray-100">
          {/* 统一宽度与内边距，两个区域放一起 */}
          <div className="max-w-[1500px] mx-auto w-full p-4 flex flex-col gap-4 items-center">
            {/* Script Form */}
            <div className="w-full">
              <ScriptForm
                selectedScript={selectedScript}
                onSubmit={handleFormSubmit}
                loading={running}
              />
            </div>

            {/* Result Viewer */}
            <div className="w-full min-w-0">
              <p className="text-gray-500 w-100">
                {t('common.elapsedTime')}: {formatElapsed(elapsedMs)}
              </p>

              {running ? (
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
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                    />
                  </svg>
                  <p>{t('common.loading')}</p>
                  <button
                    className="ml-4 px-3 py-1 border rounded"
                    onClick={stop}
                  >
                    Stop
                  </button>
                </div>
              ) : null}

              {/* ✅ Logs 移到这里，贴着“分析中/Stop”下面 */}
              <div className="mt-3">
                <LogsPanel logs={logs} running={running} />
              </div>

              {/* 结果/错误 */}
              {error ? (
                <p className="text-red-500 mt-3">
                  {t('common.error')}: {error}
                </p>
              ) : (
                <div className="mt-3">
                  <ResultViewer response={result} />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
