# Peer-to-Peer-File-Transfer
The program uses Socket Programming to implement peer-to-peer file transfer. There is manager which will maintain a list of Active Peers in the connection, the Active peers will be able to request and send files among themselves.

To create a manager (required to create one before creating the peers) run the following command in a terminal:
  python3 Manager.py

To create multiple peers, run the following command in different terminals:
  python3 Peer.py
  
 When asked to specify the path to the folder. Add the folder's path whose data you want to transfer between peers.
