import re
import os
import time
import threading
from datetime import datetime

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from llm_summarizer import summarize_logs
import web_server

BUFFER_SIZE    = 15
MIN_DELAY      = 30
ALERT_LOG_FILE = os.path.expanduser("~/ia004/alerts.log")
file_lock      = threading.Lock()
last_call_time = 0

def ensure_log_file():
    os.makedirs(os.path.dirname(ALERT_LOG_FILE), exist_ok=True)
    if not os.path.exists(ALERT_LOG_FILE):
        with open(ALERT_LOG_FILE, "w") as f:
            f.write(f"=== PGuard Alert Log — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")

def write_alert(timestamp, message):
    with file_lock:
        with open(ALERT_LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] ALARM — {message}\n")

def parse_log(raw):
    match = re.match(r"(\d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s+(.*)", raw.strip())
    if match:
        return match.group(1), match.group(2), match.group(3)
    return datetime.now().strftime("%H:%M:%S"), "INFO", raw.strip()

def call_llm(log_buffer):
    global last_call_time
    now = time.time()
    elapsed = now - last_call_time
    if elapsed < MIN_DELAY:
        time.sleep(MIN_DELAY - elapsed)
    last_call_time = time.time()
    return summarize_logs(log_buffer)

class LogSubscriber(Node):
    def __init__(self):
        super().__init__("log_subscriber")
        self.subscription = self.create_subscription(
            String, "/robot/events", self.listener_callback, 10
        )
        self.log_buffer = []
        self.alarm_times = []
        ensure_log_file()
        web_server.start_server()

    def listener_callback(self, msg):
        global last_call_time
        if web_server.is_paused():
            return
        timestamp, level, message = parse_log(msg.data)

        web_server.emit_log(timestamp, level, message)
        web_server.emit_pipeline("receiving")

        if level == "ALARM":
            write_alert(timestamp, message)
            self.alarm_times.append(datetime.now())
            self.alarm_times = [t for t in self.alarm_times if (datetime.now() - t).total_seconds() <= 120]

        self.log_buffer.append(msg.data)
        web_server.emit_buffer(len(self.log_buffer), BUFFER_SIZE)
        web_server.emit_pipeline("collecting")

        critical = len(self.alarm_times) >= 3

        if len(self.log_buffer) >= BUFFER_SIZE or (critical and len(self.log_buffer) >= 5):
            web_server.emit_pipeline("summarizing")
            batch = list(self.log_buffer)
            summary = call_llm(self.log_buffer)
            web_server.emit_summary(summary, datetime.now().strftime("%H:%M:%S"), batch)
            self.log_buffer = []
            web_server.emit_buffer(0, BUFFER_SIZE)
            web_server.emit_pipeline("idle")

def main():
    rclpy.init()
    rclpy.spin(LogSubscriber())
    rclpy.shutdown()

if __name__ == "__main__":
    main()
