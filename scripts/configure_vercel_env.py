"""Send only audited runtime variables to the linked Vercel project via stdin."""
import shutil
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app import config

values = {
    "SUPABASE_URL": config.SUPABASE_URL,
    "SUPABASE_SERVICE_ROLE_KEY": config.SUPABASE_KEY,
    "NVIDIA_API_KEY": config.NVIDIA_API_KEY,
    "NVIDIA_LLM_MODEL": config.NVIDIA_LLM_MODEL,
    "NVIDIA_EMBEDDING_MODEL": config.NVIDIA_EMBEDDING_MODEL,
    "EMBEDDING_DIMENSIONS": str(config.EMBEDDING_DIMENSIONS),
}
for name in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST"):
    if config.LANGFUSE_PUBLIC_KEY and config.LANGFUSE_SECRET_KEY:
        values[name] = getattr(config, name)
node = shutil.which("node")
npm_cli = Path(node).parent / "node_modules/npm/bin/npm-cli.js"
for name, value in values.items():
    if not value:
        raise SystemExit(f"Missing required variable: {name}")
    command = [node, str(npm_cli), "exec", "--yes", "--package=vercel@59.24.0", "--", "vercel", "env", "add", name, "production,preview", "--yes", "--force", "--scope", "engopee-gmailcoms-projects"]
    command += ["--sensitive"] if "KEY" in name else ["--no-sensitive"]
    result = subprocess.run(command, input=value, text=True, capture_output=True)
    if result.returncode:
        output = result.stdout + result.stderr
        for secret in values.values():
            if secret: output = output.replace(secret, "[redacted]")
        print(output)
        raise SystemExit(f"Failed to configure {name}")
    print(f"Configured {name} for production and preview", flush=True)
