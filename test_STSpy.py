#!/usr/bin/env python3

import unittest
import time
from STSpy import Datum, Radio


class DatumTest(unittest.TestCase):
    """Unit tests for the Datum class."""

    @staticmethod
    def create_data():
        """Create a list of STS data that can be written to STS for testing."""

        # Long text data (62*3 bytes)
        text = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' * 3
        timestamp = int(time.time())
        data = [
            Datum.Integer(id=1090, timestamp=timestamp, value=1),
            Datum.Float(id=1091, timestamp=timestamp, value=1.0),
            Datum.Text(id=1092, timestamp=timestamp, value=text),
            Datum.IntegerWithText(id=1093, timestamp=timestamp, value=(1, text)),
            Datum.FloatWithText(id=1094, timestamp=timestamp, value=(1.0, text)),
            Datum.Exponent(id=1095, timestamp=timestamp, value=1.0),
        ]
        return data

    @staticmethod
    def create_ids():
        """Create a list of STS radio IDs that can be read from STS for testing."""

        return [1090, 1091, 1092, 1093, 1094, 1095]

    def test_default_constructor(self):
        """Test the default constructor of the Datum class."""

        datum = Datum()

    def test_factory_methods(self):
        """Test the factory class methods of the Datum class."""

        DatumTest.create_data()


class RadioTest(unittest.TestCase):
    """Unit tests for the Radio class."""

    def test_default_constructor(self):
        """Test the default constructor of the Radio class."""

        radio = Radio()

    def test_pack_method_with_invalid_data_type(self):
        """Test the pack static method with an invalid data type."""

        datum = Datum(id=0, format=6)
        with self.assertRaises(RuntimeError):
            Radio.pack(datum)
    
    def test_unpack_method_with_invalid_packet_size(self):
        """Test the unpack static method with an invalid packet size."""

        packet = Radio.pack(Datum.Integer(id=0, timestamp=0, value=0))
        packet[0:1] = bytes([18 | 0x80])
        with self.assertRaises(RuntimeError):
            Radio.unpack(packet)

    def test_unpack_method_with_invalid_data_type(self):
        """Test the unpack static method with an invalid data type."""

        packet = Radio.pack(Datum.Integer(id=0, timestamp=0, value=0))
        packet[5:6] = bytes([6])
        with self.assertRaises(RuntimeError):
            Radio.unpack(packet)
    
    def test_round_trip(self):
        """Test if data round-trips through the pack and unpack static methods."""

        data = DatumTest.create_data()
        for datum in data:
            Radio.unpack(Radio.pack(datum))

    def test_transmit_method(self):
        """Test the transmit method by actually sending data to STS."""

        radio = Radio()
        data = DatumTest.create_data()
        radio.transmit(data)

    def test_receive_method(self):
        """Test the receive method by actually retrieving the latest data from STS."""

        radio = Radio()
        ids = DatumTest.create_ids()
        data = radio.receive(ids)


if __name__ == '__main__':

    unittest.main()
