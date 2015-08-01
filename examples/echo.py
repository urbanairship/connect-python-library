import logging
logging.basicConfig()

import eaglecreek

logging.getLogger('eaglecreek').setLevel(logging.DEBUG)

key, secret = "<app key>", "<master secret>"

consumer = eaglecreek.Consumer(key, secret, eaglecreek.FileRecorder('.offset'))
consumer.connect()
for event in consumer.read():
    if event is None:
        continue
    print "Got event: {}".format(event)
    consumer.ack(event)

