import logging
logging.basicConfig()

import eaglecreek
import redis
from eaglecreek.ext import redisrecorder

redis = redis.StrictRedis()
logging.getLogger('eaglecreek').setLevel(logging.DEBUG)

key, secret = "<app key>", "<master secret>"

consumer = eaglecreek.Consumer(key, secret, redisrecorder.RedisRecorder('eaglecreek-offset'))
consumer.connect()
for event in consumer.read():
    if event is None:
        continue
    redis.lpush("eaglecreek-events", event.raw)
    consumer.ack(event)

