import { useEffect, useState } from 'react';
import { API_ENDPOINTS, buildApiUrl } from '../config/api';

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
        const url = buildApiUrl(API_ENDPOINTS.models);
        const res = await fetch(url);
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
