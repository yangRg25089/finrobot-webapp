import { useEffect, useState } from 'react';

export interface TutorialScript {
  script_name: string;
  folder: string;
  params: Record<string, any>;
}

export const useAnalysisApi = () => {
  const [data, setData] = useState<TutorialScript[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const base =
          (import.meta as any).env?.VITE_API_BASE_URL ??
          'http://localhost:8000';
        const res = await fetch(`${base}/api/tutorial-scripts`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        setData(json.tutorials_wrapper ?? []);
      } catch (e: any) {
        setError(e.message || 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return { data, loading, error };
};
