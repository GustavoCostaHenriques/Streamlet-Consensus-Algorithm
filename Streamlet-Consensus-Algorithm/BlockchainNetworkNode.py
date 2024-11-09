import json
import pickle
import socket
import sys
import threading
import Block
import Message
import Transaction
import random
import os
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class BlockchainNetworkNode:
    def __init__(self, node_id,host='127.0.0.1', port=5000):
        initialBlock = Block.Block(previous_hash=0,hash=0,epoch=0,length=0,transactions=[])
        self.host = host
        self.num_of_peers= 0
        self.port = port
        self.node_id = node_id              # Unique identifier for the node
        self.blockchain = [initialBlock]    # Local blockchain for the node
        self.biggestNtChain = 0             
        self.pending_transactions = []      # Transactions pending to be included in a block
        self.current_epoch = 0              # Current epoch number
        self.notarized_blocks = []          # List of notarized blocks
        self.votes = 0                      # Dictionary with Block --> Votes
        self.finalized_blocks = []          # List of finalized blocks
        self.biggest_finalized_block = []   # Biggest list of finalized blocks
        self.leader = False                 # Indicates if the node is the leader for the current epoch
        self.message_queue = []             # Queue to store received messages
        self.peers = [(host, port)]         # List of peers connected to this node
        self.status = "active"              # Current status of the node
        self.lock = threading.Lock()
        self.delta = 0
        self.epochBlock = None

        threading.Thread(target=self.start_server, daemon=True).start()
        threading.Thread(target=self.finalize, daemon=True).start()
        self.command_listener()

    def command_listener(self):
        command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        command_socket.bind((self.host, self.port + 1000))  # Usa uma porta diferente para o comando
        command_socket.listen(1)

        while True:
            conn, addr = command_socket.accept()
            command = conn.recv(1024).decode()
            if command:
                self.menu(command)
            conn.close()

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen()

        while True:
            client_socket, address = server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

    def handle_client(self, client_socket):
        buffer = b''  # Temporary buffer to store received data

        try:
            while True:
                # Receive a chunk of data and add it to the buffer
                part = client_socket.recv(2048)
                if not part:
                    break
                buffer += part

                # Check if we have enough data to read the message length
                if len(buffer) < 4:
                    continue  # Keep receiving until we have at least 4 bytes for the length

                # Read the message length from the first 4 bytes
                message_length = int.from_bytes(buffer[:4], 'big')
                
                # Check if the full message has been received
                if len(buffer) >= message_length + 4:
                    # Extract the full message
                    message_data = buffer[4:message_length + 4]
                    message = pickle.loads(message_data)
                    
                    # Process the message
                    self.process_message(message)
                    
                    # Clear the buffer of the processed message
                    buffer = buffer[message_length + 4:]
        except Exception as e:
            print(f'Error processing client: {e}')
        finally:
            client_socket.close()

    def process_message(self, message):
        message_type = message.msg_type
        data = message.content
        if message_type!='Echo':
            messageId = f"{message.msg_type}{message.content}{message.sender}"
        else:
            messageId = f"{data.msg_type}{data.content}{data.sender}"   

        if(messageId in self.message_queue or data in self.message_queue):
            #check if the message is already in the queue
            return
        
        self.message_queue.append(messageId)
        if message_type == 'Propose':
            self.epochBlock= data
            print(f'Node {self.node_id} received Propose from {message.sender}\n')
            self.current_epoch = data.epoch           
            self.broadcast_echo(message)
            if (self.biggestNtChain<len(message.longestChain)) or self.biggestNtChain==0 and len(message.longestChain)==0:
                self.biggestNtChain=len(message.longestChain)
                self.notarized_blocks=message.longestChain
                self.vote_block(data)
            self.notorize_block_votes(data) 
        elif message_type == 'Vote':
            print(f'Node {self.node_id} received Vote from {message.sender}\n')
            self.broadcast_echo(message)
            self.notorize_block_votes(data)
        elif message_type == 'Echo':
            print(f'{self.node_id} received echo {data.msg_type} from {message.sender}\n')
            if data.msg_type=='Propose':
                print(f'{self.node_id} received propose in the Echo from { data.sender}\n')
                self.current_epoch = data.content.epoch
                self.vote_block(data.content)
            elif data.msg_type=='Vote':
                print(f'{self.node_id} received Vote in the Echo from {data.sender}\n')
                self.notorize_block_votes(data.content)
        else: 
            return            

    def propose_block(self):
        if not self.leader: # Not the leader of this epoch( Only the leader can propose a block)
            print(f"Node {self.node_id} is not the leader for epoch {self.current_epoch}")
            return 
    
        # Create a new block containing the pending transactions
        proposed_block = Block.Block(
            # Returns the hash of the last block ,if the list is empty , returns 0
            previous_hash=self.blockchain[-1].hash if self.blockchain else "0",  # Hash of the last block
            hash = 0, # this value serves just to create the block, it will be updated right away
            epoch=self.current_epoch,
            length=len(self.blockchain),
            transactions=self.pending_transactions
            )
        proposed_block.hash = proposed_block.calculate_hash()
        self.blockchain.append(proposed_block)
        self.broadcast(Message.Message(msg_type="Propose", content=proposed_block, sender=self.node_id,longestChain=self.notarized_blocks))

    def vote_block(self, block):
        
        """Votes for a proposed block if it extends the longest notarized chain.

        Args:
            block (Block): The proposed block to vote for.

        Returns:
        None """
        
        # Check if the block is valid for voting
        if len(block.transactions) == 0:
            print(f"Node {self.node_id} cannot vote for an empty block.")
            return 
            
        self.blockchain.append(self.epochBlock) # Append the block received to the blockChain
        newBlock = Block.Block(
            # Returns the hash of the last block ,if the list is empty , returns 0
            previous_hash=block.previous_hash,  # Hash of the last block
            hash=block.hash, 
            epoch=block.epoch,
            length=block.length,
            transactions=[]
            )
        
        # Broadcast the vote to all peers
        self.broadcast(Message.Message(msg_type="Vote", content=newBlock, sender=self.node_id,longestChain=[]))

    def notorize_block_votes(self, block):
        
        """Records a vote for a given block and checks if it is notarized.
        
        Args:
            block (Block): The block for which the vote is being recorded. 
                        This block should be an instance of the Block class.

        Returns:
            None"""
        
        with self.lock:
            if block in self.notarized_blocks:
                return
            
            self.votes += 1 # Increment the vote counter for the block
            # Check if the block has more than half of the votes
            if self.votes > len(self.peers)/ 2:
                self.did_notorize=True
                epoch = block.epoch
                for blockInChain in self.blockchain:
                    if blockInChain.epoch == epoch:
                        if blockInChain not in self.notarized_blocks:
                            print(f"Node {self.node_id} notarized block {block.length}\n")
                            self.notarized_blocks.append(blockInChain)

    def finalize(self):
        while True:
            if len(self._notarized_blocks)>=3 and (self.notarized_blocks[:-1] not in self.finalized_blocks):
                if self.notarized_blocks[len(self.notarized_blocks)-1].epoch == (self.notarized_blocks[len(self.notarized_blocks)-2].epoch)+1 and self.notarized_blocks[len(self.notarized_blocks)-1].epoch == (self.notarized_blocks[len(self.notarized_blocks)-3].epoch)+2:
                    self.finalized_blocks = self.notarized_blocks[:-1]
                    self.compare_finalized_blocks()

    def compare_finalized_blocks(self):
        
        """Compares the length of `finalized_blocks` and `biggest_finalized_block`,
            and prints which one is bigger. Updates `biggest_finalized_block` if 
            `finalized_blocks` becomes larger. Also prints the contents of the bigger list.

            Returns:
                None"""
        
    
        # Compare the lengths of the two lists
        if len(self.finalized_blocks) > len(self.biggest_finalized_block):
            # Update the biggest finalized block if finalized_blocks is larger
            self.biggest_finalized_block = self.finalized_blocks.copy()
            print(f"Node {self.node_id} finalized block {self.finalized_blocks[-1].length} and it's parent chain\n")
    

    def check_blockchain_notarization(self):
        
        """Verifies if the entire blockchain (except the genesis block(first block)) is notarized.
    
        If the chain is fully notarized, it is marked as valid.
    
        Returns:
        None"""
    
        #Iterate the blockchain's list
        for block in self.blockchain[1:]:  # Igonores the genesis block
            if block not in self.notarized_blocks:
                print(f"Node {self.node_id}: Blockchain is not fully notarized yet.")
                return
        print(f"Node {self.node_id}: Blockchain is fully notarized and valid.")

    def add_node(self, node_address):
        if node_address not in self.peers:
            self.peers.append(node_address)

    def send_message(self, node_address, message):
        if not message:
            print("Attempted to send an empty message.")
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect(node_address)
                serialized_message = pickle.dumps(message)
                message_length = len(serialized_message)
                # Send first the length of the message, then the message
                client_socket.sendall(message_length.to_bytes(4, 'big') + serialized_message)
        except ConnectionRefusedError:
            print(f'Connection refused by {node_address}. The node may be offline.')
        except socket.error as e:
            print(f'Socket error occurred: {e}')
        except json.JSONDecodeError:
            print('Error encoding the message to JSON. Check the message structure.')
        except TypeError as e:
            print(f'Type error occurred: {e}. This may indicate an issue with message serialization.')
        except Exception as e:
            print(f'An unexpected error occurred: {e}')

    def broadcast(self, msg):
        print(f"Node {self.node_id} sent {msg.msg_type}\n")
        for node in self.peers[1:]:
            messageId = f"{msg.msg_type}{msg.content}{msg.sender}" 
            self.message_queue.append(messageId)
            self.send_message(node,msg)

    def broadcast_echo(self, msg):
        print(f"Node {self.node_id} sent echo\n")
        for node in self.peers[1:]:
            messageId = f"{msg.msg_type}{msg.content}{msg.sender}" 
            self.message_queue.append(messageId)
            self.send_message(node,Message.Message(msg_type="Echo",content=msg,sender=msg.sender,longestChain=[]))

    def __repr__(self):
        return (f"BlockchainNetworkNode(node_id={self.node_id}, current_epoch={self.current_epoch}, "
                f"blockchain_length={len(self.blockchain)}, pending_tx={len(self.pending_transactions)}, "
                f"biggest_finalized_block={len(self.biggest_finalized_block)}, leader={self.leader}, status={self.status})")
    
    def add_transaction(self, transaction):
        
        """ Adds a transaction to the pending transactions list.

        Args:
            transaction (Transaction): The transaction to be added.

        Returns:
            None """
        
        if isinstance(transaction, Transaction.Transaction):
            self.pending_transactions.append(transaction)
            print(f"Node {self.node_id} added transaction {transaction.transaction_id}")
        else:
            print(f"Node {self.node_id} failed to add transaction: Not a valid Transaction object.")

    def generate_random_transaction(self):

        """Generates and adds a random transaction."""

        # Simulates a simple transaction
        transaction = Transaction.Transaction(sender=self.node_id, receiver=random.randint(1, len(self.peers)), transaction_id=random.randint(1000, 9999), amount=random.uniform(1.0, 100.0))
        self.add_transaction(transaction)

    def advance_epoch(self):
        self.current_epoch += 1        
        # Propose a block
        self.propose_block()

    def resetState(self):
        self.votes=0
        self.pending_transactions=[]
        self.leader=False
        self.message_queue=[]
        self.epochBlock= None
        self.print_info_divider(f"Epoch {self.current_epoch - 1} ended", Fore.CYAN)
        print()

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value):
        self._host = value

    # Getter and Setter for port
    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = value

    # Getter and Setter for node_id
    @property
    def node_id(self):
        return self._node_id

    @node_id.setter
    def node_id(self, value):
        self._node_id = value

    # Getter and Setter for blockchain
    @property
    def blockchain(self):
        return self._blockchain

    @blockchain.setter
    def blockchain(self, value):
        self._blockchain = value

    # Getter and Setter for pending_transactions
    @property
    def pending_transactions(self):
        return self._pending_transactions

    @pending_transactions.setter
    def pending_transactions(self, value):
        self._pending_transactions = value

    # Getter and Setter for current_epoch
    @property
    def current_epoch(self):
        return self._current_epoch

    @current_epoch.setter
    def current_epoch(self, value):
        self._current_epoch = value

    # Getter and Setter for notarized_blocks
    @property
    def notarized_blocks(self):
        return self._notarized_blocks

    @notarized_blocks.setter
    def notarized_blocks(self, value):
        self._notarized_blocks = value

    # Getter and Setter for votes
    @property
    def votes(self):
        return self._votes

    @votes.setter
    def votes(self, value):
        self._votes = value

    # Getter and Setter for finalized_blocks
    @property
    def finalized_blocks(self):
        return self._finalized_blocks

    @finalized_blocks.setter
    def finalized_blocks(self, value):
        self._finalized_blocks = value

    # Getter and Setter for biggest_finalized_block
    @property
    def biggest_finalized_block(self):
        return self._biggest_finalized_block

    @biggest_finalized_block.setter
    def biggest_finalized_block(self, value):
        self._biggest_finalized_block = value

    # Getter and Setter for leader
    @property
    def leader(self):
        return self._leader

    @leader.setter
    def leader(self, value):
        self._leader = value

    # Getter and Setter for message_queue
    @property
    def message_queue(self):
        return self._message_queue

    @message_queue.setter
    def message_queue(self, value):
        self._message_queue = value

    # Getter and Setter for peers
    @property
    def peers(self):
        return self._peers

    @peers.setter
    def peers(self, value):
        self._peers = value

    # Getter and Setter for status
    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    def menu(self, inp):
        if inp =='t':
            self.generate_random_transaction()
        elif inp == 'p':
            self.print_info_divider(f"Epoch {self.current_epoch} will start", Fore.CYAN)
            print()
        elif inp == 'a':
            for i in range(self.num_of_peers):
                if (self.port!=5000+i):
                    self.add_node(("127.0.0.1" , 5000+i))
        elif inp == 'l':
            print("This node is the leader")
            self.leader = True 
        elif inp == 's':
            self.advance_epoch() 
        elif inp == "e":
            self.resetState()
        elif inp =='b':
            self.print_info_divider(f"Notarized chain of node {self.node_id}", Fore.YELLOW)
            self.print_chain(self.notarized_blocks)
            self.print_info_divider(f"End of notarized chain of node {self.node_id}", Fore.YELLOW)
            print()
        elif inp =='f':
            self.print_info_divider(f"Finalized chain of node {self.node_id}", Fore.RED)
            self.print_chain(self.finalized_blocks)
            self.print_info_divider(f"End of finalized chain of node {self.node_id}", Fore.RED)
            print()
        elif inp =='bl':
            self.print_info_divider(f"BlockChain of node {self.node_id}", Fore.BLUE)
            self.print_chain(self.blockchain)
            self.print_info_divider(f"End of BlockChain of node {self.node_id}", Fore.BLUE)
            print()
        else:
            self.num_of_peers = int(inp)
            
    def print_chain(self, chain):
        print()
        for block in chain:
            print(f"Block with epoch {block.epoch}, length {block.length}, hash {block.hash[:8] if block.hash != 0 else block.hash } and previous hash {block.previous_hash[:8] if block.previous_hash != 0 else block.previous_hash} has {len(block.transactions)} transactions:")
            transcationNumber = 1
            for transaction in block.transactions:
                print(f"\t Transaction {transcationNumber} [ID-{transaction.transaction_id} Sender-{transaction.sender} Receiver-{transaction.receiver} Amount:{transaction.amount:.2f}]")
                transcationNumber += 1
            print()
        
    def print_info_divider(self, text="", color=Fore.RED):   
        columns, _ = os.get_terminal_size()
        if text:
            # Calculate the padding on each side of the text to center it
            padding = (columns - len(text) - 2) // 2  # Subtract 2 to account for spaces around the text
            if padding > 0:
                print(color + '-' * padding + f" {text} " + '-' * padding + Style.RESET_ALL)
            else:
                print(color + text + Style.RESET_ALL)  # In case the text is wider than the terminal width
        else:
            print(color + '-' * columns + Style.RESET_ALL)

def main():
    if len(sys.argv) != 3:
        print("Usage: BlockchainNetworkNode.py <node_id> <port>")
        return

    node_id = int(sys.argv[1])
    port = int(sys.argv[2])
    BlockchainNetworkNode(node_id, "127.0.0.1", port)

if __name__ == "__main__":
        main()  

            
""" def main():
    var = int(input("pls enter the node id: "))
    node = BlockchainNetworkNode(var,"127.0.0.1" , 5000+var)
    
    port = int(input("number of nodes"))
    for i in range(port):
        if (5000+var!=5000+i):
            node.add_node(("127.0.0.1" , 5000+i))

    while True:
        node.menu()
 """
""" if __name__ == "__main__":
        main()                 """