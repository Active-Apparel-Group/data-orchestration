"""
Convert .env variables to base64 and prefix with SECRET_
Usage: python tools/base64env.py path/to/.env [output_file]
"""
import base64
import sys
from pathlib import Path


def encode_env_file(env_path, output_path=None):
    # Default output file is .env_encoded in the same directory as the input
    if output_path is None:
        input_dir = Path(env_path).parent
        output_path = input_dir / ".env_encoded"
    
    encoded_lines = []
    
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            b64_value = base64.b64encode(value.encode("utf-8")).decode("utf-8")
            encoded_lines.append(f"SECRET_{key}={b64_value}")
    
    # Write directly to file with UTF-8 encoding
    with open(output_path, "w", encoding="utf-8", newline='\n') as f:
        for line in encoded_lines:
            f.write(line + '\n')
    
    print(f"✅ Encoded {len(encoded_lines)} environment variables")
    print(f"📝 Output saved to: {output_path}")
    print(f"🔤 File encoding: UTF-8")
    
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/base64env.py path/to/.env [output_file]")
        print("Example: python tools/base64env.py .env")
        print("Example: python tools/base64env.py .env .env_encoded")
        sys.exit(1)
    
    env_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result_path = encode_env_file(env_path, output_path)
        print(f"✅ Success! Environment variables encoded to UTF-8 file: {result_path}")
    except FileNotFoundError:
        print(f"❌ Error: File '{env_path}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)