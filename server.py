import socket
import threading
import ssl
from OpenSSL import crypto

# ==================== CONFIGURATION ====================
SERVER_HOST = '192.168.1.17'  # Change this to your server IP
TCP_PORT = 65432
UDP_PORT = 65433
# =======================================================

class NetworkServer:
    def __init__(self):
        self.host = SERVER_HOST
        self.tcp_port = TCP_PORT
        self.udp_port = UDP_PORT
        self.running = False
        self.tcp_clients = []  # Track all TCP clients
        self.udp_clients = set()  # Track all UDP clients
        self.client_lock = threading.Lock()  # Thread safety
        #create cer_method
    def create_ssl_certificate(self):
        """Create SSL certificates for secure communication"""
        try:
            print("Creating SSL certificates for secure TCP communication...")
            
            # Create key pair
            key = crypto.PKey()
            key.generate_key(crypto.TYPE_RSA, 2048)
            
            # Create certificate
            cert = crypto.X509()
            cert.get_subject().CN = self.host
            cert.set_serial_number(1000)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(365*24*60*60)
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(key)
            cert.sign(key, 'sha256')
            
            # Save files
            with open("server.crt", "wb") as f:
                f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
            
            with open("server.key", "wb") as f:
                f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
            
            print("SSL certificates created:")
            print("- server.crt (Certificate)")
            print("- server.key (Private Key)")
            return True
            
        except Exception as e:
            print(f"Error creating certificates: {e}")
            return False

    def broadcast_tcp_message(self, message, sender_conn):
        """Broadcast message to all TCP clients except sender"""
        with self.client_lock:
            disconnected_clients = []
            for client_conn, client_addr in self.tcp_clients:
                
                    try:
                        client_conn.sendall(message.encode())
                    except:
                        disconnected_clients.append((client_conn, client_addr))
            
            # Remove disconnected clients
            for client in disconnected_clients:
                self.tcp_clients.remove(client)
    
    def broadcast_udp_message(self, message, sender_addr):
        """Broadcast message to all UDP clients except sender"""
        with self.client_lock:
            disconnected_clients = []
            for client_addr in self.udp_clients:
                if client_addr != sender_addr:
                    try:
                        self.udp_socket.sendto(message.encode(), client_addr)
                    except:
                        disconnected_clients.append(client_addr)
            
            # Remove disconnected clients
            for client in disconnected_clients:
                self.udp_clients.remove(client)
        
    def handle_tcp_client(self, conn, addr, client_id):
        print(f"TCP Client {client_id} connected from {addr}")
        print(f"TCP 3-Way Handshake completed with Client {client_id}")
        
        # Add client to tracking list
        with self.client_lock:
            self.tcp_clients.append((conn, addr))
        
        try:
            with conn:
                # Send welcome message
                conn.sendall("Welcome to Secure TCP Server! Type 'exit' to quit.".encode())
                
                # Persistent chat loop
                message_count = 0
                while True:
                    data = conn.recv(1024).decode()
                    if not data:
                        break
                    
                    if data.lower() == 'exit':
                        print(f"TCP Client {client_id} requested to disconnect")
                        break
                    
                    message_count += 1
                    print(f"TCP Client {client_id} says: {data}")
                    
                    # BROADCAST MESSAGE TO ALL OTHER CLIENTS
                    self.broadcast_tcp_message(data, conn)
                    
                    
                   
                    
        except Exception as e:
            print(f"Error with TCP client {client_id}: {e}")
        finally:
            # Remove client from tracking
            with self.client_lock:
                for client in self.tcp_clients:
                    if client[0] == conn:
                        self.tcp_clients.remove(client)
                        break
            print(f"TCP Client {client_id} disconnected")
    
    def start_tcp_server(self):
        """Secure TCP Server with SSL Encryption and 3-Way Handshake"""
        # Create SSL certificates first
        if not self.create_ssl_certificate():
            print("Failed to create SSL certificates. TCP Server cannot start.")
            return
            
        try:
            # Create SSL context for encryption
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain('server.crt', 'server.key')
            
            # Create base server socket
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcp_socket.bind((self.host, self.tcp_port))
            tcp_socket.listen(5)
            
            # Wrap with SSL
            ssl_socket = context.wrap_socket(tcp_socket, server_side=True)
            
            print("=" * 60)
            print("SECURE TCP SERVER (With 3-Way Handshake & SSL Encryption)")
            print("=" * 60)
            print(f"TCP Server started on {self.host}:{self.tcp_port}")
            print("Protocol: TCP with SSL Encryption")
            print("Features: 3-Way Handshake, Persistent Connections")
            print("Multi-threading: ENABLED")
            print("Encryption: ENABLED")
            print("Broadcasting: ENABLED - Clients can communicate with each other!")
            print("Waiting for TCP connections...")
            print("-" * 60)
            
            tcp_client_counter = 0
            
            while True:
                conn, addr = ssl_socket.accept()
                tcp_client_counter += 1
                
                print(f"Secure TCP connection from {addr} - Client #{tcp_client_counter}")
                print(f"Total TCP clients: {len(self.tcp_clients) + 1}")
                
                # Start new thread for each TCP client
                client_thread = threading.Thread(
                    target=self.handle_tcp_client,
                    args=(conn, addr, tcp_client_counter)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except Exception as e:
            print(f"TCP Server error: {e}")
        finally:
            if tcp_socket:
                tcp_socket.close()
            print("TCP Server shut down")
    
    def handle_udp_client(self, data, addr, message_count):
        """Handle UDP messages (connectionless)"""
        try:
            message = data.decode()
            print(f"UDP Message #{message_count} from {addr}: {message}")
            
            # Add client to tracking if new
            with self.client_lock:
                if addr not in self.udp_clients:
                    self.udp_clients.add(addr)
                    print(f"New UDP client registered: {addr}")
            
            # BROADCAST MESSAGE TO ALL OTHER UDP CLIENTS
            self.broadcast_udp_message(message, addr)
            
            # Send response back to sender
            response = f" {message}"
            self.udp_socket.sendto(response.encode(), addr)
            
        except Exception as e:
            print(f"Error handling UDP message: {e}")
    
    def start_udp_server(self):
        """UDP Server (Connectionless - No Handshake)"""
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            self.udp_socket.bind((self.host, self.udp_port))
            
            print("=" * 50)
            print("UDP SERVER (Connectionless - No Handshake)")
            print("=" * 50)
            print(f"UDP Server started on {self.host}:{self.udp_port}")
            print("Protocol: UDP - Connectionless")
            print("Features: No handshake, Faster, No guaranteed delivery")
            print("Broadcasting: ENABLED - Clients can communicate with each other!")
            print("Waiting for UDP messages...")
            print("-" * 50)
            
            udp_message_count = 0
            
            while True:
                data, addr = self.udp_socket.recvfrom(1024)
                udp_message_count += 1
                
                # Handle UDP message in a new thread
                udp_thread = threading.Thread(
                    target=self.handle_udp_client,
                    args=(data, addr, udp_message_count)
                )
                udp_thread.daemon = True
                udp_thread.start()
                
        except Exception as e:
            print(f"UDP Server error: {e}")
        finally:
            self.udp_socket.close()
            print("UDP Server shut down")
    
    def start_both_servers(self):
        """Start both TCP and UDP servers simultaneously"""
        print("COMPUTER NETWORKING PROJECT - MULTI-PROTOCOL SERVER")
        print("==================================================")
        print(f"Server Host: {self.host}")
        print(f"TCP Port: {self.tcp_port} (Secure with SSL)")
        print(f"UDP Port: {self.udp_port} (Connectionless)")
        print("FEATURE: Clients can now communicate with each other!")
        print()
        
        # Create threads for both servers
        tcp_thread = threading.Thread(target=self.start_tcp_server)
        udp_thread = threading.Thread(target=self.start_udp_server)
        
        # Set as daemon threads so they exit when main program exits
        tcp_thread.daemon = True
        udp_thread.daemon = True
        
        # Start both servers
        tcp_thread.start()
        udp_thread.start()
        
        print("Both TCP and UDP servers are starting...")
        print("Press Ctrl+C to stop all servers")
        
        try:
            # Keep main thread alive
            while True:
                pass
        except KeyboardInterrupt:
            print("\nShutting down all servers...")
            self.running = False

def main():
    server = NetworkServer()
    server.start_both_servers()

if __name__ == "__main__":
    main()