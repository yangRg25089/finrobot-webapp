import asyncio
import importlib
import traceback
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, AsyncGenerator, Dict


class _LineEmitter:
    """把 write() 收到的字符按行切分，逐行发到 asyncio.Queue。"""

    def __init__(self, queue: asyncio.Queue, kind: str = "stdout"):
        self.queue = queue
        self.kind = kind
        self._buf = ""

    def write(self, s: str):
        if not isinstance(s, str):
            s = str(s)
        self._buf += s
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            if line.strip():  # 过滤空行
                self.queue.put_nowait({"type": self.kind, "text": line})

    def flush(self):
        if self._buf.strip():
            self.queue.put_nowait({"type": self.kind, "text": self._buf.strip()})
        self._buf = ""


async def run_script_stream(
    script_path: str, params: Dict[str, Any], lang: str
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    动态导入并执行模块（流式返回）：
      - 逐行推送 {"type":"stdout"|"stderr","text":...}
      - 结束时推 {"type":"result","result":...} 或 {"type":"error","error":...}
      - 最后必推 {"type":"exit"}
    """
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def _runner():
        try:
            module_path = f"tutorials_wrapper.{script_path.replace('/', '.')}"
            script_module = importlib.import_module(module_path)

            run_fn = getattr(script_module, "run", None)
            if not callable(run_fn):
                raise ValueError(f"script {script_path} missing 'run(params, lang)'")

            out = _LineEmitter(queue, "stdout")
            err = _LineEmitter(queue, "stderr")

            # 捕获脚本内部的 print 到 stdout/stderr
            with redirect_stdout(out), redirect_stderr(err):
                # 统一按 run(params, lang) 调用；如果脚本签名有第三个可选参数也无碍
                result = run_fn(params, lang)

            out.flush()
            err.flush()

            queue.put_nowait({"type": "result", "result": result})
        except Exception as e:
            error_msg = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            queue.put_nowait({"type": "error", "error": error_msg})
        finally:
            queue.put_nowait({"type": "exit"})

    # 放线程池里，避免阻塞事件循环
    fut = loop.run_in_executor(None, _runner)

    # 把队列事件逐个送给 SSE
    try:
        while True:
            ev = await queue.get()
            yield ev
            if ev.get("type") == "exit":
                break
    finally:
        # Best-effort 等后台线程收尾
        try:
            await asyncio.wrap_future(fut)  # type: ignore[arg-type]
        except Exception:
            pass
