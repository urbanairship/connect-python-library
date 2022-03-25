About
=====

``uaconnect`` is the official Python library for using the `Airship Real-Time Data Streaming
<https://docs.airship.com/api/connect/>`_ API (formerly known as Connect).

Questions
=========

The best place to ask questions or report a problem is our support site:
http://support.airship.com/

Requirements
============

Tested on Python 3.6, 3.7, 3.8, and 3.9.

For tests, ``uaconnect`` also needs `Mock <https://github.com/testing-cabal/mock>`_.

Running Tests
=============

To run tests, run:

    $ python -m unittest discover

Usage
======

See the `Real-Time Data Streaming Getting Started Guide
<https://docs.airship.com/tutorials/getting-started/data-streaming/>`_, as
well as the `Real-Time Data Streaming API docs
<https://docs.airship.com/api/connect/>`_ for more details.

RTDS Event Consumer
-------------------

To consume standard events from the RTDS API, instantiate a ``EventConsumer`` object
with the application key, access token, and an offset recorder. You can then open the
connection, and start reading events.

See more about the RTDS Event Stream
`in our documentation here <https://docs.airship.com/api/connect/#tag-event-stream>`_.

    >>> import uaconnect
    >>> consumer = uaconnect.EventConsumer(
    ...     app_key='application_key',
    ...     access_token='access_token',
    ...     recorder=uaconnect.FileRecorder('.offset'))
    >>> consumer.connect()
    >>> for event in consumer.read():
    ...     if event is None:
    ...        continue
    >>>     print("Got event: {}".format(event))
    >>>     consumer.ack(event)


RTDS Compliance Event Consumer
------------------------------

To consume compliance events from the RTDS API, instantiate a ``ComplianceConsumer`` object
with the application key, master secret and an offset recorder. You can then open the
connection, and start reading events.

See more about the RTDS Compliance Event Stream
`in the documentation here <https://docs.airship.com/api/connect/#tag-compliance-event-stream>`_.

    >>> import uaconnect
    >>> consumer = uaconnect.EventConsumer(
    ...     app_key='application_key',
    ...     master_secret='master_secret',
    ...     recorder=uaconnect.FileRecorder('.offset'))
    >>> consumer.connect()
    >>> for event in consumer.read():
    ...     if event is None:
    ...        continue
    >>>     print("Got event: {}".format(event))
    >>>     consumer.ack(event)


Alternate Data Center Support
------------------------------

When instantiating a ``EventConsumer`` or ``ComplianceConsumer`` you can pass the optional
`url` argument to explicitly specify the data center your project is located in. Possible
values are "US", "EU", or an arbitrary base url in the form of `http://domain.xyz/`. The
library will build the URL path properly from there. If no `url` is specified, "US" is used.

    >>> import uaconnect
    >>> consumer = uaconnect.EventConsumer(
    ...     app_key='application_key',
    ...     master_secret='master_secret',
    ...     url='EU',
    ...     recorder=uaconnect.FileRecorder('.offset'))


Offset recorders
----------------

Offset recorders inherit from the abstract base class ``uaconnect.Recorder``,
implementing ``read_offset`` and ``write_offset`` methods. One recorder is
included in the library, ``FileRecorder``, which stores the offset on disk. In
the ``uaconnect.ext.redisrecorder`` package there is an example implementation
of using an Redis instance to store the offset.

`ack` calls should be placed depending on whether in a failure scenario your
app wishes to possibly replay an already handled event, or risk dropping one.
For the latter, call ``ack`` as soon as the event is read; for the former, call
``ack`` only after the event has been fully handled.

Advanced options when connecting
================================

Airship Real-Time Data Streaming supports a variety of `options when connecting
<https://docs.airship.com/api/connect/#operation/api/events/post/requestbody>`_
to make sure that you're only consuming the data that you want. ``uaconnect``
makes it easy to use these connection parameters and filters.

Specifying offsets
------------------

One of the advantages of Airship Real-Time Data Streaming is that you can resume from a
specific place in the RTDS stream. This is done by specifying the ``offset``
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

If you'd like to manually set the offset for a connection to a known value
instead of the recorder's offset, set ``resume_offset`` like so:

    >>> consumer.connect(resume_offset='123456789')

Using filters
-------------

Filters are a powerful way of filtering what specific information you'd like to
see from the RTDS stream. You can filter by event type, device type, latency
on an event, or even specific devices or notifications.

For a complete list of filters, and their descriptions, check out `the
documentation <https://docs.airship.com/api/connect/#schemas/filters>`_.

Here's a brief example on how to use filters with ``uaconnect``:

    >>> import uaconnect
    >>> consumer = uaconnect.EventConsumer(
    ...     app_key='application_key',
    ...     access_token='access_token',
    ...     recorder=uaconnect.FileRecorder('.offset')
    ...     )
    >>> f = uaconnect.Filter()
    >>> f.types("PUSH_BODY", "SEND") # only receive PUSH_BODY and SEND events.
    >>> consumer.add_filter(f)
    >>> consumer.connect()
