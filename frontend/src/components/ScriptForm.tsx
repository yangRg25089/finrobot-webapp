import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useModelList } from '../hooks/useModelList';
import { TagInput } from './TagInput';

interface ScriptFormProps {
  selectedScript: { script_name: string; folder: string; params: any } | null;
  onSubmit: (data: {
    script_name: string;
    folder: string;
    params: any;
  }) => Promise<void> | void;
  onStop?: () => void;
  running?: boolean;
}

const ScriptForm: React.FC<ScriptFormProps> = ({
  selectedScript,
  onSubmit,
  onStop,
  running = false,
}) => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState<Record<string, any>>({});
  const { models, loading: modelsLoading } = useModelList();

  useEffect(() => {
    if (!selectedScript) {
      setFormData({});
      return;
    }
    const initial: Record<string, any> = {};
    Object.entries(selectedScript.params).forEach(([key, cfg]) => {
      const paramConfig = (cfg as any) || {};
      let def = paramConfig.defaultValue;

      // 容错：如果后端把数组/布尔作为字符串传过来，也尽量解析一下
      if (paramConfig.type === 'boolean') {
        if (typeof def === 'string') def = def.toLowerCase() === 'true';
        if (typeof def !== 'boolean') def = false;
      } else if (paramConfig.type === 'string[]') {
        if (Array.isArray(def)) {
          def = def.map(String);
        } else if (typeof def === 'string') {
          def = def
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean);
        } else {
          def = [];
        }
      }

      if (def === undefined || def === null) def = '';
      initial[key] = def;
    });
    setFormData(initial);
  }, [selectedScript]);

  if (!selectedScript) {
    return <p>{t('common.switchscript')}</p>;
  }

  const handleChange = (key: string, value: any) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit({
      script_name: selectedScript.script_name,
      folder: selectedScript.folder,
      params: formData,
    });
  };

  const scriptDesc = t(`common.descriptions.${selectedScript.script_name}`);

  return (
    <div className="flex gap-8">
      {/* 说明区域 */}
      <div className="w-[33rem] max-w-[33rem] min-w-[320px] bg-blue-50 rounded shadow p-6 flex flex-col">
        <h2 className="text-2xl font-bold text-blue-800">
          {selectedScript.script_name}
        </h2>
        <h3 className="font-bold mb-4 text-blue-800">
          {t('common.scriptIntroTitle')}
        </h3>
        <span className="text-blue-900 text-base">{scriptDesc}</span>
      </div>

      {/* 表单区域 */}
      <form
        onSubmit={handleSubmit}
        className="w-[33rem] max-w-[33rem] min-w-[320px] bg-white rounded shadow p-6 flex flex-col space-y-4"
      >
        <h2 className="text-2xl font-bold mb-4 text-gray-800">
          {t('common.paramTitle')}
        </h2>

        {Object.entries(selectedScript.params).map(([key, cfg]) => {
          const paramConfig = (cfg as any) || {};
          const type = paramConfig.type ?? 'text';
          const isModelKey = key === '_AI_model';

          const label = t(`common.params.${key}`);

          return (
            <div key={key} className="flex items-center mb-3">
              <label
                className="block text-gray-700 mr-2"
                style={{ minWidth: 120, maxWidth: 150, width: 120 }}
              >
                {label}
              </label>

              {isModelKey ? (
                <select
                  value={
                    formData[key] ??
                    paramConfig.defaultValue ??
                    models[0]?.model ??
                    ''
                  }
                  onChange={(e) => handleChange(key, e.target.value)}
                  className="flex-1 p-2 border rounded bg-white"
                  disabled={modelsLoading}
                >
                  {models.map((m) => (
                    <option key={m.model} value={m.model}>
                      {m.model}
                    </option>
                  ))}
                </select>
              ) : type === 'boolean' ? (
                <div className="flex items-center gap-3">
                  <input
                    id={`chk-${key}`}
                    type="checkbox"
                    checked={!!formData[key]}
                    onChange={(e) => handleChange(key, e.target.checked)}
                    className="h-4 w-4"
                  />
                  <label
                    htmlFor={`chk-${key}`}
                    className="text-gray-700 select-none"
                  >
                    {formData[key] ? 'True' : 'False'}
                  </label>
                </div>
              ) : type === 'string[]' ? (
                <TagInput
                  value={Array.isArray(formData[key]) ? formData[key] : []}
                  onChange={(v) => handleChange(key, v)}
                />
              ) : type === 'date' ? (
                <input
                  type="date"
                  value={formData[key] ?? ''}
                  onChange={(e) => handleChange(key, e.target.value)}
                  className="flex-1 p-2 border rounded"
                />
              ) : type === 'number' ? (
                <input
                  type="number"
                  value={formData[key] ?? ''}
                  onChange={(e) => {
                    const v = e.target.value;
                    handleChange(key, v === '' ? '' : Number(v));
                  }}
                  className="flex-1 p-2 border rounded"
                />
              ) : (
                <input
                  type="text"
                  value={formData[key] ?? ''}
                  onChange={(e) => handleChange(key, e.target.value)}
                  className="flex-1 p-2 border rounded"
                />
              )}
            </div>
          );
        })}

        {/* 按钮行：Submit(绿) + Stop(红) */}
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={running}
            className={`flex-1 p-2 rounded text-white ${
              running
                ? 'bg-green-400 cursor-not-allowed opacity-60'
                : 'bg-green-500 hover:bg-green-600'
            }`}
          >
            {t('common.submit')}
          </button>

          <button
            type="button"
            onClick={onStop}
            disabled={!running}
            className={`flex-1 p-2 rounded text-white ${
              running
                ? 'bg-red-500 hover:bg-red-600'
                : 'bg-red-400 cursor-not-allowed opacity-60'
            }`}
          >
            Stop
          </button>
        </div>
      </form>
    </div>
  );
};

export default ScriptForm;
