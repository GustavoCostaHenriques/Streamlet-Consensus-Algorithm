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
            communicate_with_node(i, NumberOfNodes)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            communicate_with_node(i, 'a')
            
    print()
    print_simulation_divider("Start of simulation")
    print()
    print()

    for i in range(NumberOfEpoch):
        Transactions = int(input(f"Enter the number of transactions for epoch {i}:\n=> "))
        leader = generateRandomLeader(NumberOfNodes - 1)

        print()
        print_epoch_divider(f"Epoch {i} will start")
        for k in range(NumberOfNodes):
            communicate_with_node(k, 'p')
        print()
        print(f"The leader for epoch {i} is node {leader}.")
        
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            communicate_with_node(leader, 'l')

        start = time.time()

        for _ in range(Transactions):
            communicate_with_node(leader, 't')
            
        communicate_with_node(leader, 's')      
          
        while(time.time() - start < Delta):
            continue
        print()
        print_epoch_divider(f"Epoch {i} ended")
        
        for j in range(NumberOfNodes):
            communicate_with_node(j, 'e')
        print()
        
        Info = int(input("If you want to go to the next epoch please insert -1.\n" 
                         "If not, please insert the number of the node you want to check:\n=> "))
        
        if(Info == -1):
            print()
            continue
        
        else:
            print()
            Letter = input(f"Node {Info} selected.\n" 
                         "If you want to see the notarized blocks insert 'N'.\n"
                         "If you want to see the finalized blocks insert 'F'.\n"
                         "If you want to see the entire blockChain insert 'B'.\n"
                         "If you want to go to the next epoch insert 'E'.:\n=> ")
            while(Letter != 'E'):
                print(f"Please look at the replica {Info} to see what you asked for!\n")
                if (Letter == 'N'):
                    print()
                    communicate_with_node(Info, 'b')
                elif(Letter == 'F'):
                    print()
                    communicate_with_node(Info, 'f')
                elif(Letter == 'B'):
                    print()
                    communicate_with_node(Info, 'bl')
                else:
                    Info = int(Letter)

                print()
                Letter = input(f"Node {Info} selected.\n" 
                         "If you want to see the notarized blocks insert 'N'.\n"
                         "If you want to see the finalized blocks insert 'F'.\n"
                         "If you want to see the entire blockChain insert 'B'.\n"
                         "If you want to see another node, insert the number you want to see.\n"
                         "If you want to go to the next epoch insert 'E'.:\n=> ")
            print() 
                            
    print()
    print_simulation_divider("End of simulation")
    print()
    print()
                
def communicate_with_node(port, letter):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('127.0.0.1', 6000 + port))
                s.sendall(str(letter).encode())
                
def generateRandomLeader(NumberOfNodes):
    leader_index = random.randint(0,NumberOfNodes)
    return leader_index

def print_epoch_divider(text=""):
    columns, _ = os.get_terminal_size()
    if text:
        # Calculate the padding on each side of the text to center it
        padding = (columns - len(text) - 2) // 2  # Subtract 2 to account for spaces around the text
        if padding > 0:
            print(Fore.CYAN + '-' * padding + f" {text} " + '-' * padding + Style.RESET_ALL)
        else:
            print(Fore.CYAN + text + Style.RESET_ALL)  # In case the text is wider than the terminal width
    else:
        print(Fore.CYAN + '-' * columns + Style.RESET_ALL)

def print_simulation_divider(text=""):
    columns, _ = os.get_terminal_size()
    if text:
        padding = (columns // 2) - (len(text) // 2) - 2
        if padding > 0:
            print(Fore.GREEN + '*' * columns)
            print(Fore.GREEN + '*' + ' ' * (columns - 2) + '*')
            print(Fore.GREEN + '*' + ' ' * padding + f"{text}" + ' ' * padding + ' *')
            print(Fore.GREEN + '*' + ' ' * (columns - 2) + '*')
            print(Fore.GREEN + '*' * columns + Style.RESET_ALL)
        else:
            print(Fore.GREEN + '*' * columns)
            print(f"{text}")
            print('*' * columns + Style.RESET_ALL)
    else:
        print(Fore.GREEN + '*' * columns + Style.RESET_ALL)
    
if __name__ == "__main__":
    main()