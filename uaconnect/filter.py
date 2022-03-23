from typing import Dict


class Filter(object):
    def __init__(self):
        self.filters: Dict = {}

    def device_types(self, *types) -> None:
        """Filter by device type.

        Valid device types are "ios", "android", "amazon", "sms", "email", "web", and "open".

        """
        if not types:
            raise ValueError("Must specify at least one device type")
        for t in types:
            if t not in ("ios", "android", "amazon", "sms", "email", "web", "open"):
                raise ValueError("Invalid device type '%s'" % t)
        self.filters["device_types"] = list(types)

    def types(self, *types) -> None:
        """Filter by event type.

        See the Connect documentation for a list of valid event types. Examples
        include "PUSH_BODY", "OPEN", and "CLOSE".

        """
        if not types:
            raise ValueError("Must specify at least one event type")
        # The API expects event types to be uppercase.
        self.filters["types"] = list(t.upper() for t in types)

    def latency(self, threshold: str) -> None:
        """Filter out events that are more than `threshold` ms latent.

        Latency is measured as the time between the event occurrence and when
        the event was processed.

        """
        self.filters["latency"] = threshold

    def notifications(self, push_id: str = None, group_id: str = None) -> None:
        if (not push_id and not group_id) or (push_id and group_id):
            raise ValueError(
                "Either push_id or group_id must be specified in "
                "notifications filter."
            )
        if push_id:
            self.filters["notifications"] = {"push_id": push_id}
        else:
            self.filters["notifications"] = {"group_id": group_id}

    def devices(
        self,
        channel: str = None,
        ios_channel: str = None,
        android_channel: str = None,
        amazon_channel: str = None,
        named_user_id: str = None,
    ):
        """Include events that are for this channel or named user.

        Unlike the other filters, this can handle multiple options, so multiple
        options can be used with either a single string or a sequence, e.g.:

        >>> filter_.devices(ios_channel='73757eeb-54cc-4337-84d7-484046e9f607')
        >>> filter_.devices(channel='73757eeb-54cc-4337-84d7-484046e9f607')
        >>> filter_.devices(android_channel=[
        ...     '73757eeb-54cc-4337-84d7-484046e9f607',
        ...     'c76874b5-2e35-483b-a3a0-e05265f94260'])
        >>> filter_.devices(
        ...     ios_channel='73757eeb-54cc-4337-84d7-484046e9f607',
        ...     android_channel='c76874b5-2e35-483b-a3a0-e05265f94260')

        """
        if not (
            ios_channel or android_channel or amazon_channel or named_user_id or channel
        ):
            raise ValueError("Must specify at least one device ID")

        devices = []

        if isinstance(channel, str):
            devices.append({"channel": channel})
        elif channel:
            devices.extend({"channel": c} for c in channel)

        if isinstance(ios_channel, str):
            devices.append({"ios_channel": ios_channel})
        elif ios_channel:
            devices.extend({"ios_channel": c} for c in ios_channel)

        if isinstance(android_channel, str):
            devices.append({"android_channel": android_channel})
        elif android_channel:
            devices.extend({"android_channel": c} for c in android_channel)

        if isinstance(amazon_channel, str):
            devices.append({"amazon_channel": amazon_channel})
        elif amazon_channel:
            devices.extend({"amazon_channel": c} for c in amazon_channel)

        if isinstance(named_user_id, str):
            devices.append({"named_user_id": named_user_id})
        elif named_user_id:
            devices.extend({"named_user_id": c} for c in named_user_id)

        self.filters["devices"] = devices
