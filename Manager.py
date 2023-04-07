import socket
import threading
import time

HOST = '127.0.0.1'
PORT = 65345

class Manager:
    class Peer:
        def __init__(self, conn, addr):
            self.conn = conn
            self.addr = addr
            self.files = []

    def __init__(self, host, port, timeout=60):
        # Setup socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))

        self.timeout = timeout
        self.threadLock = threading.Lock()
        self.active_peers = []

    def broadcastActivePeers(self):
        self.threadLock.acquire()
        for peer in self.active_peers:
            l = ';'.join([f"{p.addr[0]},{p.addr[1]},{len(p.files)}" for p in self.active_peers])
            peer.conn.sendall(l.encode())
        self.threadLock.release()

    def registerPeer(self, peer):
        peer.conn.settimeout(60)
        self.threadLock.acquire()
        if peer not in self.active_peers:
            print(f'[INFO] New peer connected: {peer.addr}')
            self.active_peers.append(peer)
        self.threadLock.release()

        self.broadcastActivePeers()

    def removePeer(self, peer):

        # Remove peer from active peers, lock the connection and close it
        self.threadLock.acquire()
        if peer in self.active_peers:
            print(f'[INFO] Peer disconnected: {peer.addr}')
            self.active_peers.remove(peer)
        self.threadLock.release()
        peer.conn.close()

        self.broadcastActivePeers()

    def handlePeer(self, peer):
        while True:
            try:
                data = peer.conn.recv(1024)

                if not data or data == b'CLOSE':
                    self.removePeer(peer)
                    break
                    
            except socket.timeout:
                print(f'[INFO] Pinging {peer.addr}')
                peer.conn.sendall(b'PING')
                data = peer.conn.recv(1024)
                if not data == b'PONG':
                    self.removePeer(peer)
                    break
            

    def handlePeerConnections(self):
        while True:
            self.socket.listen()
            clientSocket, clientAddress = self.socket.accept()
            clientHost, clientPort = clientSocket.recv(1024).decode().split(',')
            clientPort = int(clientPort)
            self.registerPeer(self.Peer((clientSocket, clientAddress), (clientHost, clientPort)))
            threading.Thread(target=self.handlePeer, args=(self.active_peers[-1],), daemon=True).start()
    
    def run(self):
        
        print('Manager has been started!')

        try:
            self.handlePeerConnections()
        
        except KeyboardInterrupt:
            print('Manager Shutting down...')
            self.socket.close()
            for peer in self.active_peers.copy():
                peer.conn.close()
                self.active_peers.remove(peer)
            exit(0)
        
        except Exception as e:
            self.socket.close()
            for peer in self.active_peers.copy():
                peer.conn.close()
                self.active_peers.remove(peer)
            print('{e}').format(e=e)
            raise

if __name__ == '__main__':
    # Manager(HOST, PORT).run()
    # create a object of Manager class
    manager = Manager(HOST, PORT)
    # call run method of Manager class
    manager.run()