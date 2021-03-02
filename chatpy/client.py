import socket
import select
import errno
import sys

HEADER_L = 10 

IP = "127.0.0.1"
PORT = 1488

my_username = input("Username: ")

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))
#recieve
client_socket.setblocking(False)

username = my_username.encode('utf-8')
username_header = f"{len(username):<{HEADER_L}}".encode('utf-8')
client_socket.send(username_header + username)

while True:
    message = input(f"{my_username} > ")

    if message:
        message = message.encode('utf-8')
        message_header = f"{len(message) :< {HEADER_L}}".encode('utf-8')
        client_socket.send(message_header + message)
    
    try:
        while True:
            #recieve
            username_header = client_socket.recv(HEADER_L)
            if not len(username_header):
                print('connection clossed')
                sys.exit()
            username_length = int(username_header.decode('utf-8'))
            username = client_socket.recv(username_length).decode("utf-8")
            
            message_header = client_socket.recv(HEADER_L)
            message_length = int(message_header.decode('utf-8'))
            message = client_socket.recv(message_length).decode("utf-8")

            print(f"{username} > {message}")

    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error ', str(e))
            sys.exit()
        continue

    except Exception as e:
        print('Gneral error ', str(e))
        sys.exit()