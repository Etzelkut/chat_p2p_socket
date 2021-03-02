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

from threads import *
HEADER_L = 100
BUFFER_SIZE = 528

class GUI_client(tk.Frame):
    def __init__(self, parent, IP, port, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        
        self.ip = IP
        self.port = port

        self.parent = parent
        self.frame_search = tk.Frame(self, width=100, height=100)
        self.search_space = tk.Entry(master = self.frame_search, width = 30)
        self.seatch_button = tk.Button(master = self.frame_search, text = "Search", command = self.search_file)
        
        self.connect_button_text = tk.StringVar()
        self.connect_button = tk.Button(master = self.frame_search, textvariable = self.connect_button_text, command = self.connect)
        self.connect_button_text.set("connect")

        self.seatch_button.config(font=("Courier", 14))
        self.search_space.config(font=("Courier", 14))
        self.connect_button.config(font=("Courier", 14))

        self.frame_result = tk.Frame(self, borderwidth=1, relief=tk.RAISED)
        self.txt_result = tk.Text(self.frame_result, state = 'disabled')
        
        self.scrollbox_y = tk.Scrollbar(self.frame_result, orient=tk.VERTICAL)
        self.scrollbox_x = tk.Scrollbar(self.frame_result, orient=tk.HORIZONTAL)

        self.clickable_list = tk.Listbox(self.frame_result, selectmode = tk.SINGLE)

        self.clickable_list.config(font=("Courier", 12), yscrollcommand=self.scrollbox_y.set, xscrollcommand=self.scrollbox_x.set)
        self.clickable_list.bind('<<ListboxSelect>>', self.on_selection)
        self.scrollbox_y.config(command=self.clickable_list.yview)
        self.scrollbox_x.config(command=self.clickable_list.xview)

        self.frame_load = tk.Frame(self, borderwidth=1, relief=tk.RAISED)
        #width=150, height=150
        self.load_space = tk.Entry(master = self.frame_load, width = 30, state = 'disabled')
        self.load_button = tk.Button(master = self.frame_load, text = "Load", command = self.load)
        
        self.load_space.config(font=("Courier", 14))
        self.load_button.config(font=("Courier", 14))

        self.frame_search.pack(fill=tk.X)
        self.search_space.pack(padx=5, pady=5, side=tk.LEFT)
        self.seatch_button.pack(padx=5, pady=5, side=tk.LEFT)
        self.connect_button.pack(padx=5, pady=5, side=tk.RIGHT)

        self.frame_result.pack(fill=tk.BOTH, expand = True)      
        self.txt_result.pack(padx=5, pady=5, fill=tk.BOTH, expand = True)
        self.scrollbox_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.scrollbox_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.clickable_list.pack(padx=5, pady=5, fill=tk.BOTH, expand = True)
        self.scrollbox_x.pack(side=tk.BOTTOM, fill=tk.X)
        #self.scrollbox_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.frame_load.pack(fill=tk.BOTH, expand = True)
        self.load_space.pack(padx=5, pady=5, side=tk.LEFT)
        self.load_button.pack(padx=5, pady=5, side=tk.LEFT) 

        self.connected = False
        
        self.file_wanted = None
        self.load_queue = queue.Queue()
        self.file_wanted_queue = queue.Queue()


    def add_history(self, text):
        self.txt_result.configure(state='normal')
        self.txt_result.insert(tk.END, text + "\n")
        self.txt_result.configure(state='disabled')


    def on_selection(self, click):
        index_got = click.widget.curselection()
        list_box = self.clickable_list.get(0,'end')
        if not list_box:
            print("")
        else:
            text = list_box[index_got[0]]
            self.load_space.configure(state='normal')
            self.load_space.delete(0,'end')
            self.load_space.insert(0, text)
            self.load_space.configure(state='disabled')

    def wrap_header(self, text, in_bytes = False):
        if not in_bytes:
            text = text.encode('utf-8')
            text_header = f"{len(text):<{HEADER_L}}".encode('utf-8')
            return text_header + text
        else:
            text_header = bytes(f"{len(text):<{HEADER_L}}", "utf-8")
            return text_header + text


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

    def connect_socket(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.ip, self.port))
        send_text = "HELLO"
        self.add_history("sended HELLO")
        send_text = self.wrap_header(send_text) 
        self.client_socket.send(send_text)
        
        data = self.recieve_loop(self.client_socket)
        gotten_data = data.decode("utf-8")
        if gotten_data == "HI":
            return True, gotten_data
        else:
            return False, gotten_data
    
    def search_file(self):
        if not self.connected:
            messagebox.showerror("Connection Failed", "You are not connected")
            return
        else:
            self.clickable_list.delete(0,'end')
            print("!!!!!!!!")
            file_searched = self.search_space.get()
            send_text = "SEARCH"
            send_text = self.wrap_header(send_text) 
            self.file_wanted = file_searched
            file_searched = self.wrap_header(file_searched)
            self.client_socket.send(send_text + file_searched)

        data = self.recieve_loop(self.client_socket)
        gotten_data = data.decode("utf-8")

        if gotten_data == "FOUND":
            self.add_history("found")
            data_list = self.recieve_loop(self.client_socket)
            gotten_data_list = pickle.loads(data_list)
            print("GOT LIST", gotten_data_list)
            self.clickable_list.insert("end", *gotten_data_list)
        else:
            self.add_history("Not Found")
            print(gotten_data)

    def connect(self):
        if not self.connected:
            self.root_disk = os.path.dirname(os.path.abspath(__file__))  + "/sharedp2p"
            if not path.exists(self.root_disk):
                messagebox.showerror("Connection Failed", "Path sharedp2p do not exist")
                return
            
            files_list = list(sorted(os.listdir(self.root_disk)))
            if len(files_list) == 0 or len(files_list) > 5:
                messagebox.showerror("Connection Failed", "No files or more than five")
                return

            #################################################################
            is_connected, gotten_data = self.connect_socket()
            self.add_history("got " + str(gotten_data))
            
            if is_connected == False:
                self.client_socket.close()
                self.add_history("Close")
                print("closed", gotten_data)
                return
            
            print("here we are", gotten_data)
            #<filename, file type (e.g., text, jpg, etc), file size, file last modified date (DD/MM/YY),IP address, port number>
            
            loading_loop_thread = loading_loop(self.load_queue)
            load_ip, load_port = loading_loop_thread.ip, loading_loop_thread.port
            ######################################################################
            
            for i in range(len(files_list)):
                directory_of_the_file = os.path.join(self.root_disk, files_list[i])
                info_file = os.stat(directory_of_the_file)
                typee = filetype.guess(directory_of_the_file)
                files_list[i] = [files_list[i], typee.extension, info_file[6], time.asctime(time.localtime(info_file[8])), load_ip, load_port]


            self.files_list = files_list
            print(files_list)
            self.add_history(str(files_list))

            send_files_list = pickle.dumps(self.files_list)
            send_files_list = self.wrap_header(send_files_list, in_bytes=True)
            self.client_socket.send(send_files_list)
    
            #WITH THIS WILL WORK BETTER BUT NOT SPECIFIED IN THE TASK
            """
            data = self.recieve_loop(self.client_socket)
            gotten_data = data.decode("utf-8")
            
            if gotten_data == "Accepted":
                print("You are accepted")
                self.add_history("Accepted")
            else:
                self.client_socket.close()
                self.add_history("Not Accepted")
                print("closed not accepted", gotten_data)
                return
            """

            self.connected = True
            self.connect_button_text.set("diconnect")
        
            self.load_queue.put("Hi")
            loading_loop_thread.start()

        else:
            send_text = "BYE"
            self.add_history("Bye")
            send_text = self.wrap_header(send_text) 
            self.client_socket.send(send_text)
            self.load_queue.get(0)
            print(self.load_queue.empty())

            self.client_socket.close()
            print("Clossing by BYE")
            self.connected = False
            self.connect_button_text.set("connect")
    
    def load(self):
        if not self.connected:
            messagebox.showerror("Connection Failed", "You are not connected")
            return
        else:
            #this is user A, can be a problem if user B dissconect during the load, but it was not specified in task so this is okay
            download_file = self.load_space.get()
            if not self.load_space.get():
                messagebox.showerror("Load Failed", "You did not choose anything or got empty list!")
                return
            dictionary = download_file.split(" ")
            ip = dictionary[-2]
            port = int(dictionary[-1])
            
            #lock
            file_description = self.file_wanted + " " + str(dictionary[0])+ " " + str(dictionary[1])
            print(file_description)
            #lock

            self.file_wanted_queue.put("Hi")
            downl_loop(self.file_wanted_queue, ip, port, file_description).start()
"""            self.load_space.configure(state='normal')
            self.load_space.delete(0,'end')
            self.load_space.insert(0, text)
            self.load_space.configure(state='disabled')"""



if __name__ == "__main__":
    IP = socket.gethostname()
    port = 14
    window = tk.Tk()
    window.title("GUI CN")
    GUI_client(window, IP, port).pack(fill=tk.BOTH, expand = True)
    window.mainloop()

#height=500, width=500
