class Filter(object):
    def __init__(self):
        self.filters = {}

    def device_types(self, *types):
        """Filter by device type.

        Valid device types are "ios", "android", and "amazon".

        """
        if not types:
            raise ValueError("Must specify at least one device type")
        for t in types:
            if t not in ('ios', 'android', 'amazon'):
                raise ValueError("Invalid device type '%s'" % t)
        self.filters['device_types'] = list(types)

    def types(self, *types):
        """Filter by event type.

        See the Connect documentation for a list of valid event types. Examples
        include "PUSH_BODY", "OPEN", and "CLOSE".

        """
        if not types:
            raise ValueError("Must specify at least one event type")
        # The API expects event types to be uppercase.
        self.filters['types'] = list(t.upper() for t in types)
