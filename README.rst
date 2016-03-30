About
=====

``uaconnect`` is a Python library for using the `Urban Airship Connect
<https://www.urbanairship.com/products/connect>`_ API for streaming mobile
event data to your application.

Requirements
============

Tested on Python 2.7 and 3.5, and should work with 3.3+.

For tests, ``uaconnect`` also needs `Mock <https://github.com/testing-cabal/mock>`_.

Running Tests
=============

To run tests, run:

    $ python -m unittest discover

Usage
=====

See the `Connect Getting Started Guide
<http://docs.urbanairship.com/topic-guides/connect-getting-started.html>`_, as
well as the `Connect API
<http://docs.urbanairship.com/topic-guides/connect-api.html>`_ for more
details.

Basic usage
-----------

To use the library, instantiate a ``Consumer`` object with the application key,
access token, and an offset recorder. You can then open the connection, and
start reading events.

    >>> import uaconnect
    >>> consumer = uaconnect.Consumer(
    ...     'application_key', 'access_token',
    ...     uaconnect.FileRecorder('.offset'))
    >>> consumer.connect()
    >>> for event in consumer.read():
    ...     if event is None:
    ...        continue
    >>>     print("Got event: {}".format(event))
    >>>     consumer.ack(event)


Offset recorders
----------------

Offset recorders inherit from the abstract base class ``uaconnect.Recorder``,
implementing ``read_offset`` and ``write_offset`` methods. One recorder is included
in the library, ``FileRecorder``, which stores the offest on disk. In the
``uaconnect.ext.redisrecorder`` package there is an example implementation of
using an Redis instance to store the offset.

`ack` calls should be placed depending on whether in a failure scenario your
app wishes to possibly replay an already handled event, or risk dropping one.
For the latter, call ``ack`` as soon as the event is read; for the former, call
``ack`` only after the event has been fully handled.

Advanced options when connecting
================================

Urban Airship Connect supports a variety of `options when connecting
<http://docs.urbanairship.com/api/connect.html#stream-object>`_ to make sure
that you're only consuming the data that you want. ``uaconnect`` makes it easy
to use these connection parameters and filters.

Specifying offsets
------------------

One of the advantages of Urban Airship Connect is that you can resume from a
specific place in the Connect stream. This is done by specifying the ``offset``
that's associated with the event. While ``uaconnect`` automatically tracks
offsets for you with ``uaconnect.FileRecorder``, you can also explicitly set an
offset.

    >>> import uaconnect
    >>> recorder = uaconnect.FileRecorder(".offset") # or wherever you would like the file to exist
    >>> recorder.write_offset("8865499359") # a randomly chosen offset
    >>> recorder.read_offset()
    '8865499359'

An alternative here is to just write the offset explicitly into the file, or
whatever ``Recorder`` subclass you're using to track offsets.

    $ cat .offset
    886549935

Now, the next time you connect, it will pick up from that last offset.

Using filters
-------------

Filters are a powerful way of filtering what specific information you'd like to
see from the Connect stream. You can filter by event type, device type, latency
on an event, or even specific devices or notifications.

For a complete list of filters, and their descriptions, check out `the
documentation <http://docs.urbanairship.com/api/connect.html#stream-object>`_.

Here's a brief example on how to use filters with ``uaconnect``:

    >>> import uaconnect
    >>> consumer = uaconnect.Consumer(
    ...     'application_key', 'access_token',
    ...     uaconnect.FileRecorder('.offset'))
    >>> f = uaconnect.Filter()
    >>> f.types("PUSH_BODY", "SEND") # only receive PUSH_BODY and SEND events.
    >>> consumer.add_filter(f)
    >>> consumer.connect()
