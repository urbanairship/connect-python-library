"""Redis Queue example

This example script reads from the Urban Airship Connect stream, writing files
into a Redis queue. Offsets are stored in Redis as well, using the included
uaconnect.ext.redisrecorder module.

On SIGINT, the consumer is cleanly shut down so that the last event can be
processed correctly and the last offset stored in Redis.

"""
from __future__ import print_function

import argparse
import logging
import signal
import sys
logging.basicConfig()

import uaconnect
import redis
from uaconnect.ext import redisrecorder

logging.getLogger('uaconnect').setLevel(logging.INFO)


def consume(key, token, types):
    redisconn = redis.StrictRedis()
    consumer = uaconnect.Consumer(key, token, redisrecorder.RedisRecorder('uaconnect-offset'))
    consumer.connect()

    def shutdown_handler(signum, frame):
        print("Shutting down", file=sys.stderr)
        consumer.stop()
    signal.signal(signal.SIGINT, shutdown_handler)

    for event in consumer.read():
        if event is None:
            continue
        redisconn.lpush("uaconnect-events", event.raw)
        consumer.ack(event)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Stream Urban Airship Connect events into Redis')
    parser.add_argument('key', type=str, help='Urban Airship Application Key')
    parser.add_argument('token', type=str, help='Access Token')
    parser.add_argument('-v', '--verbose', dest='verbose',
        default=False, action='store_true', help='Log extra information')
    parser.add_argument('--types', dest='types', action='append', help='Process only these event types')

    args = parser.parse_args()
    if args.verbose:
        logging.getLogger('uaconnect').setLevel(logging.DEBUG)

    consume(args.key, args.token, args.types)
