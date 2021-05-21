import logging
import select
import socket
import random

import users
import chats


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
        self.chat_list = [chats.Chat(1, 'MyFirstChat'), chats.Chat(2, 'MySecondChat')]
        self.user_chat_dict = {}

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.addr, self.port))
        self.server_socket.listen()
        self.run = True
        logging.debug('Server has started successfully.')

    def stop(self):
        self.run = False

    def close(self):
        for sock in self.client_sockets:
            sock.close()
        self.server_socket.close()

    def main_loop(self):
        while self.run:
            rlist, wlist, xlist = select.select([self.server_socket] + self.client_sockets, self.client_sockets, [])

            for current_socket in rlist:
                self.read_messages(current_socket)

            for current_socket in wlist:
                self.send_messages(current_socket)
        # After while
        self.close()

    def queue_msg(self, msg: str, recipients: tuple, exclude: tuple = None):
        logging.debug('Queueing msg: ' + repr(msg))
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
        user = users.create_guest()
        self.socket_user_dict[conn] = user
        chat = random.choice(self.chat_list)
        chat.add_participant(self.socket_user_dict[conn])
        self.user_chat_dict[user] = chat
        logging.debug(
            'A new client connected, addr: {0}, nickname:{1}'.format(addr, self.socket_user_dict[conn].name))
        self.queue_msg('You have joined {0}'.format(chat.name), (conn,))
        self.queue_msg('{0} has joined the chat.'.format(self.socket_user_dict[
                                                             conn].name), self.users_to_sockets(chat.participants))

    def client_disconnected(self, current_socket):
        logging.debug('Client {0}, name {1} has disconnected.'.format(current_socket.getpeername(),
                                                                      self.socket_user_dict[
                                                                          current_socket].name))
        user = self.socket_user_dict[current_socket]
        chat = self.user_chat_dict[user]
        self.client_sockets.remove(current_socket)
        self.msgs_to_send.pop(current_socket, None)
        self.user_chat_dict[user].remove_participant(user)
        self.queue_msg('{0} has left the chat.'.format(self.socket_user_dict[
                                                           current_socket].name),
                       self.users_to_sockets(chat.participants))

        self.user_chat_dict.pop(user)
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
            # msg = self.socket_user_dict[current_socket].name + ' said: ' + msg
            user = self.socket_user_dict[current_socket]
            msg, recipients = self.user_chat_dict[user].handle_new_msg(msg, user)
            logging.debug('Message after modification: ' + msg)
            recipients = self.users_to_sockets(recipients)
            self.queue_msg(msg, recipients, exclude=(current_socket,))

    def send_messages(self, current_socket):
        if current_socket in self.msgs_to_send:
            for msg in self.msgs_to_send[current_socket]:
                logging.debug('Sending message to: ' + self.socket_user_dict[current_socket].name)
                current_socket.sendall(msg)
                self.msgs_to_send[current_socket].remove(msg)

    def sockets_to_users(self, socks: tuple):
        return [self.socket_user_dict.get(sock, None) for sock in socks]

    def users_to_sockets(self, users: tuple):
        keys = tuple(self.socket_user_dict.keys())
        values = tuple(self.socket_user_dict.values())
        res = []
        for user in users:
            user_i = values.index(user)
            res.append(keys[user_i])
        return res


if __name__ == '__main__':
    try:
        server = Server('127.0.0.1', 8050)
        server.start()
        server.main_loop()
    except KeyboardInterrupt:
        print('Interrupted, quiting...')
