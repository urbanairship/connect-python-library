import unittest

import eaglecreek


class TestFilter(unittest.TestCase):

    def test_invalid_device_type(self):
        f = eaglecreek.Filter()

        self.assertRaises(ValueError, f.device_types, 'ios', 'foobar')
        self.assertRaises(ValueError, f.device_types)
        self.assertRaises(ValueError, f.device_types, 'blackberry')

    def test_device_type(self):
        f = eaglecreek.Filter()
        f.device_types('ios')
        self.assertEqual(f.filters['device_types'], ['ios'])

        f.device_types('ios', 'android', 'amazon')
        self.assertEqual(f.filters['device_types'], ['ios', 'android', 'amazon'])

    def test_invalid_event_type(self):
        f = eaglecreek.Filter()

        self.assertRaises(ValueError, f.types)

        # Invalid event type does not raise value error, as this list is more
        # likely to change.
        f.types('FUTURE_EVENT')

    def test_event_type(self):
        f = eaglecreek.Filter()
        f.types('OPEN')
        self.assertEqual(f.filters['types'], ['OPEN'])

        f.types('OPEN', 'CLOSE')
        self.assertEqual(f.filters['types'], ['OPEN', 'CLOSE'])

        f.types('open')
        self.assertEqual(f.filters['types'], ['OPEN'])

    def test_latency(self):
        f = eaglecreek.Filter()
        f.latency(10000)
        self.assertEqual(f.filters['latency'], 10000)

    def test_invalid_notifications(self):
        f = eaglecreek.Filter()
        self.assertRaises(ValueError, f.notifications)
        self.assertRaises(ValueError, f.notifications, push_id='1234', group_id='5678')

    def test_notifications(self):
        f = eaglecreek.Filter()
        f.notifications(push_id='1234')
        self.assertEqual(f.filters['notifications'], {'push_id': '1234'})

        f.notifications(group_id='1234')
        self.assertEqual(f.filters['notifications'], {'group_id': '1234'})

    def test_invalid_devices(self):
        f = eaglecreek.Filter()
        self.assertRaises(ValueError, f.devices)

    def test_devices(self):
        f = eaglecreek.Filter()

        f.devices(ios_channel='1234')
        self.assertEqual(f.filters['devices'], [{'ios_channel': '1234'}])

        f.devices(android_channel=['1234', '5678'])
        self.assertEqual(f.filters['devices'],
            [{'android_channel': '1234'}, {'android_channel': '5678'}])

        f.devices(amazon_channel='1234', named_user_id='fred')
        self.assertEqual(f.filters['devices'],
            [{'amazon_channel': '1234'}, {'named_user_id': 'fred'}])
