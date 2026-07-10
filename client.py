import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import socket
import ssl

# ==================== CONFIGURATION ====================
SERVER_IP = '192.168.1.17'  # Change this to your server IP
TCP_PORT = 65432
UDP_PORT = 65433
# =======================================================

class SimpleChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Client")
        self.root.geometry("400x500")
        
        self.username = ""
        self.is_connected = False
        self.current_socket = None
        self.protocol = ""
        
        self.setup_gui()
        
    def setup_gui(self):
        # Connection 
        conn_frame = tk.Frame(self.root)
        conn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(conn_frame, text="Name:").pack(side=tk.LEFT)
        self.name_entry = tk.Entry(conn_frame, width=15)
        self.name_entry.pack(side=tk.LEFT, padx=5)
        self.name_entry.insert(0, "Anonymous")
        
        tk.Label(conn_frame, text="Protocol:").pack(side=tk.LEFT, padx=(10,0))
        self.protocol_var = tk.StringVar(value="TCP")
        protocol_menu = tk.OptionMenu(conn_frame, self.protocol_var, "TCP", "UDP")
        protocol_menu.pack(side=tk.LEFT, padx=5)
        
        self.connect_btn = tk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.pack(side=tk.RIGHT)
        
        # Chat display
        self.chat_text = scrolledtext.ScrolledText(self.root, state=tk.DISABLED)
        self.chat_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Message input
        input_frame = tk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.msg_entry = tk.Entry(input_frame)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.msg_entry.bind('<Return>', lambda e: self.send_message())
        
        self.send_btn = tk.Button(input_frame, text="Send", command=self.send_message, state=tk.DISABLED)
        self.send_btn.pack(side=tk.RIGHT)
        
    def toggle_connection(self):
        if not self.is_connected:
            self.connect()
        else:
            self.disconnect()
    
    def connect(self):
        self.username = self.name_entry.get().strip()
        if not self.username:
            messagebox.showerror("Error", "Please enter your name")
            return
        
        self.protocol = self.protocol_var.get()
        self.connect_btn.config(state=tk.DISABLED)
        
        # Start connection  thread
        thread = threading.Thread(target=self.start_client, daemon=True)
        thread.start()
    
    def start_client(self):
        try:
            if self.protocol == "TCP":
                self.start_tcp_client()
            else:
                self.start_udp_client()
        except Exception as e:
            self.add_message(f"Connection error: {e}")
            self.root.after(0, self.disconnect)
    
    def start_tcp_client(self):
        """TCP Client with SSL"""
        try:
            # SSL 
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ssl_socket = context.wrap_socket(client_socket, server_hostname=SERVER_IP)
            
            # Connect ssl like in java
            ssl_socket.connect((SERVER_IP, TCP_PORT))
            
            # Get welcome message
            welcome = ssl_socket.recv(1024).decode()
            
            self.current_socket = ssl_socket
            self.is_connected = True
            
            self.root.after(0, lambda: self.on_connected(welcome))
            
            # Receive messages 
            while self.is_connected:
                try:
                    message = ssl_socket.recv(1024).decode()
                    if message:
                        self.add_message(message)
                except:
                    break
                    
        except Exception as e:
            self.add_message(f"TCP Error: {e}")
        finally:
            if self.is_connected:
                self.root.after(0, self.disconnect)
    
    def start_udp_client(self):
        """UDP Client"""
        try:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Send a join message to register with server
            join_msg = f"{self.username} joined the chat"
            udp_socket.sendto(join_msg.encode(), (SERVER_IP, UDP_PORT))
            
            self.current_socket = udp_socket
            self.is_connected = True
            
            self.root.after(0, lambda: self.on_connected("Connected to UDP server"))
            
            # Receive messages like in java and handel exception
            while self.is_connected:
                try:
                    udp_socket.settimeout(1.0)
                    data, addr = udp_socket.recvfrom(1024)
                    message = data.decode()
                    self.add_message(message)
                except socket.timeout:
                    continue
                except:
                    break
                    
        except Exception as e:
            self.add_message(f"UDP Error: {e}")
        finally:
            if self.is_connected:
                self.root.after(0, self.disconnect)
    
    def on_connected(self, welcome_message):
        self.connect_btn.config(text="Disconnect", state=tk.NORMAL)
        self.send_btn.config(state=tk.NORMAL)
        self.msg_entry.focus()
        
        self.add_message("=" * 40)
        self.add_message(f"Chat - {self.username}")
        self.add_message("Connected!")
        self.add_message("-" * 40)
        self.add_message(welcome_message)
    
    def disconnect(self):
        self.is_connected = False
        try:
            if self.current_socket:
                self.current_socket.close()
        except:
            pass
        
        self.connect_btn.config(text="Connect", state=tk.NORMAL)
        self.send_btn.config(state=tk.DISABLED)
        self.add_message("Disconnected from server")
    
    def send_message(self):
        if not self.is_connected:
            return
            
        message = self.msg_entry.get().strip()
        if not message:
            return
            
        self.msg_entry.delete(0, tk.END)
        
        if message.lower() == 'exit':
            self.disconnect()
            return
        
        # Send message
        full_message = f"{self.username}: {message}"
        
        try:
            if self.protocol == "TCP":
                self.current_socket.sendall(full_message.encode())
            else:
                self.current_socket.sendto(full_message.encode(), (SERVER_IP, UDP_PORT))
        except Exception as e:
            self.add_message(f"Send error: {e}")
    
    def add_message(self, message):
        def update_display():
            self.chat_text.config(state=tk.NORMAL)
            self.chat_text.insert(tk.END, message + "\n")
            self.chat_text.config(state=tk.DISABLED)
            self.chat_text.see(tk.END)
        
        self.root.after(0, update_display)

def main():
    root = tk.Tk()
    app = SimpleChatGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()