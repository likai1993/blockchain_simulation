# Internet Simulator
Making a socket programming with TCP connection by python.
Topology: Clients want to send data to each other with a public server in the middle, who behaves as a internet simulator.
This server use multithreading code mechanism to maintain the blocking accept() method.
This server use list data type to maintain connecting of multiple clients.
The clients run VPN client code.

## Usage
```bash
./server.py PORT_NUMBER
``` 
