"""Airship RTDS offset recorder

Used to maintain the current state of the stream.

"""
import abc
import os


class Recorder(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def read_offset(self):
        """Read the last saved event offset."""
        raise NotImplementedError

    @abc.abstractmethod
    def write_offset(self, offset):
        """Write the given offset as the last acknolwedged event."""
        raise NotImplementedError


class FileRecorder(Recorder):
    filename: str

    def __init__(self, filename: str):
        super(FileRecorder, self).__init__()
        self.filename = filename

    def read_offset(self):
        if os.path.exists(self.filename):
            f = open(self.filename, "r")
            offset = f.read().strip()
        else:
            offset = None
        return offset

    def write_offset(self, offset: str):
        f = open(self.filename, "w")
        f.write(offset)
        f.close()
