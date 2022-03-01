#!/usr/bin/env python3
# BSD 3-Clause License
#
# Copyright (c) 2019 Subaru Telescope
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import pickle
import random
import time
from argparse import ArgumentParser
from datetime import datetime
from logging import basicConfig, getLogger, INFO
from socket import MSG_PEEK
from socketserver import TCPServer, BaseRequestHandler

from STSpy.radio import Radio

alertPath = '/software/ait/alarm/packets.pickle'


def savePacket(packet, filepath=alertPath):
    packets = unPickle(filepath)
    packets.append(packet)
    doPickle(filepath, packets)


def unPickle(filepath):
    try:
        with open(filepath, 'rb') as thisFile:
            unpickler = pickle.Unpickler(thisFile)
            return unpickler.load()
    except EOFError:
        time.sleep(0.1 + random.random())
        return unPickle(filepath=filepath)
    except FileNotFoundError:
        return []


def doPickle(filepath, var):
    with open(filepath, 'wb') as thisFile:
        pickler = pickle.Pickler(thisFile, protocol=2)
        pickler.dump(var)


class RequestHandler(BaseRequestHandler):

    def handle(self):

        logger = getLogger()

        def _recv_packet(sock):

            # 0x80 | len(packet) : binary data packet
            # MSB == 0           : no more data packet
            header = Radio._recvn(sock, 1, MSG_PEEK)
            if not header[0] & 0x80:
                return None
            packet = Radio._recv_packet(sock)
            return packet

        try:
            command = self.request.makefile().readline().strip()
            if command[0] in 'Ww':
                # write command
                self.request.sendall(b'OK: Write On\n')
                while True:
                    packet = _recv_packet(self.request)
                    if not packet:
                        break
                    savePacket(packet)
                    datum = Radio.unpack(packet)
                    logger.info(datum)
            else:
                logger.warning('Command {} not supported'.format(command))
        except Exception as e:
            logger.error(e)
            raise


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('--address', default='127.0.0.1')
    parser.add_argument('--port', default=Radio.PORT)
    parser.add_argument('--log-file',
                        default='/software/ait/logs/STSboard/%s' % datetime.now().strftime('%Y%m%d%H%M%S.log'))
    parser.add_argument('--log-level', default=INFO)
    args, _ = parser.parse_known_args()

    basicConfig(filename=args.log_file, level=args.log_level, format='{asctime:s} [{levelname:s}] {message:s}',
                style='{')
    logger = getLogger()

    with TCPServer((args.address, args.port), RequestHandler) as server:
        server.allow_reuse_address = True
        logger.info('Serving on {}'.format(server.server_address))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
