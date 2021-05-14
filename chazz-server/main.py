import select
import socket

addr = '127.0.0.1'
port = 8050
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((addr, port))
server_socket.listen()
client_sockets_list = []
msgs_to_send = {}   # format: {socket: [msgs],}

while True:
    rlist, wlist, xlist = select.select([server_socket]+client_sockets_list, client_sockets_list, [])

    for current_socket in rlist:
        if current_socket == server_socket:
            conn, addr = current_socket.accept()
            client_sockets_list.append(conn)
            print('A new connection:', addr)
        else:
            msg = current_socket.recv(1024)
            for sock in client_sockets_list:
                if not sock == current_socket:
                    if sock in msgs_to_send:
                        msgs_to_send[sock].append(msg)
                    else:
                        msgs_to_send[sock] = []

    for current_socket in wlist:
        if current_socket in msgs_to_send:
            for msg in msgs_to_send[current_socket]:
                current_socket.sendall(msg)
                msgs_to_send[current_socket].remove(msg)


