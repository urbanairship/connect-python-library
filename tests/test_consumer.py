import json
from os import access
import unittest
import mock

from uaconnect import consumer


class TestConsumer(unittest.TestCase):
    def test_connect_success(self):
        c = consumer.Connection(app_key="key", access_token="token", url="us")

        conn = mock.Mock()
        conn.status_code = 200

        with mock.patch("uaconnect.consumer.requests.post", return_value=conn):
            c.connect(None)

    def test_connect_307(self):
        c = consumer.Connection(app_key="key", access_token="token", url="us")
        c._headers = mock.Mock(return_value={"auth": "fake"})

        redir_conn = mock.Mock()
        redir_conn.status_code = 307
        redir_conn.cookies = {"foo": "bar"}

        good_conn = mock.Mock()
        good_conn.status_code = 200
        good_conn.cookies = None

        payload = json.dumps({"start": "LATEST"})

        # First connection returns a 307 with cookies, second returns a 200
        with mock.patch(
            "uaconnect.consumer.requests.post", side_effect=[redir_conn, good_conn]
        ) as post:
            c.connect(None)

            # Ensure no cookies the first time, then send cookies returned in
            # the 307
            post.assert_has_calls(
                [
                    mock.call(
                        "us",
                        data=payload,
                        headers={"auth": "fake"},
                        stream=True,
                        cookies=None,
                    ),
                    mock.call(
                        "us",
                        data=payload,
                        headers={"auth": "fake"},
                        stream=True,
                        cookies={"foo": "bar"},
                    ),
                ]
            )

    def test_connect_failure_retry(self):
        c = consumer.Connection(app_key="key", access_token="token", url="us")

        conn = mock.Mock()
        conn.status_code = 200

        with mock.patch("uaconnect.consumer.time.sleep") as sleep:
            with mock.patch(
                "uaconnect.consumer.requests.post",
                side_effect=[consumer.requests.exceptions.ConnectionError(), conn],
            ):
                c.connect(None)

                sleep.assert_called_with(0.1)

    def test_connect_failure_retries_exceeded(self):
        c = consumer.Connection(app_key="key", access_token="token", url="us")

        with mock.patch("uaconnect.consumer.time.sleep") as sleep:
            with mock.patch(
                "uaconnect.consumer.requests.post",
                side_effect=consumer.requests.exceptions.ConnectionError(),
            ):
                self.assertRaises(consumer.ConnectionError, c.connect, None)

                # Ensure while reconnecting we got to the max backoff
                sleep.assert_called_with(10)
                # Check that we retried 10 times
                self.assertEqual(sleep.call_count, 9)

    def test_connect_resume_offset(self):
        c = consumer.Connection(app_key="key", access_token="token", url="us")

        c.filters = {}
        conn = mock.Mock()
        conn.status_code = 200

        with mock.patch("uaconnect.consumer.requests.post", return_value=conn):
            c.connect(c.filters, resume_offset="123456789")
            self.assertEqual(c.body, '{"resume_offset": "123456789"}')

    def test_connect_start_earliest(self):
        c = consumer.Connection(app_key="key", access_token="token", url="us")

        c.filters = {}
        conn = mock.Mock()
        conn.status_code = 200

        with mock.patch("uaconnect.consumer.requests.post", return_value=conn):
            c.connect(c.filters, start="EARLIEST")
            self.assertEqual(c.body, '{"start": "EARLIEST"}')

    def test_connect_start_latest(self):
        c = consumer.Connection(app_key="key", access_token="token", url="us")

        c.filters = {}
        conn = mock.Mock()
        conn.status_code = 200

        with mock.patch("uaconnect.consumer.requests.post", return_value=conn):
            c.connect(c.filters, start="LATEST")
            self.assertEqual(c.body, '{"start": "LATEST"}')

    def test_connect_start_invalid_input(self):
        c = consumer.Connection(app_key="key", access_token="token", url="us")

        c.filters = {}

        with mock.patch(
            "uaconnect.consumer.requests.post",
            side_effect=consumer.requests.exceptions.ConnectionError(),
        ):
            self.assertRaises(
                consumer.InvalidParametersError, c.connect, c.filters, start="sdfs3"
            )

    def test_connect_start_and_resume_offset_error(self):
        c = consumer.Connection(app_key="key", access_token="token", url="us")

        c.filters = {}

        with mock.patch(
            "uaconnect.consumer.requests.post",
            side_effect=consumer.requests.exceptions.ConnectionError(),
        ):
            self.assertRaises(
                consumer.InvalidParametersError,
                c.connect,
                c.filters,
                start="LATEST",
                resume_offset="123456789",
            )

    def test_eu_events_url(self):
        c = consumer.Consumer("key", "token", "recorder", url="eu")

        self.assertEqual(c.url, "https://connect.asnapieu.com/api/events")

    def test_default_us_base_url(self):
        c = consumer.Consumer("key", "token", "recorder")

        self.assertEqual(c.url, "https://connect.urbanairship.com/api/events")

    def test_arbitrary_base_url(self):
        c = consumer.Consumer("key", "token", "recorder", url="https://user-input.url/")

        self.assertEqual(c.url, "https://user-input.url/api/events")
