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


def queue_msg_to_send(sock, msg):
    msg = msg.encode('utf-8')
    if sock in msgs_to_send:
        msgs_to_send[sock].append(msg)
    else:
        msgs_to_send[sock] = [msg]

def queue_msg_to_send_all(msg, sender=None):
    for sock in client_sockets_list:
        if not sock == sender:
            logging.debug('Queueing message to: ' + sockets_users_dict[sock].name)
            queue_msg_to_send(sock, msg)


def main():
    while True:
        rlist, wlist, xlist = select.select([server_socket] + client_sockets_list, client_sockets_list, [])
        for current_socket in rlist:
            if current_socket == server_socket:
                conn, addr = current_socket.accept()
                client_sockets_list.append(conn)
                sockets_users_dict[conn] = users.create_guest()
                logging.debug(
                    'A new client connected, addr: {0}, nickname:{1}'.format(addr, sockets_users_dict[conn].name))
                queue_msg_to_send_all('{0} has joined the chat.'.format(sockets_users_dict[
                                                                          conn].name))
            else:
                msg = current_socket.recv(1024)
                if not msg:
                    # Client disconnected
                    logging.debug('Client {0}, name {1} has disconnected.'.format(current_socket.getpeername(),
                                                                                  sockets_users_dict[
                                                                                      current_socket].name))
                    client_sockets_list.remove(current_socket)
                    msgs_to_send.pop(current_socket, None)
                    queue_msg_to_send_all('{0} has left the chat.'.format(sockets_users_dict[
                                                                                      current_socket].name))
                    sockets_users_dict.pop(current_socket, None)
                    continue
                if msg.isalnum():
                    msg = msg.decode('utf-8')
                else:
                    logging.debug('Message is not valid. Throwing to trash.')
                    continue

                logging.debug('A new message received: ' + msg)
                msg = sockets_users_dict[current_socket].name + ' said: ' + msg
                logging.debug('Message after modification: ' + msg)
                queue_msg_to_send_all(msg, sender=current_socket)

        for current_socket in wlist:
            if current_socket in msgs_to_send:
                for msg in msgs_to_send[current_socket]:
                    logging.debug('Sending message to: ' + sockets_users_dict[current_socket].name)
                    current_socket.sendall(msg)
                    msgs_to_send[current_socket].remove(msg)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted, quiting...')
