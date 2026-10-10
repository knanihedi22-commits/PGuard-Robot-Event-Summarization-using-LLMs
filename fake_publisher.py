import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from datetime import datetime
import random

EVENTS = [
    ("INFO",  "Patrol started — Zone A"),
    ("INFO",  "Zone A cleared, moving to Zone B"),
    ("INFO",  "Zone B entry checkpoint passed"),
    ("ALARM", "Intrusion detected — Gate A"),
    ("INFO",  "Image captured and stored"),
    ("INFO",  "Alert sent to security operator"),
    ("WARN",  "LiDAR sensor signal weak"),
    ("INFO",  "Patrol resumed normally"),
    ("ALARM", "Unexpected stop detected near Gate C"),
    ("INFO",  "Robot self-recovered and back on route"),
    ("WARN",  "Battery at 22% — returning to base"),
    ("INFO",  "Docking station reached — charging"),
    ("INFO",  "Zone C cleared — no anomalies"),
    ("ALARM", "Perimeter breach detected — sector 4"),
    ("INFO",  "Operator acknowledged alarm"),
]

class FakePublisher(Node):
    def __init__(self):
        super().__init__("fake_publisher")
        self.publisher = self.create_publisher(String, "/robot/events", 10)
        self.timer     = self.create_timer(2.0, self.publish_event)

    def publish_event(self):
        level, message = random.choice(EVENTS)
        timestamp      = datetime.now().strftime("%H:%M:%S")
        msg            = String()
        msg.data       = f"{timestamp} [{level}] {message}"
        self.publisher.publish(msg)
        print(f"robot → {msg.data}")

def main():
    rclpy.init()
    rclpy.spin(FakePublisher())
    rclpy.shutdown()

if __name__ == "__main__":
    main()
