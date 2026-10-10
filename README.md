# PGuard — Robot Event Summarization using LLMs (IA004)

A ROS 2 pipeline that listens to event logs from an autonomous security robot, buffers them, and uses a local LLM (TinyLlama via Ollama) to produce short summaries for a human security operator. Everything is shown in a live web dashboard.

## Features

- **ROS 2 subscriber** on the `/robot/events` topic (`std_msgs/String`)
- **Log parsing** of `HH:MM:SS [LEVEL] message` into time, level (`INFO` / `WARN` / `ALARM`) and text
- **Batch summarization**: every 15 logs are sent to a local LLM, which returns a 2–3 sentence summary with ALARM events mentioned first
- **Critical mode**: 3 or more ALARMs within 2 minutes triggers an early summary (once at least 5 logs are buffered) and a critical banner in the UI
- **Rate limiting**: at least 30 seconds between LLM calls
- **Alert log**: every ALARM is appended to `alerts.log`
- **Live web dashboard** (Flask + Socket.IO): live log table, counters, buffer progress bar, pipeline stages, summaries with per-summary report, alarm panel, and Stop/Resume controls
- **Fake publisher** included, so the project runs without a real robot

## Architecture

```
fake_publisher.py ──► /robot/events (ROS 2) ──► subscriber.py ──► llm_summarizer.py ──► Ollama (host machine)
                                                     │
                                                     └──► web_server.py (Flask + Socket.IO) ──► Browser dashboard
```

| File | Role |
|------|------|
| `fake_publisher.py` | Publishes a random robot event every 2 seconds (simulates the robot) |
| `subscriber.py` | ROS 2 node: parses logs, buffers them, writes alerts, triggers summaries |
| `llm_summarizer.py` | Sends the buffered logs to Ollama and returns the summary |
| `web_server.py` | Flask/Socket.IO server and the dashboard HTML (port 5000 inside the container) |
| `start.sh` | Sources ROS 2 Humble, starts the publisher in the background, then the subscriber |
| `Dockerfile` | Based on `osrf/ros:humble-desktop`, installs Flask, Flask-SocketIO and gevent |
| `docker-compose.yml` | Maps port `8080 → 5000` and lets the container reach Ollama on the host |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with Docker Compose (Docker Desktop on Windows/macOS)
- [Ollama](https://ollama.com/download) installed and running **on the host machine** (not inside the container)
- An internet connection in the browser (the dashboard loads Socket.IO from a CDN)

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/knanihedi22-commits/PGuard-Robot-Event-Summarization-using-LLMs.git
cd PGuard-Robot-Event-Summarization-using-LLMs
```

### 2. Install the model and start Ollama on the host

```bash
ollama pull tinyllama
ollama serve        # skip if Ollama is already running as a background service
```

Check that it responds:

```bash
curl http://localhost:11434/api/tags
```

### 3. Build and run the project

```bash
docker compose up --build
```

(On older Docker installs, use `docker-compose up --build`.)

### 4. Open the dashboard

Go to **http://localhost:8080**

You should see logs arriving every 2 seconds. After 15 logs (or earlier in critical mode) the first summary appears. Expect up to ~30 seconds between summaries because of the rate limit.

### 5. Stop

Press `Ctrl+C`, then:

```bash
docker compose down
```

## Useful commands

```bash
# Run in the background and follow logs
docker compose up --build -d
docker compose logs -f

# Open a shell in the running container
docker compose exec ia004 bash

# Inspect the ROS 2 topic from inside the container
source /opt/ros/humble/setup.bash
ros2 topic echo /robot/events

# Read the alert log from inside the container
cat ~/ia004/alerts.log
```

## Configuration

| Setting | Where | Default |
|---------|-------|---------|
| Buffer size (logs per summary) | `subscriber.py` → `BUFFER_SIZE` | `15` |
| Min delay between LLM calls | `subscriber.py` → `MIN_DELAY` | `30` s |
| Alert log path | `subscriber.py` → `ALERT_LOG_FILE` | `~/ia004/alerts.log` |
| LLM model | `llm_summarizer.py` → `"model"` | `tinyllama` |
| Ollama URL | `llm_summarizer.py` | `http://host.docker.internal:11434` |
| Publish interval | `fake_publisher.py` → `create_timer` | `2.0` s |
| Dashboard port | `docker-compose.yml` → `ports` | `8080` |
| ROS domain | `docker-compose.yml` → `ROS_DOMAIN_ID` | `0` |

## Using a real robot

To use real data instead of the simulator, remove the `python3 fake_publisher.py &` line from `start.sh`, then publish `std_msgs/String` messages on `/robot/events` in this format:

```
14:32:05 [ALARM] Intrusion detected — Gate A
```

Valid levels are `INFO`, `WARN` and `ALARM`. Messages that don't match the format are treated as `INFO`.

For the container to see a robot on your network, you may need `network_mode: host` (Linux only) and a matching `ROS_DOMAIN_ID`.

## Troubleshooting

**Summary shows `[ERROR] Ollama not running ...`**
Ollama isn't reachable from the container. Make sure it's running on the host and `ollama pull tinyllama` has completed. On Linux, Ollama listens on localhost only by default; start it with `OLLAMA_HOST=0.0.0.0 ollama serve` so the container can reach it.

**Port 8080 already in use**
Change the left side of `"8080:5000"` in `docker-compose.yml`.

**Dashboard loads but nothing updates**
Check `docker compose logs -f` for errors, and make sure the page can load the Socket.IO script from the CDN.

**Summaries are slow**
TinyLlama runs on your CPU unless you have GPU support in Ollama. The request timeout is 60 seconds in `llm_summarizer.py`.

## Notes

- `alerts.log` is written inside the container and is lost when the container is removed. To keep it, add a volume in `docker-compose.yml`:
  ```yaml
  volumes:
    - ./data:/root/ia004
  ```
- The Stop button in the dashboard pauses log processing; Resume continues it.

## Tech stack

ROS 2 Humble · Python 3 · Flask · Flask-SocketIO · gevent · Docker · Ollama (TinyLlama)

