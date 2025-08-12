/**
 * API 配置管理
 */

// 获取 API Base URL
export const getApiBaseUrl = (): string => {
  return (import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000';
};

// API 端点配置
export const API_ENDPOINTS = {
  // 脚本相关
  scripts: '/api/tutorial-scripts',
  runScript: '/api/run-script',
  models: '/api/models',

  // 历史记录相关
  history: (scriptName: string) => `/api/history/${scriptName}`,
  allHistories: '/api/history',
  deleteHistory: (scriptName: string, timestamp?: string) =>
    timestamp
      ? `/api/history/${scriptName}?timestamp=${timestamp}`
      : `/api/history/${scriptName}`,
} as const;

// 构建完整的 API URL
export const buildApiUrl = (endpoint: string): string => {
  const baseUrl = getApiBaseUrl();
  return `${baseUrl}${endpoint}`;
};

// 便利方法：构建静态资源 URL
export const buildStaticUrl = (path: string): string => {
  const baseUrl = getApiBaseUrl();
  return `${baseUrl}${path}`;
};
