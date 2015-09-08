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
