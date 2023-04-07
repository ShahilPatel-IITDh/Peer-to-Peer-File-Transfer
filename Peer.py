import socket
import threading
import os

HOST = '127.0.0.1'
PORT = 65345

class Peer:
    def __init__(self, host, port, chunkSize=1024):
        self.managerHost = host
        self.managerPort = port
        self.chunkSize = chunkSize        
        self.folder = input('Path to the shared folder: ')
        self.files = ['file1.txt', 'file2.txt', 'file3.txt']

        try:
            if not os.path.isdir(self.folder):
                raise(Exception('Invalid folder path!'))
        except Exception as e:
            print({e}).format(e=e)
            exit(1)

        # socket for incoming requests 
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', 0))
        self.host, self.port = self.socket.getsockname()

        # Socket for communication with manager
        self.manager = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.manager.connect((self.managerHost, self.managerPort))
        self.manager.sendall("{self.host},{self.port}".encode()).format(self=self)
         
    # Not updated
    def handleManager(self):
        name = input('Enter peer name: ')
        while True:
            data = self.socket.recv(1024)
            if not data:
                raise Exception('Manager disconnected!')
            
            if data == b'PING':
                print('Pong!')
                self.manager.sendall(b'PONG')
                continue

            print('Received peer update!')
            self.peers = [(p.split(",")[0], p.split(",")[1]) for p in data.decode().split(';')]
            # print the active peers list here
            print(self.peers)

    # Not updated
    def sendFile(self, filename):
        if filename not in self.files:
            print(f"{filename} not shared!")
            return
        # if file present then send the file to the requesting peer
        with open(filename, 'rb') as f:
            data = f.read()
        self.socket.sendall(f"SHARE {filename},{len(data)}".encode())
        ack = self.socket.recv(1024)
        if ack == b'OK':
            self.socket.sendall(data)
            print(f"{filename} shared successfully!")
        else:
            print(f"Error sharing {filename}: {ack.decode()}")

    # Not updated
    def requestFile(self, filename):
        threads = []
        # Request file from each peer in parallel
        for peer in self.peers:
            t = threading.Thread(target=self.fetchFile, args=(peer, filename), daemon=True)
            threads.append(t)
            t.start()
        
        # Wait for all threads to finish
        for t in threads:
            t.join()

        # Combine the file fragments and save the complete file
        with open(filename, 'wb') as f:
            for i in range(len(threads)):
                filepath = f"{filename}.part{i}"
                with open(filepath, 'rb') as part:
                    f.write(part.read())
                os.remove(filepath)
        print(f"{filename} downloaded successfully!")

    # Not updated
    def fetchFile(self, peer, filename):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((self.managerHost, 0))
            sock.listen()
            sock.settimeout(10)
            sock.sendall(f"GET {filename}".encode())
            data = sock.recv(1024)
            filesize = int(data.decode().split(",")[1])
            print(f"Fetching {filename} from {peer}")
            recv_bytes = 0
            with open(f"{filename}.part{peer[1]}", 'wb') as f:
                while recv_bytes < filesize:
                    data = sock.recv(1024)
                    f.write(data)
                    recv_bytes += len(data)
            sock.sendall(f"DISCONNECT {peer[1]}".encode())
            sock.close()
        except:
            print(f"Could not fetch {filename} from {peer}")
    
    # Not updated
    def shareFile(self, filename):
        if filename not in self.files:
            print(f"{filename} not shared!")
            return
        
        # if file present then send the file to the requesting peer
        with open(filename, 'rb') as f:
            data = f.read()
        self.socket.sendall(f"SHARE {filename},{len(data)}".encode())
        self.socket.recv(1024)
        self.socket.sendall(data)
        print(f"{filename} shared successfully!")

    def run(self):
        try:

            threading.Thread(target=self.handleManager, daemon=True).start()
            threading.Thread(target=self.handleRequests, daemon=True).start()

            while True:
                # Wait for the peers to be available
                if not hasattr(self, 'peers') or len(self.peers) == 0:
                    print('Waiting for peers...')
                    while not hasattr(self, 'peers'):
                        pass
                
                # Choose the file to request for
                filename = input('Enter filename to download: ')
                if(filename == ''):
                    print('Please Enter a file name that you want to download')
                    continue
                
                if filename in os.listdir(self.folder):
                    print('File already present!')
                    continue
                
                # Request the file
                self.requestFile(filename)

        except KeyboardInterrupt:
            self.socket.sendall(b'CLOSE')
            self.socket.close()
            print('Shutting down...')
            exit(0)
        

        except Exception as exp:
            self.socket.sendall(b'CLOSE')
            self.socket.close()
            print(f'[ERROR] {exp}')
            raise

if __name__ == '__main__':
    peer = Peer(HOST, PORT)
    peer.run()