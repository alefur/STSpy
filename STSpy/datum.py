###############################################################################
# Copyright (c) 2018 Subaru Telescope
###############################################################################


class Datum(object):
    """A class to represent STS *datum*."""

    # Data types (formats)
    INTEGER = 0
    FLOAT = 1
    TEXT = 2
    INTEGER_WITH_TEXT = 3
    FLOAT_WITH_TEXT = 4
    EXPONENT = 5  # Like FLOAT but may be presented differently on the STS web pages

    def __init__(self, id=None, format=0, timestamp=0, value=0):
        """Create a Datum object.

           Arguments
               id: STS radio ID
               format: Data type (format)
               timestamp: Timestamp in seconds since Unix epoch
               value: Data value
        """

        self.id = id
        self.format = format
        self.timestamp = timestamp
        self.value = value

    def __repr__(self):

        return '{}(id={}, format={}, timestamp={}, value={})'.format(
            self.__class__.__name__,
            repr(self.id), repr(self.format), repr(self.timestamp), repr(self.value)
        )

    @classmethod
    def Integer(cls, id=None, timestamp=0, value=0):
        """A factory method to create a Datum object with INTEGER data."""

        return cls(id=id, format=Datum.INTEGER, timestamp=timestamp, value=value)

    @classmethod
    def Float(cls, id=None, timestamp=0, value=0.0):
        """A factory method to create a Datum object with FLOAT data."""

        return cls(id=id, format=Datum.FLOAT, timestamp=timestamp, value=value)

    @classmethod
    def Text(cls, id=None, timestamp=0, value=''):
        """A factory method to create a Datum object with TEXT data."""

        return cls(id=id, format=Datum.TEXT, timestamp=timestamp, value=value)

    @classmethod
    def IntegerWithText(cls, id=None, timestamp=0, value=(0, '')):
        """A factory method to create a Datum object with INTEGER and TEXT data."""

        return cls(id=id, format=Datum.INTEGER_WITH_TEXT, timestamp=timestamp, value=value)

    @classmethod
    def FloatWithText(cls, id=None, timestamp=0, value=(0.0, '')):
        """A factory method to create a Datum object with FLOAT and TEXT data."""

        return cls(id=id, format=Datum.FLOAT_WITH_TEXT, timestamp=timestamp, value=value)

    @classmethod
    def Exponent(cls, id=None, timestamp=0, value=0.0):
        """A factory method to create a Datum object with EXPONENT data."""

        return cls(id=id, format=Datum.EXPONENT, timestamp=timestamp, value=value)
