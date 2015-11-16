About
=====

``uaconnect`` is a Python library for using the `Urban Airship Connect
<https://www.urbanairship.com/products/connect>`_ API for streaming mobile
event data to your application.

Requirements
============

Tested on Python 2.7 and 3.5, and should work with 3.3+.

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
