import json
import logging
import time
from typing import Any, Iterator, List, Optional, Dict, Tuple, Union

import requests
from requests.cookies import RequestsCookieJar

from uaconnect import Recorder, Filter, recorder

# import uaconnect

logger = logging.getLogger("uaconnect")


US_BASE_URL: str = "https://connect.urbanairship.com/"
EU_BASE_URL: str = "https://connect.asnapieu.com/"
EVENT_PATH: str = "api/events"
COMPLIANCE_PATH: str = "api/events/general"


class InvalidParametersError(Exception):
    """Raised when request is malformed. Includes both the 'resume_offset' and 'start' params.

    The request will be canceled and not sent to the server.
    """


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
        self.error: Optional[str] = error
        self.error_code: Optional[str] = error_code
        self.details: Optional[str] = details
        self.response: Optional[str] = response
        super(AirshipFailure, self).__init__(*args)

    @classmethod
    def from_response(cls, response: requests.Response):
        """Instantiate a ValidationFailure from a Response object"""

        try:
            payload: Dict = response.json()
            error = payload.get("error")
            error_code = payload.get("error_code")
            details = payload.get("details")
        except ValueError:
            error = response.reason
            error_code = None
            details = response.content

        logger.error(
            "Request failed with status %d: '%s %s': %s",
            response.status_code,
            error_code,
            error,
            json.dumps(details),
        )

        return cls(
            error, error_code, details, response, response.status_code, response.content
        )


class Event(object):
    """An event returned from RTDS."""

    __slots__ = (
        "raw",
        "data",
        "id",
        "device",
        "event_type",
        "offset",
        "occurred",
        "processed",
        "body",
    )

    @classmethod
    def from_json(cls, payload):
        event = cls()
        event.raw = payload
        event.data = json.loads(payload)
        event.id = event.data["id"]
        event.event_type = event.data["type"]
        event.offset = event.data["offset"]
        event.device = event.data.get("device", None)
        event.occurred = event.data["occurred"]
        event.processed = event.data["processed"]
        event.body = event.data.get("body")

        return event

    def __repr__(self):
        return (
            f"<[{self.occurred}] - Event {self.event_type} {self.id} [{self.offset}]>"
        )


class Connection:
    app_key: Optional[str] = None
    access_token: Optional[str] = None
    master_secret: Optional[str] = None
    stream: Optional[Iterator] = None
    stop: bool = False
    url: str
    cookies: Optional[RequestsCookieJar] = None
    _conn: Optional[requests.Response] = None

    def __init__(
        self,
        app_key: str,
        url: str,
        access_token: Optional[str] = None,
        master_secret: Optional[str] = None,
    ):
        """Internal class used to wrap connections

        :param app_key: The app key used to identify an Airship project to stream
        events for
        :param access_token: Optional. A bearer token used to authenticate with the
        events API
        :param master_secret: Optional. The project's master secret used to authenticate
        with the compliance events API
        :param url: Optional. Possible values: 'us' or 'eu' to automatically use the
        Airship site your project is based in. You may also input an arbitrary base url
        """
        self.app_key = app_key
        self.access_token = access_token
        self.master_secret = master_secret
        self.url = url

    def close(self) -> None:
        """Cleanly close streaming connection"""
        if self._conn and not self._conn.raw.closed:
            self._conn.close()
        self._conn = None
        self.stream = None

    def _headers(self) -> Dict[str, Any]:
        """Create request headers, adding bearer token if present"""
        headers = {
            "Accept": "application/vnd.urbanairship+x-ndjson; version=3;",
            "Content-Type": "application/json",
            "X-UA-Appkey": self.app_key,
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers

    def connect(
        self,
        filters: List[Dict[str, Any]],
        resume_offset: Optional[str] = None,
        start=None,
    ) -> None:
        """Creates streaming connection to Airship RTDS API.

        :param filters: Required. A list of uaconnect.Filter objects used to limit
        events returned from the API
        :param resume_offset: Optional. A numeric string representing the event offset to
        resume consuming from. Use uaconnect.FileRecorder.read_offset() to read from
        saved offset cursor
        :param start: Optional. Specifies that the stream should start at the
        beginning or the end of the project's data window. One of "EARLIEST" or "LATEST"
        """
        logger.info(
            "Opening connection to %s, offset %s", self.url, resume_offset or start
        )

        backoff: float = 0.1
        attempts: int = 0

        while not self.stop:
            attempts += 1
            payload: Dict[str, Any] = {}

            if resume_offset and start:
                logging.error("Request can only have start or resume_offset parameter")
                self.stop
                raise InvalidParametersError
            elif resume_offset:
                payload["resume_offset"] = resume_offset
            elif start == "EARLIEST" or start == "LATEST":
                payload["start"] = start
            elif start is None and resume_offset is None:
                payload["start"] = "LATEST"
            else:
                logging.error("Start can only be one of EARLIEST or LATEST")
                self.stop
                raise InvalidParametersError

            if filters:
                payload["filters"] = filters

            self.body = json.dumps(payload)

            try:
                if self.access_token:
                    self._conn = requests.post(
                        self.url,
                        data=self.body,
                        headers=self._headers(),
                        stream=True,
                        cookies=self.cookies,
                    )
                else:
                    self._conn = requests.post(
                        self.url,
                        data=self.body,
                        auth=(self.app_key, self.master_secret),
                        headers=self._headers(),
                        stream=True,
                        cookies=self.cookies,
                    )

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
                    errorString = (
                        "Unable to connect after [%s] attempts, " "giving up" % attempts
                    )
                    raise ConnectionError(errorString)

                logging.info("Connection failed, retrying [%s]", attempts)
                time.sleep(backoff)

                backoff += backoff * attempts

                if backoff > 10:
                    backoff = 10

        logger.info("Connection opened to %s", self.url)


class Consumer(object):
    """UA Connect consumer object."""

    app_key: str
    access_token: Optional[str] = None
    master_secret: Optional[str] = None
    recorder: Recorder
    base_url: Optional[str] = None
    url: str
    api_path: str = EVENT_PATH
    connection: Connection
    outstanding: Dict
    offset_filename: str = ".offset"
    offset: Optional[str] = None
    filters: List[Dict[str, Any]]
    _stop: bool = False

    def __init__(
        self,
        app_key,
        recorder,
        access_token=None,
        master_secret=None,
        url="us",
    ) -> None:
        self.app_key = app_key
        self.access_token = access_token
        self.master_secret = master_secret
        self.recorder = recorder
        self.outstanding = {}
        self.filters = []

        if url.lower() == "us":
            self.base_url = US_BASE_URL
            logging.info("Using US base url")
        elif url.lower() == "eu":
            self.base_url = EU_BASE_URL
            logging.info("Using EU base url")
        else:
            self.base_url = url
            logging.info(f"Using base url: {url}")

        self.url = f"{self.base_url}{self.api_path}"

        if self.access_token:
            self.connection = Connection(
                app_key=self.app_key, access_token=self.access_token, url=self.url
            )
        else:
            self.connection = Connection(
                app_key=self.app_key, master_secret=self.master_secret, url=self.url
            )

    def _record(self, event: Event) -> None:
        self.outstanding[event.offset] = event  # type: ignore

    def ack(self, event: Event) -> None:
        """Acknowledge an event so that it is not re-read."""

        offset: str = event.offset  # type: ignore

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

    def connect(
        self, resume_offset: Optional[str] = None, start: Optional[str] = None
    ) -> None:
        """Connect to the stream using the given filters and offset/start.
        If neither resume_offset nor start are passed, we will attempt to
        read the offset from the recorder."""
        possible_start_values: Tuple[str, str] = ("LATEST", "EARLIEST")

        if start and resume_offset:
            logging.error("Request can only have start or resume_offset parameter")
            raise InvalidParametersError
        elif start not in possible_start_values:
            logging.error("Start can only be one of EARLIEST or LATEST")
            raise InvalidParametersError
        elif start in possible_start_values:
            self.start = start
        elif resume_offset:
            self.offset = resume_offset
        else:
            logging.info(
                "Neither start nor resume_offset was provided. Attempting to read offset from recorder."
            )
            self.offset = self.recorder.read_offset()

        if self.offset:
            self.connection.connect(filters=self.filters, resume_offset=self.offset)
        elif self.start:
            self.connection.connect(filters=self.filters, start=self.start)
        else:
            self.connection.connect(filters=self.filters, start="LATEST")

    def read(self) -> Iterator[Union[Event, None]]:
        """Read the stream and yield each event as it is streamed.

        This function can yield a None, so that a caller can perform periodic
        actions during slow times.
        """
        self._stop = False
        while not self._stop:
            try:
                line = next(self.connection.stream)  # type: ignore
                if not line:
                    # Got keepalive in form of blank line
                    yield None
                    continue
                logger.debug("Received entry: %s", line)
                e = Event.from_json(line)
                self._record(e)
                yield e
            except (requests.exceptions.ConnectionError, StopIteration):
                self.connection.close()
                self.connection.connect(filters=self.filters, resume_offset=self.offset)

    def stop(self) -> None:
        """Instruct the consumer to stop and close the connection cleanly."""
        self._stop = True

    def add_filter(self, filter_: Filter) -> None:
        """Add a ``uaconnect.Filter`` to the stream.

        To reconnect with a new filter the consumer must be `close()`ed and
        then reconnected.

        """
        self.filters.append(filter_.filters)


class EventConsumer(Consumer):
    """Consume Real Time Data Stream events from the Airship RTDS Streaming API."""

    api_path: str = EVENT_PATH

    def __init__(
        self,
        app_key: str,
        access_token: str,
        recorder: Recorder,
        url: str = "us",
    ) -> None:
        super().__init__(
            app_key=app_key, access_token=access_token, recorder=recorder, url=url
        )

        if not access_token:
            raise InvalidParametersError(
                "access_token authentication must be used to authenticate with EventConsumer"
            )


class ComplianceConsumer(Consumer):
    """Consume Real Time Data Stream Compliance events from the Airship RTDS Streaming API"""

    api_path: str = COMPLIANCE_PATH

    def __init__(
        self, app_key: str, master_secret: str, recorder: Recorder, url: str = "us"
    ) -> None:
        super().__init__(
            app_key=app_key, master_secret=master_secret, recorder=recorder, url=url
        )

        if not master_secret:
            raise InvalidParametersError(
                "master_secret authentication must be used to authenticate with ComplianceConsumer"
            )
