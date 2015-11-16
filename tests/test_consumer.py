import json
import unittest

try:
    from unittest import mock
except ImportError:
    import mock

from uaconnect import consumer


class TestConsumer(unittest.TestCase):

    def test_connect_success(self):
        c = consumer.Connection('key', 'token', 'url')

        conn = mock.Mock()
        conn.status_code = 200

        with mock.patch('uaconnect.consumer.requests.post', return_value=conn):
            c.connect(None)

    def test_connect_307(self):
        c = consumer.Connection('key', 'token', 'url')
        c._headers = mock.Mock(return_value={'auth': 'fake'})

        redir_conn = mock.Mock()
        redir_conn.status_code = 307
        redir_conn.cookies = {'foo': 'bar'}

        good_conn = mock.Mock()
        good_conn.status_code = 200
        good_conn.cookies = None

        payload = json.dumps({'start': 'LATEST'})

        # First connection returns a 307 with cookies, second returns a 200
        with mock.patch('uaconnect.consumer.requests.post',
                side_effect=[redir_conn, good_conn]) as post:
            c.connect(None)

            # Ensure no cookies the first time, then send cookies returned in
            # the 307
            post.assert_has_calls([
                mock.call('url', data=payload,
                    headers={'auth': 'fake'}, stream=True, cookies=None),
                mock.call('url', data=payload,
                    headers={'auth': 'fake'}, stream=True, cookies={'foo': 'bar'}),
            ])

    def test_connect_failure_retry(self):
        c = consumer.Connection('key', 'token', 'url')

        conn = mock.Mock()
        conn.status_code = 200

        with mock.patch('uaconnect.consumer.time.sleep') as sleep:
            with mock.patch('uaconnect.consumer.requests.post',
                    side_effect=[consumer.requests.exceptions.ConnectionError(), conn]):
                c.connect(None)

                sleep.assert_called_with(0.1)

    def test_connect_failure_retries_exceeded(self):
        c = consumer.Connection('key', 'token', 'url')

        with mock.patch('uaconnect.consumer.time.sleep') as sleep:
            with mock.patch('uaconnect.consumer.requests.post',
                    side_effect=consumer.requests.exceptions.ConnectionError()):
                self.assertRaises(consumer.ConnectionError, c.connect, None)

                # Ensure while reconnecting we got to the max backoff
                sleep.assert_called_with(10)
                # Check that we retried 10 times
                self.assertEqual(sleep.call_count, 9)

