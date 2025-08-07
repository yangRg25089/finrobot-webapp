import { useEffect, useState } from 'react';

export interface ModelInfo {
  model: string;
  base_url?: string;
  api_type?: string;
}

export const useModelList = () => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchModels = async () => {
      setLoading(true);
      try {
        const base =
          (import.meta as any).env?.VITE_API_BASE_URL ??
          'http://localhost:8000';
        const res = await fetch(`${base}/api/models`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        setModels(json as ModelInfo[]);
      } catch (e: any) {
        setError(e.message ?? 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchModels();
  }, []);

  return { models, loading, error };
};
