import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

interface ScriptFormProps {
  selectedScript: { script_name: string; folder: string; params: any } | null;
  onSubmit: (data: { script_name: string; folder: string; params: any }) => Promise<void> | void;
  loading?: boolean; // ← 新增，可选
}

const ScriptForm: React.FC<ScriptFormProps> = ({ selectedScript, onSubmit, loading = false }) => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState<Record<string, any>>({});

  // 当选择的脚本变化时，初始化默认值
  useEffect(() => {
    if (!selectedScript) {
      setFormData({});
      return;
    }
    const initial: Record<string, any> = {};
    Object.entries(selectedScript.params).forEach(([key, cfg]) => {
      const paramConfig = (cfg as any) || {};
      const def = paramConfig.defaultValue ?? "";
      initial[key] = def;
    });
    setFormData(initial);
  }, [selectedScript]);

  if (!selectedScript) {
    return <p>{t("common.switchscript")}</p>;
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

  return (
    <form onSubmit={handleSubmit} className="p-4 bg-white shadow rounded space-y-4">
      {Object.entries(selectedScript.params).map(([key, cfg]) => {
        const paramConfig = (cfg as any) || {};
        const type = paramConfig.type ?? "text";

        return (
          <div key={key}>
            <label className="block text-gray-700 mb-1">{t(`params.${key}`)}</label>
            <input
              type={type}
              value={formData[key] ?? ""}          // ← 只从 state 读
              onChange={(e) => handleChange(key, e.target.value)}
              className="w-full p-2 border rounded"
            />
          </div>
        );
      })}

      <button
        type="submit"
        disabled={loading}
        className={`w-full p-2 rounded text-white ${
          loading ? "bg-blue-400 cursor-not-allowed opacity-60" : "bg-blue-500 hover:bg-blue-600"
        }`}
      >
        {loading ? t("common.submitting") : t("common.submit")}
      </button>
    </form>
  );
};

export default ScriptForm;
