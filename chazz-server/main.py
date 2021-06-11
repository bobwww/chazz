import logging
import select
import socket
import random

import users
import chats
from netproto import *

chat_list = ['Coffee', 'Banana']

def admin_command(f):

    def inside(_, user, args):
        if not user.is_admin():
            logging.warning(f'{user.name} has no perm to do cmd.')
            return
        f(user, args)

    return inside


class Server:
    logging.basicConfig(level=logging.DEBUG)

    def __init__(self, addr, port, max_connections):
        self.addr = addr
        self.port = port
        self.server_socket = None
        self.client_sockets = []
        self.socket_user_dict = {}
        self.msgs_to_send = {}
        self.run = False
        self.banned_addresses = []
        self.user_chat_dict = {}
        self.chat_list = [chats.Chat(i, chat) for i, chat in enumerate(chat_list)]
        self.max_connections = max_connections
        self.request_func_dict = {Protocol.SEND_MSG: self.handle_chat_msg,
                                  Protocol.CHECK_ADMIN: self.handle_check_admin,
                                  Protocol.KICK: self.handle_kick,
                                  Protocol.MUTE: self.handle_mute,
                                  Protocol.UNMUTE: self.handle_unmute,
                                  Protocol.BAN: self.handle_ban,
                                  Protocol.UNBAN: self.handle_unban,
                                  Protocol.OP: self.handle_op,
                                  Protocol.DEOP: self.handle_deop,
                                  Protocol.PRIVATE_MSG: self.handle_private_msg,
                                  Protocol.RENAME: self.handle_rename,
                                  Protocol.FIND_ID: self.handle_id_query}

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.addr, self.port))
        self.server_socket.listen()
        self.run = True
        logging.info('Server has started successfully.')

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
        if addr[0] in self.banned_addresses or len(self.client_sockets) >= self.max_connections:
            conn.close()
            return
        self.client_sockets.append(conn)
        user = users.create_guest(self.users)
        self.socket_user_dict[conn] = user
        chat = random.choice(self.chat_list)
        chat.add_participant(user)
        if len(chat.participants) == 1:
            user.admin = True
        self.user_chat_dict[user] = chat
        logging.debug(
            'A new client connected, addr: {0}, nickname:{1}'.format(addr, self.socket_user_dict[conn].name))
        self.queue_msg('You have joined {0}'.format(chat.name), (conn,))
        self.queue_msg('{0} has joined the chat.'.format(self.socket_user_dict[
                                                             conn].name), self.users_to_sockets(chat.participants))

    def client_disconnected(self, current_socket):
        logging.debug('Client {0}, name {1} has disconnected.'.format(current_socket.getpeername()[0],
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
        current_socket.close()
        self.user_chat_dict.pop(user)
        self.socket_user_dict.pop(current_socket, None)
        if user.is_admin():
            if not chat.is_any_admin() and len(chat.participants) > 0:
                chat.get_oldest_user().set_admin(True)

    def read_messages(self, current_socket):
        if current_socket == self.server_socket:
            self.handle_new_connection(current_socket)
        else:
            msg = current_socket.recv(1024)
            if not msg:
                # Client disconnected
                self.client_disconnected(current_socket)
                return

            msg = Protocol.parse(msg)
            if msg:
                logging.debug('A new message received: ' + msg.code + '|' + msg.args)
                user = self.socket_user_dict[current_socket]

                self.request_func_dict.get(msg.code)(user, msg.args)
                # try:
                #     user = self.socket_user_dict[current_socket]
                #     self.request_func_dict.get(msg.code)(user, msg.args)
                # except Exception as e:
                #     logging.error('An exception has occured: '+repr(e))
            # msg = self.socket_user_dict[current_socket].name + ' said: ' + msg
            # user = self.socket_user_dict[current_socket]
            # msg, recipients = self.user_chat_dict[user].handle_new_msg(msg, user)
            # logging.debug('Message after modification: ' + msg)
            # recipients = self.users_to_sockets(recipients)
            # self.queue_msg(msg, recipients, exclude=(current_socket,))

    def send_messages(self, current_socket):
        if current_socket in self.msgs_to_send:
            for msg in self.msgs_to_send[current_socket]:
                logging.debug('Sending message to: ' + self.socket_user_dict[current_socket].name)
                current_socket.sendall(msg)
                self.msgs_to_send[current_socket].remove(msg)

    def handle_chat_msg(self, user, content):
        if not self.is_chatmsg_valid(content):
            logging.debug('Message is not valid. Throwing to trash.')
            return
        if user.is_muted():
            logging.debug('User is muted. Throwing to trash.')
            return
        msg, recipients = self.user_chat_dict[user].handle_new_msg(content, user)
        logging.debug('Message after modification: ' + msg)
        recipients = self.users_to_sockets(recipients)
        self.queue_msg(msg, recipients, exclude=tuple(self.users_to_sockets((user,))))

    def handle_check_admin(self, user, args):
        if user.is_admin():
            msg = 'You are admin'
        else:
            msg = 'You are not admin'
        self.queue_msg(msg, tuple(self.users_to_sockets((user,))))

    def handle_id_query(self, user, args):
        target = users.name_to_user(args, self.users)
        if target:
            msg = '[SYSTEM]ID of ' + target.name + ' is '+ str(target.uid)
        else:
            msg = 'User not found'
        self.queue_msg(msg, tuple(self.users_to_sockets((user,))))

    @admin_command
    def handle_kick(self, user, args):
        user = users.name_to_user(args, self.users)
        target_sock = self.users_to_sockets((user,))[0]
        self.client_disconnected(target_sock)

    @admin_command
    def handle_ban(self, user, args):
        user = users.name_to_user(args, self.users)
        target_sock = self.users_to_sockets((user,))[0]
        self.banned_addresses.append(target_sock.getpeername()[0])
        self.client_disconnected(target_sock)

    @admin_command
    def handle_unban(self, user, args):
        self.banned_addresses.remove(args)

    @admin_command
    def handle_mute(self, user, args):
        user = users.name_to_user(args, self.users)
        user.muted = True

    @admin_command
    def handle_unmute(self, user, args):
        user = users.name_to_user(args, self.users)
        user.muted = False

    def handle_private_msg(self, user, args):
        target_name, content = args.split(',')
        print(target_name, content)
        user = users.name_to_user(target_name, self.users)
        target_sock = self.users_to_sockets((user,))[0]
        self.queue_msg(content, (target_sock,))

    @admin_command
    def handle_op(self, user, args):
        user = users.name_to_user(args, self.users)
        user.admin = True

    @admin_command
    def handle_deop(self, user, args):
        user = users.name_to_user(args, self.users)
        user.admin = False

    def handle_rename(self, user, args):
        if not users.is_name_valid(args):
            msg = '[SYSTEM]Name is invalid'
        elif users.is_name_in_use(args, self.users):
            msg = '[SYSTEM]Name is already in use'
        else:
            user.name = args
            msg = '[SYSTEM]Name changed to: ' + args
        self.queue_msg(msg, tuple(self.users_to_sockets((user,))))


    @property
    def users(self):
        return list(self.socket_user_dict.values())

    def sockets_to_users(self, socks: tuple):
        return [self.socket_user_dict.get(sock, None) for sock in socks]

    def users_to_sockets(self, users: tuple):
        keys = tuple(self.socket_user_dict.keys())
        values = tuple(self.users)
        res = []
        for user in users:
            user_i = values.index(user)
            res.append(keys[user_i])
        return res



if __name__ == '__main__':
    try:
        server = Server('127.0.0.1', 8050, 20)
        server.start()
        server.main_loop()
    except KeyboardInterrupt:
        print('Interrupted, quiting...')
