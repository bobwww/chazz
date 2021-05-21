import select
import socket
import msvcrt
import logging

_input = b''
logging.basicConfig(level=logging.INFO)


def user_input():
    global _input

    if msvcrt.kbhit():
        ch = msvcrt.getche()
        if ch == b'\r':
            tmp = _input
            logging.debug('Input:' + repr(tmp))
            _input = b''
            return tmp
        elif ch == b'\x08':
            _input = _input[:-1]
        else:
            _input += ch
            return None
    else:
        return None


addr = '127.0.0.1'
port = 8050
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((addr, port))
msgs_to_send = []

while True:
    msg = user_input()
    if msg is not None:
        print()
        msgs_to_send.append(b'SEND\r\n'+msg)

    rlist, wlist, xlist = select.select([client_socket], [client_socket], [])

    if rlist:
        msg = client_socket.recv(1024).decode('utf-8')
        logging.debug('Received message: ' + msg)
        print(msg)

    if wlist:
        for msg in msgs_to_send:
            logging.debug('Sending message: ' + repr(msg))
            client_socket.sendall(msg)
            msgs_to_send.remove(msg)
