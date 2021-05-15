import select
import socket
import users
import logging

logging.basicConfig(level=logging.DEBUG)
addr = '127.0.0.1'
port = 8050
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((addr, port))
server_socket.listen()
client_sockets_list = []
sockets_users_dict = {}
msgs_to_send = {}  # format: {socket: [msgs],}
logging.debug('Server has started successfully.')


def queue_msg(msg: str, recipients: tuple, exclude: tuple = None):
    if exclude is None:
        exclude = ()
    msg = msg.encode('utf-8')
    for sock in recipients:
        if sock in exclude:
            continue
        if sock in msgs_to_send:
            msgs_to_send[sock].append(msg)
        else:
            msgs_to_send[sock] = [msg]


def is_chat_msg_valid(msg):
    return msg.isascii()
    # allowed_chars = b'0123456789zxcvbnm,.asdfghjkl;qwertyuiop[]" !?-*' + b"'"
    # for ch in msg:
    #     if ch not in allowed_chars:
    #         return False
    # return True


def handle_new_connection(current_socket):
    conn, addr = current_socket.accept()
    client_sockets_list.append(conn)
    sockets_users_dict[conn] = users.create_guest()
    logging.debug(
        'A new client connected, addr: {0}, nickname:{1}'.format(addr, sockets_users_dict[conn].name))
    queue_msg('{0} has joined the chat.'.format(sockets_users_dict[
                                                    conn].name), client_sockets_list)


def client_disconnected(current_socket):
    logging.debug('Client {0}, name {1} has disconnected.'.format(current_socket.getpeername(),
                                                                  sockets_users_dict[
                                                                      current_socket].name))
    client_sockets_list.remove(current_socket)
    msgs_to_send.pop(current_socket, None)
    queue_msg('{0} has left the chat.'.format(sockets_users_dict[
                                                  current_socket].name), client_sockets_list)
    sockets_users_dict.pop(current_socket, None)


def read_messages(current_socket):
    if current_socket == server_socket:
        handle_new_connection(current_socket)
    else:
        msg = current_socket.recv(1024)
        if not msg:
            # Client disconnected
            client_disconnected(current_socket)
            return
        if is_chat_msg_valid(msg):
            msg = msg.decode('utf-8')
        else:
            logging.debug('Message is not valid. Throwing to trash.')
            return

        logging.debug('A new message received: ' + msg)
        msg = sockets_users_dict[current_socket].name + ' said: ' + msg
        logging.debug('Message after modification: ' + msg)
        queue_msg(msg, client_sockets_list, exclude=(current_socket,))


def send_messages(current_socket):
    if current_socket in msgs_to_send:
        for msg in msgs_to_send[current_socket]:
            logging.debug('Sending message to: ' + sockets_users_dict[current_socket].name)
            current_socket.sendall(msg)
            msgs_to_send[current_socket].remove(msg)


def main():
    while True:
        rlist, wlist, xlist = select.select([server_socket] + client_sockets_list, client_sockets_list, [])

        for current_socket in rlist:
            read_messages(current_socket)

        for current_socket in wlist:
            send_messages(current_socket)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted, quiting...')
