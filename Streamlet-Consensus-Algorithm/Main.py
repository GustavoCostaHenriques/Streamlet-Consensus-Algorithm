import threading
import BlockchainNetworkNode
import random
import time
import os
import socket
import subprocess
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def main():
    
    NumberOfNodes = int(input("Enter the number of nodes:\n=> "))
    NumberOfEpoch = int(input("Enter the number of epochs:\n=> "))
    Delta = int(input("Enter the number of seconds per epoch:\n=> "))
    
    # Creation of all nodes
    for i in range(NumberOfNodes):
        node_id = i 
        port = 5000 + i
        subprocess.Popen(['start', 'cmd', '/k', 'python', 'BlockchainNetworkNode.py', str(node_id), str(port)], shell=True)

    time.sleep(2)

    # Connection between all nodes
    for i in range(NumberOfNodes):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 6000 + i))
            s.sendall(str(NumberOfNodes).encode())
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 6000 + i))
            s.sendall(b'a')

    for i in range(NumberOfEpoch):
        Transactions = int(input(f"Enter the number of transactions for epoch {i}:\n=> "))
        leader = generateRandomLeader(NumberOfNodes)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 6000 + leader))
            s.sendall(b'l')

        for i in range(Transactions):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('127.0.0.1', 6000 + leader))
                s.sendall(b't')
                
def generateRandomLeader(NumberOfNodes):
    leader_index = random.randint(0,NumberOfNodes)
    return leader_index
    
if __name__ == "__main__":
    main()