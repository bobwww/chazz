import logging
import select
import socket

import users


class Server:
    logging.basicConfig(level=logging.DEBUG)

    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.server_socket = None
        self.client_sockets = []
        self.socket_user_dict = {}
        self.msgs_to_send = {}
        self.run = False

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.addr, self.port))
        self.server_socket.listen()
        self.run = True
        logging.debug('Server has started successfully.')

    def main_loop(self):
        while self.run:
            rlist, wlist, xlist = select.select([self.server_socket] + self.client_sockets, self.client_sockets, [])

            for current_socket in rlist:
                self.read_messages(current_socket)

            for current_socket in wlist:
                self.send_messages(current_socket)

    def queue_msg(self, msg: str, recipients: tuple, exclude: tuple = None):
        if exclude is None:
            exclude = ()
        msg = msg.encode('utf-8')
        for sock in recipients:
            if sock in exclude:
                continue
            if sock in self.msgs_to_send:
                self.msgs_to_send[sock].append(msg)
            else:
                self.msgs_to_send[sock] = [msg]

    @staticmethod
    def is_chatmsg_valid(msg):
        return msg.isascii()

    def handle_new_connection(self, current_socket):
        conn, addr = current_socket.accept()
        self.client_sockets.append(conn)
        self.socket_user_dict[conn] = users.create_guest()
        logging.debug(
            'A new client connected, addr: {0}, nickname:{1}'.format(addr, self.socket_user_dict[conn].name))
        self.queue_msg('{0} has joined the chat.'.format(self.socket_user_dict[
                                                             conn].name), self.client_sockets)

    def client_disconnected(self, current_socket):
        logging.debug('Client {0}, name {1} has disconnected.'.format(current_socket.getpeername(),
                                                                      self.socket_user_dict[
                                                                          current_socket].name))
        self.client_sockets.remove(current_socket)
        self.msgs_to_send.pop(current_socket, None)
        self.queue_msg('{0} has left the chat.'.format(self.socket_user_dict[
                                                           current_socket].name), self.client_sockets)
        self.socket_user_dict.pop(current_socket, None)

    def read_messages(self, current_socket):
        if current_socket == self.server_socket:
            self.handle_new_connection(current_socket)
        else:
            msg = current_socket.recv(1024)
            if not msg:
                # Client disconnected
                self.client_disconnected(current_socket)
                return
            if self.is_chatmsg_valid(msg):
                msg = msg.decode('utf-8')
            else:
                logging.debug('Message is not valid. Throwing to trash.')
                return

            logging.debug('A new message received: ' + msg)
            msg = self.socket_user_dict[current_socket].name + ' said: ' + msg
            logging.debug('Message after modification: ' + msg)
            self.queue_msg(msg, self.client_sockets, exclude=(current_socket,))

    def send_messages(self, current_socket):
        if current_socket in self.msgs_to_send:
            for msg in self.msgs_to_send[current_socket]:
                logging.debug('Sending message to: ' + self.socket_user_dict[current_socket].name)
                current_socket.sendall(msg)
                self.msgs_to_send[current_socket].remove(msg)


if __name__ == '__main__':
    try:
        server = Server('127.0.0.1', 8050)
        server.start()
        server.main_loop()
    except KeyboardInterrupt:
        print('Interrupted, quiting...')
