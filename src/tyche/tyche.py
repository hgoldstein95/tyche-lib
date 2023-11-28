import json
import os
import time
import hypothesis
import websocket

PORT = 8181
OUTPUT_FILE = lambda property: f".tyche/{property}.jsonl"


def visualize(write_to_websocket=True, write_to_file=False):

    def decorator(f):

        def wrapper(*args, **kwargs):
            global queue
            global last_flush

            queue = []
            last_flush = time.time()

            # Flush queue to file, websocket, or both
            def flush():
                global queue
                global last_flush

                result = "\n".join(json.dumps(line) for line in queue) + "\n"

                if write_to_websocket:
                    ws = websocket.create_connection(f"ws://localhost:{PORT}")
                    ws.send(result)
                    ws.close()

                if write_to_file:
                    fname = OUTPUT_FILE(
                        f.__name__) if callable(OUTPUT_FILE) else OUTPUT_FILE
                    os.makedirs(os.path.dirname(fname), exist_ok=True)
                    with open(fname, "a") as handle:
                        handle.write(result)

                last_flush = time.time()
                queue = []

            # Add a test case to the queue and potentially flush
            def handle_test_case(test_case):
                global queue
                global last_unflushed

                queue.append(test_case)
                if time.time() - last_flush > 1:
                    flush()

            hypothesis.internal.observability.TESTCASE_CALLBACKS.append(  # type: ignore
                handle_test_case)
            try:
                f()
            finally:
                flush()

        return wrapper

    return decorator
