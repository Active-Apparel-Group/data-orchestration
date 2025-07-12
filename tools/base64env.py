"""
Convert .env variables to base64 and prefix with SECRET_
Usage: python utils/env_to_base64.py path/to/.env > .env_encoded
"""
import base64
import sys


def encode_env_file(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            b64_value = base64.b64encode(value.encode("utf-8")).decode("utf-8")
            print(f"SECRET_{key}={b64_value}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python env_to_base64.py path/to/.env")
        sys.exit(1)
    encode_env_file(sys.argv[1])