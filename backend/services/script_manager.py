import importlib
from typing import Any, Dict


def run_script(script_path: str, params: Dict[str, Any], lang: str) -> Dict[str, Any]:
    """
    动态导入并执行策略模块
    """
    try:
        module_path = f"tutorials_wrapper.{script_path.replace('/', '.')}"
        script_module = importlib.import_module(module_path)

        if not hasattr(script_module, "run"):

            raise ValueError(f"script {script_path} missing 'run(params)'")

        return script_module.run(params, lang)
    except ModuleNotFoundError:
        raise ValueError(f"Unsupported script: {script_path}")
