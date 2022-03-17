import uaconnect
import redis


class RedisRecorder(uaconnect.Recorder):
    redisargs = None
    key = None

    def __init__(self, key, **redisargs):
        super(RedisRecorder, self).__init__()
        self.key = key
        self.redisargs = redisargs
        self._conn = redis.StrictRedis(**redisargs)

    def read_offset(self):
        return self._conn.get(self.key)

    def write_offset(self, offset):
        return self._conn.set(self.key, offset)
