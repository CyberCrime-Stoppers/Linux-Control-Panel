import subprocess
import threading
from queue import Queue


class WorkerPool:
    """Reusable worker thread pool for background commands."""

    def __init__(self, max_workers=4):
        self.queue = Queue()
        self.workers = []

        for _ in range(max_workers):
            t = threading.Thread(target=self._loop, daemon=True)
            t.start()
            self.workers.append(t)

    def _loop(self):
        while True:
            task = self.queue.get()
            if task is None:
                break
            cmd, callback = task
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=30
                )
                if callback:
                    callback(result.stdout, result.stderr, result.returncode)
            except subprocess.TimeoutExpired:
                if callback:
                    callback("", "Command timed out after 30s", -1)
            except FileNotFoundError as e:
                if callback:
                    callback("", f"Command not found: {e}", -1)
            except PermissionError:
                if callback:
                    callback("", "Permission denied — try sudo", -1)
            except Exception as e:
                if callback:
                    callback("", str(e), -1)
            self.queue.task_done()

    def submit(self, cmd_list, callback=None):
        self.queue.put((cmd_list, callback))

    def shutdown(self):
        for _ in self.workers:
            self.queue.put(None)
