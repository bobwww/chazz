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


def handle_isadmin(msg=b''):
    msgs_to_send.append(b'ISADMIN\r\n')

def handle_kick(msg=b''):
    msgs_to_send.append(b'KICK\r\n'+msg.split()[1])
addr = '127.0.0.1'
port = 8050
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((addr, port))
msgs_to_send = []


def handle_ban(msg=b''):
    msgs_to_send.append(b'BAN\r\n' + msg.split()[1])


def handle_unban(msg=b''):
    msgs_to_send.append(b'UNBAN\r\n' + msg.split()[1])


def handle_mute(msg=b''):
    msgs_to_send.append(b'MUTE\r\n' + msg.split()[1])

def handle_unmute(msg=b''):
    msgs_to_send.append(b'UNMUTE\r\n' + msg.split()[1])


def handle_private_msg(msg=b''):
    name = msg.split()[1]
    content = msg.split()[2:]
    msgs_to_send.append(b'PRV\r\n' + name + b',' + content)


def handle_op(msg=b''):
    msgs_to_send.append(b'OP\r\n' + msg.split()[1])


def handle_deop(msg=b''):
    msgs_to_send.append(b'DEOP\r\n' + msg.split()[1])

def handle_rename(msg=b''):
    msgs_to_send.append(b'RENAME\r\n' + msg.split()[1])

def handle_find_id(msg=b''):
    msgs_to_send.append(b'IDQUERY\r\n' + msg.split()[1])

cmds = {b'isadmin': handle_isadmin, b'kick': handle_kick, b'mute': handle_mute, b'unmute': handle_unmute,
        b'ban': handle_ban, b'unban': handle_unban,
        b'op':handle_op, b'deop':handle_deop, b'prv':handle_private_msg, b'rename': handle_rename, b'checkid': handle_find_id}

while True:
    msg = user_input()
    if msg is not None:
        print()
        if msg.startswith(b'/'):
            msg = msg[1:]
            cmds.get(msg.split()[0], lambda x: None)(msg)

        else:

            msgs_to_send.append(b'SEND\r\n' + msg)

    rlist, wlist, xlist = select.select([client_socket], [client_socket], [])

    if rlist:
        msg = client_socket.recv(1024)
        if not msg:
            print('Disconnected.')
            break
        msg = msg.decode('utf-8')
        logging.debug('Received message: ' + msg)
        print(msg)

    if wlist:
        for msg in msgs_to_send:
            logging.debug('Sending message: ' + repr(msg))
            client_socket.sendall(msg)
            msgs_to_send.remove(msg)
