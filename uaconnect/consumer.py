import codecs
import collections
import json
import logging
import os
import select
import time

import requests

logger = logging.getLogger("uaconnect")

CONNECT_URL = 'https://connect.urbanairship.com/api/events/'


class ConnectionError(Exception):
    """Raised when no connection can be established.

    The Connection class will attempt to retry, and will issue this exception
    if retries continue to fail.
    """


class AirshipFailure(Exception):
    """Raised when we get an error response from the server.


    :param args: For backwards compatibility, ``*args`` includes the status and
        response body.

    """

    error = None
    error_code = None
    details = None
    response = None

    def __init__(self, error, error_code, details, response, *args):
        self.error = error
        self.error_code = error_code
        self.details = details
        self.response = response
        super(AirshipFailure, self).__init__(*args)

    @classmethod
    def from_response(cls, response):
        """Instantiate a ValidationFailure from a Response object"""

        try:
            payload = response.json()
            error = payload.get('error')
            error_code = payload.get('error_code')
            details = payload.get('details')
        except ValueError:
            error = response.reason
            error_code = None
            details = response.content

        logger.error(
            "Request failed with status %d: '%s %s': %s",
            response.status_code, error_code, error, json.dumps(details))

        return cls(
            error,
            error_code,
            details,
            response,
            response.status_code,
            response.content
        )


class Connection(object):
    """Internal class used to wrap connections"""

    app_key = None
    access_token = None
    stream = None
    _conn = None
    stop = False
    url = None
    cookies = None

    def __init__(self, app_key, access_token, url):
        self.app_key = app_key
        self.access_token = access_token
        self.url = url

    def close(self):
        if not self._conn.raw.closed:
            self._conn.close()
        self._conn = None
        self.stream = None

    def _headers(self):
        auth = 'Bearer %s' % self.access_token
        headers = {
            'Authorization': auth,
            'Accept': 'application/vnd.urbanairship+x-ndjson; version=3;',
            'Content-Type': 'application/json',
            'X-UA-Appkey': self.app_key,
        }
        return headers

    def connect(self, filters, resume_offset=None, start=None):
        logger.info("Opening connection to %s, offset %s", self.url,
            resume_offset or start)

        backoff = 0.1
        attempts = 0

        while not self.stop:
            attempts += 1
            payload = {}
            if resume_offset:
                payload['resume_offset'] = resume_offset
            elif start:
                payload['start'] = start
            else:
                payload['start'] = 'LATEST'
            if filters:
                payload['filters'] = filters
            body = json.dumps(payload)

            try:
                self._conn = requests.post(self.url, data=body,
                        headers=self._headers(), stream=True,
                        cookies=self.cookies)
                if self._conn.status_code == 307:
                    logging.info("Handling redirect, retrying [%s]", attempts)
                    self.cookies = self._conn.cookies
                    continue
                elif not self._conn.status_code == 200:
                    raise AirshipFailure.from_response(self._conn)
                self.stream = self._conn.iter_lines()
                attempts = 0
                break
            except requests.exceptions.ConnectionError:
                if attempts > 9:
                    raise ConnectionError("Unable to connect after [%s] attempts, giving up" % attempts)
                logging.info("Connection failed, retrying [%s]", attempts)
                time.sleep(backoff)
                backoff += backoff * attempts
                if backoff > 10:
                    backoff = 10

        logger.info("Connection opened to %s", self.url)


class Consumer(object):
    """UA Connect consumer object."""

    app_key = None
    access_token = None
    recorder = None
    url = None
    connection = None
    outstanding = None
    _stop = False
    offset_filename = '.offset'
    offset = 'LATEST'
    filters = None

    def __init__(self, app_key, access_token, recorder, url=None):
        self.app_key = app_key
        self.access_token = access_token
        self.recorder = recorder
        if url is not None:
            self.url = url
        else:
            self.url = CONNECT_URL
        self.outstanding = collections.OrderedDict()
        self.connection = Connection(app_key, access_token, self.url)
        self.filters = []

    def _record(self, event):
        self.outstanding[event.offset] = event

    def ack(self, event):
        """Acknowledge an event so that it is not re-read."""

        offset = event.offset

        # check that offset is in outstanding
        if offset not in self.outstanding:
            raise ValueError("Received ack for unknown event offset {}".format(offset))
        last = None

        if offset == next(iter(self.outstanding)):
            last = offset
            self.outstanding.pop(offset)

            # We can get acks in any order, so search through any already ack'd
            # items after the one we just marked, to clean them up and to store
            # the very last offset.
            for outstanding_offset, acked in self.outstanding.items():
                if not acked:
                    break
                last = outstanding_offset
                self.outstanding.pop(outstanding_offset)
        else:
            # This is not the oldest event, but mark that we've ack'd it
            self.outstanding[offset] = True

        if last is not None:
            self.recorder.write_offset(last)
            self.offset = last

    def connect(self):
        """Connect to the stream using the given filters and offset/start."""
        self.offset = self.recorder.read_offset()
        if self.offset:
            self.connection.connect(self.access_token, self.filters,
                resume_offset=self.offset)
        else:
            self.connection.connect(self.access_token, self.filters,
                start='LATEST')

    def read(self):
        """Read the stream and yield each event as it is streamed.

        This function can yield a None, so that a caller can perform periodic
        actions during slow times.
        """
        self._stop = False
        while not self._stop:
            try:
                line = next(self.connection.stream)
                if not line:
                    # Got keepalive in form of blank line
                    yield None
                    continue
                logger.debug("Received entry: %s", line)
                e = Event.from_json(line)
                self._record(e)
                yield e
            except (requests.exceptions.ConnectionError,
                    StopIteration):
                self.connection.close()
                self.connection.connect(self.access_token, resume_offset=self.offset)

    def stop(self):
        """Instruct the consumer to stop and close the connection cleanly."""
        self._stop = True

    def add_filter(self, filter_):
        """Add a ``uaconnect.Filter`` to the stream.

        To reconnect with a new filter the consumer must be `close()`ed and
        then reconnected.

        """
        self.filters.append(filter_.filters)


class Event(object):
    """An event returned from Connect."""

    __slots__ = ('raw', 'data', 'id', 'device', 'event_type', 'offset')

    @classmethod
    def from_json(cls, payload):
        event = cls()
        event.raw = payload
        event.data = json.loads(payload.decode('utf8'))
        event.id = event.data['id']
        event.event_type = event.data['type']
        event.offset = event.data['offset']
        event.device = event.data.get('device', None)
        return event

    def __repr__(self):
        return "<Event {} {} [{}]>".format(self.event_type, self.id,
            self.offset)
