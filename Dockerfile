FROM osrf/ros:humble-desktop

RUN apt-get update && apt-get install -y python3-pip && rm -rf /var/lib/apt/lists/*

RUN pip3 install flask flask-socketio gevent gevent-websocket

WORKDIR /ia004
COPY . .
RUN chmod +x start.sh

EXPOSE 5000

CMD ["bash", "start.sh"]
