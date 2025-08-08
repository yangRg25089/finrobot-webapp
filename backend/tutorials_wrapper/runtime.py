# tutorials_wrapper/runtime.py
from functools import wraps
from typing import Callable


def guard_run(reraise: bool = True):
    """
    装饰 run(params, lang):
      - 捕获异常，如果有exception 事件并 print("ERROR: ...")
      - reraise=True: 继续抛出给上层 run_script_stream 处理
    """

    def _decorator(func: Callable):
        @wraps(func)
        def _wrapped(params, lang, *args, **kwargs):
            try:
                return func(params, lang, *args, **kwargs)
            except Exception as exc:
                print(f"ERROR: {exc}")
                if reraise:
                    raise
                return {"error": str(exc)}

        return _wrapped

    return _decorator
