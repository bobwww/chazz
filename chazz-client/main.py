import select
import socket
import msvcrt

_input = b''


def user_input():
    global _input

    if msvcrt.kbhit():
        ch = msvcrt.getche()
        if ch == b'\r':
            tmp = _input
            _input = b''
            return tmp
        else:
            _input += ch
            return None


addr = '127.0.0.1'
port = 8050
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((addr, port))
msgs_to_send = []

while True:
    msg = user_input()
    if msg is not None:
        msgs_to_send.append(msg)

    rlist, wlist, xlist = select.select([client_socket], [client_socket], [])

    if rlist:
        msg = client_socket.recv(1024).decode('utf-8')
        print(msg)

    if wlist:
        for msg in msgs_to_send:
            client_socket.sendall(msg)
            msgs_to_send.remove(msg)
