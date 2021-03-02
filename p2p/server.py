import socket 
import _thread
HEADER_LENGTH = 100
import pickle

class Server():
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.filelist = {}
        self.lock = _thread.allocate_lock()

    def receive_message(self, client_socket):
        try:
            len_of_message_header = client_socket.recv(HEADER_LENGTH)
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
            text_header = f"{len(text):<{HEADER_LENGTH}}".encode('utf-8')
            return text_header + text
        else:
            text_header = bytes(f"{len(text):<{HEADER_LENGTH}}", "utf-8")
            return text_header + text


    def add_to_database(self, gotten_data_list):
        for i in range(len(gotten_data_list)):
            file_name = gotten_data_list[i][0]
            if file_name in self.filelist:
                #gotten_data_list[i].pop("filename")
                hash_appended = {}
                hash_appended["file_type"] = gotten_data_list[i][1]
                hash_appended["file_size"] = gotten_data_list[i][2]
                hash_appended["last_modified"] = gotten_data_list[i][3]
                hash_appended["IP"] = gotten_data_list[i][4]
                hash_appended["port"] = gotten_data_list[i][5]
                self.filelist[file_name].append(hash_appended)
            else:
                self.filelist[file_name] = []
                #gotten_data_list[i].pop("filename")
                hash_appended = {}
                hash_appended["file_type"] = gotten_data_list[i][1]
                hash_appended["file_size"] = gotten_data_list[i][2]
                hash_appended["last_modified"] = gotten_data_list[i][3]
                hash_appended["IP"] = gotten_data_list[i][4]
                hash_appended["port"] = gotten_data_list[i][5]

                self.filelist[file_name].append(hash_appended)
        return
    
    def BYE_handler(self, address):
        #could be done efficently if just storing indexes when assigmenting
        #
        empty_list = []
        empty_list_items = []
        for key, items in self.filelist.items():
            
            for i in range(len(items)):
                dictionaty_in_list = items[i]
                if dictionaty_in_list["IP"] == address[0] and dictionaty_in_list["port"] == address[1]:
                    empty_list_items.append(i)

            for ii in empty_list_items:
                self.filelist[key].pop(ii)
            empty_list_items = []
            if self.filelist[key] == []:
                empty_list.append(key)
        #
        for key in empty_list:
            self.filelist.pop(key)

        print(self.filelist, "\n")  
        return  

    def SEARCH_handler(self, key, address, client_socket):
        #could be done efficently if just storing indexes when assigmenting
        send_list = self.filelist[key].copy()
        empty_list_items = []

        for i in range(len(send_list)):
            dictionaty_in_list = send_list[i]
            if dictionaty_in_list["IP"] == address[0] and dictionaty_in_list["port"] == address[1]:
                empty_list_items.append(i)
        
        for i in empty_list_items:
            send_list.pop(i)

        if send_list == []:
            message = self.wrap_header("NOT FOUND")
            client_socket.send(message)
            print("NOT FOUND")
            return

        message = self.wrap_header("FOUND")
        client_socket.send(message)
        print("FOUND", send_list)

        #<file type, file size, file last modified date (DD/MM/YY), IP address, portnumber>
        for i in range(len(send_list)):
            #could be done by just dict.values() but it change order so ughh
            send_list[i] = [send_list[i]["file_type"], send_list[i]["file_size"], send_list[i]["last_modified"], send_list[i]["IP"], send_list[i]["port"]]

        send_files_list = pickle.dumps(send_list)
        send_files_list = self.wrap_header(send_files_list, in_bytes=True)
        client_socket.send(send_files_list)
        return 



    def on_client(self, client_socket, address):
        print("adress is", address)

        data = self.recieve_loop(client_socket)
        gotten_data = data.decode("utf-8")
        print("GOT DATA", gotten_data)
        
        if gotten_data != "HELLO":
            message = self.wrap_header("You are dissconected for wrong Handshake words")
            client_socket.send(message)
            print("Wrong Handshake words")
            client_socket.close()
            print("Closing", address)
            return
        else:
            message = self.wrap_header("HI")
            client_socket.send(message)
            print("Right Handshake words")
        
        data_list = self.recieve_loop(client_socket)
        gotten_data_list = pickle.loads(data_list)
        print("GOT DATA", gotten_data_list)
        
        if not isinstance(gotten_data_list, list) or len(gotten_data_list)>5 or len(gotten_data_list) == 0: 
            message = self.wrap_header("You are dissconected for wrong list of file")
            client_socket.send(message)
            print("wrong list of file")
            client_socket.close()
            print("Closing", address)
            return
        else:
            #WITH THIS WILL WORK BETTER BUT NOT SPECIFIED IN THE TASK
            #message = self.wrap_header("Accepted")
            #client_socket.send(message)
            print("Accepted", address, "\n")
        #

        self.lock.acquire()
        self.add_to_database(gotten_data_list)
        self.lock.release()
        adress_of_client_server = (gotten_data_list[0][4], gotten_data_list[0][5])

        while True:
            data = self.recieve_loop(client_socket)
            gotten_data = data.decode("utf-8")
            
            if gotten_data == "BYE":
                client_socket.close()
                print("BYEing", address)
                self.lock.acquire()
                self.BYE_handler(adress_of_client_server)
                self.lock.release()
                return
            
            if gotten_data == "SEARCH":
                data = self.recieve_loop(client_socket)
                gotten_data = data.decode("utf-8")
                if gotten_data in self.filelist:
                    self.SEARCH_handler(gotten_data, adress_of_client_server, client_socket)
                else:
                    message = self.wrap_header("NOT FOUND")
                    client_socket.send(message)
                    print("NOT FOUND")
            

    def start(self):
        self.server_socker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #this is gonna do let recconect
        self.server_socker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socker.bind((self.ip, self.port))
        self.server_socker.listen()

        while True:
            print("WE ARE HERE point 1")
            client_socket, address = self.server_socker.accept()
            _thread.start_new_thread(self.on_client, (client_socket, address))
        self.server_socker.close()



if __name__ == "__main__":
    IP = socket.gethostname()
    port = 14
    server = Server(IP, port)
    server.start()
