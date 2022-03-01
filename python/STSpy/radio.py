###############################################################################
# Copyright (c) 2018 Subaru Telescope
###############################################################################
import socket
import struct
from . import Datum


class Radio(object):
    """A class to communicate with the STS board (STS radio)."""

    # Default STS server IP address and STS board TCP port number
    HOST = 'localhost'
    PORT = 9001

    # Default timeout (seconds)
    TIMEOUT = 5.0

    def __init__(self, host=HOST, port=PORT, timeout=TIMEOUT):
        """Create a Radio object.

           Arguments
               host: Domain name or IP address of the STS server
               port: TCP port number that the STS board listens to
               timeout: Network socket timeout in seconds
        """

        self.host = host
        self.port = port
        self.timeout = timeout

    def __repr__(self):

        return '{}(host={}, port={}, timeout={})'.format(
            self.__class__.__name__, repr(self.host), repr(self.port), repr(self.timeout)
        )

    def transmit(self, data):
        """Send STS data to the STS board.

           Argument
               data: Sequence of Datum objects

           Result
               None
        """

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            # Enter in binary write mode
            sock.sendall(b'W\n')
            response = sock.makefile().readline()
            if 'OK: Write On' in response:
                for datum in data:
                    packet = Radio.pack(datum)
                    sock.sendall(packet)
                # Exit from binary write mode
                sock.sendall(b'\n')
                response = sock.makefile().readline()
                if 'OK: Write Off' in response:
                    # Send quit command to disconnect from STSboard gracefully
                    sock.sendall(b'Q\n')
            else:
                raise RuntimeError('Invalid response')
        finally:
            sock.close()

    def receive(self, ids):
        """Retrieve latest STS data from the STS board.

           Argument
               ids: Sequence of STS radio IDs

           Result
               List of Datum objects
        """

        data = []
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            # Enter in binary read mode
            sock.sendall(b'R\n')
            response = sock.makefile().readline()
            if 'OK: Read On' in response:
                for id in ids:
                    message = struct.pack('!I', int(id))
                    sock.sendall(message)
                    response = Radio._recv_packet(sock)
                    datum = Radio.unpack(response)
                    data.append(datum)
                # Exit from binary read mode
                message = struct.pack('!i', -1)
                sock.sendall(message)
                # response = sock.makefile().readline()
                # # NB: STSboard does send the following message at the end of binary read
                # if 'OK: Write Off' in response:
                #     # Send quit command to disconnect from STSboard gracefully
                #     sock.sendall(b'Q\n')
            else:
                raise RuntimeError('Invalid response')
        finally:
            sock.close()
        return data

    # Format strings used by the struct module to pack/unpack STS board binary data
    _HEADER_FORMAT = '!BIBI'
    _INTEGER_FORMAT = '!i'
    _FLOAT_FORMAT = '!d'

    # Size of each STS board binary data components
    _HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)
    _INTEGER_SIZE = struct.calcsize(_INTEGER_FORMAT)
    _FLOAT_SIZE = struct.calcsize(_FLOAT_FORMAT)

    # Maximum value that can be stored in a 7-bit field in the STS board binary data header
    _MAXIMUM_PACKET_SIZE = 127

    @staticmethod
    def pack(datum):
        """Create STS board binary data from a Datum object."""

        def pack_header(packet, size):

            struct.pack_into(
                Radio._HEADER_FORMAT, packet, 0,
                size | 0x80, datum.id, datum.format, datum.timestamp
            )

        def pack_integer(packet, offset, number):

            struct.pack_into(Radio._INTEGER_FORMAT, packet, offset, int(number))

        def pack_float(packet, offset, number):

            struct.pack_into(Radio._FLOAT_FORMAT, packet, offset, float(number))

        def pack_text(packet, offset, text):

            packet[offset:] = text.encode('latin-1')[:Radio._MAXIMUM_PACKET_SIZE - offset]

        if datum.format == Datum.INTEGER:
            size = Radio._HEADER_SIZE + Radio._INTEGER_SIZE
            packet = bytearray(size)
            pack_header(packet, size)
            pack_integer(packet, Radio._HEADER_SIZE, datum.value)
        elif datum.format == Datum.FLOAT or datum.format == Datum.EXPONENT:
            size = Radio._HEADER_SIZE + Radio._FLOAT_SIZE
            packet = bytearray(size)
            pack_header(packet, size)
            pack_float(packet, Radio._HEADER_SIZE, datum.value)
        elif datum.format == Datum.TEXT:
            size = min(Radio._HEADER_SIZE + len(datum.value), Radio._MAXIMUM_PACKET_SIZE)
            packet = bytearray(size)
            pack_header(packet, size)
            pack_text(packet, Radio._HEADER_SIZE, datum.value)
        elif datum.format == Datum.INTEGER_WITH_TEXT:
            size = min(
                Radio._HEADER_SIZE + Radio._INTEGER_SIZE + len(datum.value[1]),
                Radio._MAXIMUM_PACKET_SIZE
            )
            packet = bytearray(size)
            pack_header(packet, size)
            pack_integer(packet, Radio._HEADER_SIZE, datum.value[0])
            pack_text(packet, Radio._HEADER_SIZE + Radio._INTEGER_SIZE, datum.value[1])
        elif datum.format == Datum.FLOAT_WITH_TEXT:
            size = min(
                Radio._HEADER_SIZE + Radio._FLOAT_SIZE + len(datum.value[1]),
                Radio._MAXIMUM_PACKET_SIZE
            )
            packet = bytearray(size)
            pack_header(packet, size)
            pack_float(packet, Radio._HEADER_SIZE, datum.value[0])
            pack_text(packet, Radio._HEADER_SIZE + Radio._FLOAT_SIZE, datum.value[1])
        else:
            raise RuntimeError('Invalid data type ({})'.format(datum.format))
        return packet

    @staticmethod
    def unpack(packet):
        """Create a Datum object from STS board binary data."""

        def unpack_header():

            return struct.unpack_from(Radio._HEADER_FORMAT, packet, 0)

        def unpack_integer(offset):

            return struct.unpack_from(Radio._INTEGER_FORMAT, packet, offset)[0]

        def unpack_float(offset):

            return struct.unpack_from(Radio._FLOAT_FORMAT, packet, offset)[0]

        def unpack_text(offset, size):

            return packet[offset:size].decode('latin-1')

        datum = Datum()
        size, datum.id, datum.format, datum.timestamp = unpack_header()
        if not size & 0x80:
            raise RuntimeError('Invalid packet header ({})'.format(size))
        size &= ~0x80
        if size != len(packet):
            raise RuntimeError('Invalid packet size ({})'.format(len(packet)))
        if datum.format == Datum.INTEGER:
            datum.value = unpack_integer(Radio._HEADER_SIZE)
        elif datum.format == Datum.FLOAT or datum.format == Datum.EXPONENT:
            datum.value = unpack_float(Radio._HEADER_SIZE)
        elif datum.format == Datum.TEXT:
            datum.value = unpack_text(Radio._HEADER_SIZE, size)
        elif datum.format == Datum.INTEGER_WITH_TEXT:
            datum.value = (
                unpack_integer(Radio._HEADER_SIZE),
                unpack_text(Radio._HEADER_SIZE + Radio._INTEGER_SIZE, size)
            )
        elif datum.format == Datum.FLOAT_WITH_TEXT:
            datum.value = (
                unpack_float(Radio._HEADER_SIZE),
                unpack_text(Radio._HEADER_SIZE + Radio._FLOAT_SIZE, size)
            )
        else:
            raise RuntimeError('Invalid data type ({})'.format(datum.format))
        return datum

    @staticmethod
    def _recv_packet(sock):
        """Receive STS board binary data from a socket 'sock'."""

        header = Radio._recvn(sock, 1, socket.MSG_PEEK)
        size = struct.unpack(Radio._HEADER_FORMAT[:2], header)[0] & ~0x80
        return Radio._recvn(sock, size)

    @staticmethod
    def _recvn(sock, size, flags=0):
        """Receive exactly 'size' bytes from a socket 'sock'."""

        buffer = bytearray(size)
        offset = 0
        while offset < size:
            buffer_ = sock.recv(size - offset, flags)
            size_ = len(buffer_)
            if not size_:
                raise RuntimeError('Connection closed by peer')
            buffer[offset:offset + size_] = buffer_
            offset += size_
        return buffer
