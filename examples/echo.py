import logging

import uaconnect

logging.basicConfig()
logging.getLogger("uaconnect").setLevel(logging.DEBUG)

app_key = "<app key>"
access_token = "<token>"

consumer = uaconnect.EventConsumer(
    app_key=app_key,
    access_token=access_token,
    recorder=uaconnect.FileRecorder(".offset"),
)
consumer.connect()

for event in consumer.read():
    if event is None:
        continue

    print(f"Got event: {event}")
    consumer.ack(event)
