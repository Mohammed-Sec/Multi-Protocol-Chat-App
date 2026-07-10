Secure Multi-Protocol Chat Application

Overview
This project is a comprehensive multi-protocol chat application that demonstrates advanced computer networking architectures. It features a custom-built dual-server environment capable of handling both connection-oriented (TCP) and connectionless (UDP) communications simultaneously, providing a highly practical implementation of network socket programming.

Core Features
The server architecture utilizes multithreading to manage multiple client connections concurrently, ensuring real-time message broadcasting without blocking the main execution thread. The client-side features a graphical user interface built with Tkinter, allowing users to seamlessly switch between TCP and UDP network protocols before establishing a connection to the server.

Security and Encryption
To secure data in transit, the TCP implementation integrates SSL/TLS encryption. The server dynamically generates its own RSA 2048-bit key pairs and self-signed X.509 certificates using the OpenSSL library. This ensures that all TCP payloads are fully encrypted, protecting the communication channels against packet sniffing and man-in-the-middle attacks.

Protocol Mechanics
For the TCP protocol, the application enforces a secure 3-way handshake and maintains persistent, encrypted connections for guaranteed data delivery. For the UDP protocol, the application demonstrates connectionless, low-latency message broadcasting. This dual implementation effectively highlights the fundamental differences between stateful, secure data transmission and high-speed, stateless network operations.
