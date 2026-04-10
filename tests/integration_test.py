from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    server_cmd = [sys.executable, "-m", "server.server", "--host", "127.0.0.1", "--port", "9443"]
    client_cmd = [
        sys.executable,
        "-m",
        "client.client",
        "--host",
        "127.0.0.1",
        "--port",
        "9443",
        "--message",
        "ADAS telemetry link validation",
    ]

    server = subprocess.Popen(server_cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        time.sleep(2)
        result = subprocess.run(client_cmd, cwd=ROOT, capture_output=True, text=True, check=True)
        print(result.stdout.strip())
    finally:
        server.terminate()
        try:
            stdout, stderr = server.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            stdout, stderr = server.communicate()

        if stdout.strip():
            print(stdout.strip())
        if stderr.strip():
            print(stderr.strip(), file=sys.stderr)


if __name__ == "__main__":
    main()
