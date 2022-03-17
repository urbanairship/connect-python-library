import logging

logging.basicConfig()

import uaconnect

logging.getLogger("uaconnect").setLevel(logging.DEBUG)

app_key = "<app key>"
access_token = "<token>"

consumer = uaconnect.Consumer(app_key, access_token, uaconnect.FileRecorder(".offset"))
consumer.connect()
for event in consumer.read():
    if event is None:
        continue
    print(f"Got event: {event}")
    consumer.ack(event)
