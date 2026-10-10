import json
import urllib.request
import urllib.error

def summarize_logs(log_list):
    logs_text = "\n".join(log_list)
    prompt = (
        "You are a security robot monitoring assistant for PGuard autonomous robots. "
        "Summarize these robot event logs in 2-3 sentences for a human security operator. "
        "Mention ALARM events first. Be professional and concise.\n\n"
        f"Logs:\n{logs_text}\n\nSummary:"
    )
    payload = json.dumps({
        "model": "tinyllama",
        "prompt": prompt,
        "stream": False
    }).encode("utf-8")

    req = urllib.request.Request(
        "http://host.docker.internal:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            result = json.loads(r.read().decode())
            return result.get("response", "[ERROR] No response").strip()
    except urllib.error.URLError:
        return "[ERROR] Ollama not running on Windows — see instructions"
    except Exception as e:
        return f"[ERROR] {str(e)}"
