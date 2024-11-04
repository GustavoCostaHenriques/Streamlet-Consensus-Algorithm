import json
import pickle
import socket
import threading
import time
import Block
import Message
import Transaction
import random


class BlockchainNetworkNode:
    def __init__(self, node_id,host='127.0.0.1', port=5000):
        initialBlock = Block.Block(previous_hash=0,epoch=0,length=0,transactions=0)
        self.host = host
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
        self.peers = []                     # List of peers connected to this node
        self.status = "active"              # Current status of the node
        self.lock = threading.Lock()

        threading.Thread(target=self.start_server, daemon=True).start()

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen()
        #print(f'Node {self.node_id} listening on {self.host}:{self.port}')

        while True:
            client_socket, address = server_socket.accept()
            print(f'Connection from {address}')
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

    def handle_client(self, client_socket):
        buffer = b''
        while True:
            try:
                part = client_socket.recv(1024)
                if not part:
                    break
                buffer += part
            except Exception as e:
                print(f'Error: {e}')
            break
        if buffer:
            message = pickle.loads(buffer)
            self.process_message(message)
        client_socket.close()

    def process_message(self, message):
        message_type = message.msg_type
        data = message.content
        if message_type!='Echo':
            messageId = f"{message.msg_type}{message.content}{message.sender}"
        else:
            messageId = f"{data.msg_type}{data.content}{data.sender}"   

        if(messageId in self.message_queue or data in self.message_queue):
            print(f"message already received {message_type} with {data.msg_type} and {data.sender}")      #check if the message is already in the queue
            return
        
        self.message_queue.append(messageId)
        if message_type=='EpochEnd':
            self.resetState()
            self.menu()
        elif message_type == 'Propose':
            print(f'Received propose')
            self.current_epoch = data.epoch
            self.broadcast_echo(message)
            if (self.biggestNtChain<len(message.longestChain)) or self.biggestNtChain==0 and len(message.longestChain)==0:
                self.biggestNtChain=len(message.longestChain)
                self.vote_block(data)
        elif message_type == 'Vote':
            print(f'Received Vote from {message.sender}')
            self.broadcast_echo(message)
            self.notorize_block_votes(data)
        elif message_type == 'Echo':
            print(f'Received echo {data.msg_type}" from "{message.sender}')
            if data.msg_type=='Propose':
                print(f'Received propose from { data.sender}')
                self.current_epoch = data.epoch
                self.vote_block(data.content)
            elif data.msg_type=='Vote':
                print(f'Received Vote from {data.sender}')
                self.notorize_block_votes(data.content)

    def propose_block(self):
        self.generate_random_transaction()
        if not self.leader: # Not the leader of this epoch( Only the leader can propose a block)
            print(f"Node {self.node_id} is not the leader for epoch {self.current_epoch}")
            return 
    
        # Create a new block containing the pending transactions
        proposed_block = Block.Block(
            # returns the hash of the last block ,if the list is empty , returns 0
            previous_hash=self.blockchain[-1].calculate_hash() if self.blockchain else "0",  # Hash of the last block
            epoch=self.current_epoch,
            length=len(self.blockchain) + 1,
            transactions=self.pending_transactions
            )
        print(len(self.notarized_blocks))
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
        
        # Check if the e proposed block index is bigger than the notarized chain
        #if block.length > len(self.notarized_blocks):
            #self.blockchain.append(block)
            
        # Broadcast the vote to all peers
        self.broadcast(Message.Message(msg_type="Vote", content=block, sender=self.node_id,longestChain=[]))
        print(f"Node {self.node_id} voted for block in epoch {self.current_epoch}.")

    def notorize_block_votes(self, block):
        
        """Records a vote for a given block and checks if it is notarized.
        
        Args:
            block (Block): The block for which the vote is being recorded. 
                        This block should be an instance of the Block class.

        Returns:
            None"""
        
        with self.lock():
            if block in self.notarized_blocks:
                print("block already notarized")
                return
            
            self.votes += 1 # Increment the vote counter for the block
            print(self.votes)
            # Check if the block has more than half of the votes
            if self.votes > len(self.peers)/ 2:
                print(threading.get_native_id())
                print(f"Node {self.node_id} notarized block {block.length}.")
                self.notarized_blocks.append(block)
        #self.check_blockchain_notarization()

    def finalize(self):
        if len(self._notarized_blocks)>=4:
            if self.notarized_blocks[len(self.notarized_blocks)-1].epoch == (self.notarized_blocks[len(self.notarized_blocks)-2].epoch)+1 and self.notarized_blocks[len(self.notarized_blocks)].epoch == (self.notarized_blocks[len(self.notarized_blocks)-3].epoch)+2:
                self.finalized_blocks = self.notarized_blocks[1:-1]
                self.compare_finalized_blocks()
        else:
            print("cant finalize len<4")

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
            print("The current finalized block list is now bigger than "
            "the previous biggest.The bigger list was updated.")
            print(f"Current finalized blocks: {self.finalized_blocks}")
        
        else:
            print("The biggest finalized block list is still bigger than the current finalized blocks.")
            print(f"Biggest finalized blocks: {self.biggest_finalized_block}")

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
                client_socket.sendall(serialized_message)
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
        print(f"sent {msg.msg_type} , {msg.content}")
        for node in self.peers:
            messageId = f"{msg.msg_type}{msg.content}{msg.sender}" 
            self.message_queue.append(messageId)
            self.send_message(node,msg)

    def broadcast_echo(self, msg):
        print("sent echo")
        for node in self.peers:
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
            print(f"Node {self.node_id} added transaction {transaction.transaction_id}.")
        else:
            print(f"Node {self.node_id} failed to add transaction: Not a valid Transaction object.")

    def generate_random_transaction(self):

        """Generates and adds a random transaction."""

        # Simulação simples de transação
        transaction = Transaction.Transaction(sender=self.node_id, receiver=random.randint(1, 3), transaction_id=random.randint(1000, 9999), amount=random.uniform(1.0, 100.0))
        self.add_transaction(transaction)

    def advance_epoch(self):
        self.current_epoch += 1
        print(f"Node {self.node_id} will advance to epoch {self.current_epoch}.")
        
        # Start the epoch process in a separate thread
        self.run_epoch_process()
        
    def run_epoch_process(self):
        """Handles the epoch process and enforces a time limit."""
        self.leader = True  # Assign leader status for this epoch
        
        # Propose a block
        self.propose_block()
        
        # Wait for 2 seconds to complete the epoch process
        time.sleep(2)
        
        # End of the epoch process, reset leader status
        self.resetState()
        self.broadcast(Message.Message(msg_type="EpochEnd", content=self.current_epoch, sender=self.node_id,longestChain=[]))
        print(f"Node {self.node_id} has completed epoch {self.current_epoch}.")
        self.menu()

    def resetState(self):
        self.votes=0
        self.pending_transactions=[]
        self.leader=False
        self.message_queue=[]

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

    def menu(self):
        inp = input("enter command: l- assign leader, e- start epoch ,b-notarized blocks,f-finalize,bl-blockchain ")
        if inp =='l':
            self.leader = True 
        elif inp =='e':
            self.advance_epoch() 
        elif inp =='b':
            for block in self.notarized_blocks:
                print(str(block.epoch) + " "+ str(block.transactions))
        elif inp =='f':
            self.finalize()
        elif inp =='bl':
            print(self.blockchain)
def main():
    
    var = input("pls enter the node id: ")
    if var=='1':
        node = BlockchainNetworkNode(var,"127.0.0.1" , 5000)
    elif var=='2':
        node = BlockchainNetworkNode(var,"127.0.0.1" , 5001)
    elif var=='3':
        node = BlockchainNetworkNode(var,"127.0.0.1" , 5002)
    port = input("port")       
    if port=='1':
        node.add_node(("127.0.0.1" , int(5001)))
        node.add_node(("127.0.0.1" , int(5002)))
    elif port=='2':
        node.add_node(("127.0.0.1" , int(5000)))
        node.add_node(("127.0.0.1" , int(5002)))
    elif port=='3':
        node.add_node(("127.0.0.1" , int(5000)))
        node.add_node(("127.0.0.1" , int(5001)))

    while True:
        node.menu()

if __name__ == "__main__":
        main()    