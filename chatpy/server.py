import socket
#gives OS level IO capabiities with socket in mind 
import select

HEADER_LENGTH = 10
IP = "127.0.0.1"
PORT = 1488

server_socker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#this is gonna do let recconect
server_socker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socker.bind((IP, PORT))

server_socker.listen()

socket_list = [server_socker]

clients = {}

def recieve_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)

        if not len(message_header):
            return False
        
        message_length = int(message_header.decode("utf-8").strip())
        return {"Header": message_header, "data": client_socket.recv(message_length)}
    except:
        return False

#select takes 3 param, read list, things you want to read in, write list, sockets 
# we gonna read and write, socket error 
while True:
    read_socket, _, exception_socket = select.select(socket_list, [], socket_list)
    #ckeck read_socket
    for notifed_socket in read_socket:
        if notifed_socket == server_socker:
            client_socket, client_adress = server_socker.accept()
            
            user = recieve_message(client_socket)
            if user is False:
                continue

            socket_list.append(client_socket)

            clients[client_socket] = user

            print(f"Accept new connection from {client_adress[0]}:{client_adress[1]} username:{user['data'].decode('utf-8')}")
        
        else:
            message = recieve_message(notifed_socket)

            if message is False:
                print(f"Closed connection from {clients[notifed_socket]['data'].decode('utf-8')}")
                socket_list.remove(notifed_socket)
                del clients[notifed_socket]
                continue
            user = clients[notifed_socket]

            username = user['data'].decode('utf-8')
            print(f"receive from {username}: {message['data'].decode('utf-8')}")

            for client_socket in clients:
                if client_socket != notifed_socket:
                    client_socket.send(user['Header'] + user['data'] + message['Header'] + message['data'])
    for notifed_socket in exception_socket:
        socket_list.remove(notifed_socket)
        del clients[notifed_socket]
