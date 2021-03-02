import tkinter as tk
from tkinter.filedialog import askopenfile
import os 
from os import path
from tkinter import messagebox
import filetype
import time
import socket
import pickle
import ast
import threading 
import queue
import _thread

HEADER_L = 100
BUFFER_SIZE = 528


class loading_loop(threading.Thread):
    def __init__(self, queue_getted):
        threading.Thread.__init__(self)
        self.queue_getted = queue_getted

        self.socket_load = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_load.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        IP = socket.gethostname()
        self.socket_load.bind((IP, 0))
        self.ip, self.port = self.socket_load.getsockname()
        self.socket_load.listen()

    def wrap_header(self, text, in_bytes = False):
        if not in_bytes:
            text = text.encode('utf-8')
            text_header = f"{len(text):<{HEADER_L}}".encode('utf-8')
            return text_header + text
        else:
            text_header = bytes(f"{len(text):<{HEADER_L}}", "utf-8")
            return text_header + text

    def receive_message(self, client_socket):
        if self.queue_getted.empty():
            self.socket_load.close()
            print("Thread closed!!!")
            return "quit"
        try:
            len_of_message_header = client_socket.recv(HEADER_L)
            if not len(len_of_message_header):
                return False
            len_of_message = int(len_of_message_header.decode("utf-8"))
            data = client_socket.recv(len_of_message)
            return data
        except:
            return False

    def recieve_loop(self, client_socket):
        while True:
            data = self.receive_message(client_socket)
            if data is "quit":
                return "quit"
            if data is False:
                continue
            return data
    
    def on_client(self, client_socket, address):
        print("adress is", address)
        data = self.recieve_loop(client_socket)
        if data is "quit":
            return
        gotten_data = data.decode("utf-8")
        
        if gotten_data == "DOWNLOAD":
            data = self.recieve_loop(client_socket)
            gotten_data = data.decode("utf-8")
            
            file_name = gotten_data.split(" ")
            print(file_name)
            send_text = "FILE"
            send_text = self.wrap_header(send_text) 
            client_socket.send(send_text)

            file_name = file_name[0]
            print(file_name)
            root_disk = os.path.dirname(os.path.abspath(__file__))  + "/sharedp2p"
            directory_of_the_file = os.path.join(root_disk, file_name)

            f = open(directory_of_the_file,'rb')
            while True:
                l = f.read(BUFFER_SIZE)
                while (l):
                    client_socket.send(l)
                    #print('Sent ',repr(l))
                    l = f.read(BUFFER_SIZE)
                if not l:
                    f.close()
                    client_socket.close()
                    return
        else:
            client_socket.close()
            print("client closed by load loop")


    def run(self):
        """        while True:
            #self.server_socker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #self.server_socker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)"""
        while True:
            if self.queue_getted.empty():
                self.socket_load.close()
                print("Thread closed!!!")
                _thread.exit()
                return
            print("WE ARE HERE point 1")
            client_socket, address = self.socket_load.accept()
            _thread.start_new_thread(self.on_client, (client_socket, address))
        self.socket_load.close()




class downl_loop(threading.Thread):
    def __init__(self, queue_getted, ip, port, file_description):
        threading.Thread.__init__(self)
        self.queue_getted = queue_getted
        self.ip, self.port = ip, port
        self.file_description = file_description

    def receive_message(self, client_socket):
        try:
            len_of_message_header = client_socket.recv(HEADER_L)
            if not len(len_of_message_header):
                return False
            len_of_message = int(len_of_message_header.decode("utf-8"))
            data = client_socket.recv(len_of_message)
            return data
        except:
            return False

    def recieve_loop(self, client_socket):
        while True:
            data = self.receive_message(client_socket)
            if data is False:
                continue
            return data
    
    def wrap_header(self, text, in_bytes = False):
        if not in_bytes:
            text = text.encode('utf-8')
            text_header = f"{len(text):<{HEADER_L}}".encode('utf-8')
            return text_header + text
        else:
            text_header = bytes(f"{len(text):<{HEADER_L}}", "utf-8")
            return text_header + text
    
    def run(self):
        #self.server_socker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.server_socker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if not self.queue_getted.empty():
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.ip, self.port))
            
            send_text = "DOWNLOAD"
            send_text = self.wrap_header(send_text) 
            self.client_socket.send(send_text)

            send_text = self.file_description
            send_text = self.wrap_header(send_text) 
            self.client_socket.send(send_text)

            data = self.recieve_loop(self.client_socket)
            gotten_data = data.decode("utf-8")

            #file_description
            file_name = self.file_description.split(" ")
            file_name = file_name[0]

            if gotten_data == "FILE":
                with open(file_name, 'wb') as f:
                        while True:
                            data = self.client_socket.recv(BUFFER_SIZE)
                            if not data:
                                f.close()
                                print("STOPED")
                                break
                            # write data to a file
                            f.write(data)
            else:
                print("Nothing came")
            
            self.client_socket.close()
            self.queue_getted.get(0)
            print(self.queue_getted.empty())


        """
        data = self.recieve_loop(self.client_socket)
        gotten_data = data.decode("utf-8")
        if gotten_data == "HI":
            return True, gotten_data
        else:
            return False, gotten_data
        """