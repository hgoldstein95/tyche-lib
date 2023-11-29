import atexit
import json
import threading
import hypothesis
import websocket

PORT = 8181
POLLING_INTERVAL_SECONDS = 1


# Adapted from https://stackoverflow.com/questions/3393612/run-certain-code-every-n-seconds
class RepeatedTimer(object):

    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.daemon = True
            self._timer.start()
            self.is_running = True

    def stop(self):
        if self._timer is not None:
            self._timer.cancel()
        self.is_running = False


class TycheManager:

    def __init__(self):
        self._queue = []
        self._connection = websocket.create_connection(
            f"ws://localhost:{PORT}")
        atexit.register(self._cleanup)
        self._timer = RepeatedTimer(POLLING_INTERVAL_SECONDS, self._flush)

    def _cleanup(self):
        self._timer.stop()
        self._flush()
        self._connection.close()

    def _flush(self):
        result = "\n".join(json.dumps(line) for line in self._queue) + "\n"
        self._connection.send(result)
        self._queue = []

    def enqueue(self, test_case):
        self._queue.append(test_case)


manager = TycheManager()

hypothesis.internal.observability.TESTCASE_CALLBACKS.append(  # type: ignore
    manager.enqueue)
