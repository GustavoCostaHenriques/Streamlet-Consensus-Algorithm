import datetime
import json
import time
import pickle
import socket
import sys
import threading
import Block
import Message
import Transaction
import hashlib
import random
import os
from colorama import Fore, Style, init

# Initialize colorama
#todo: ALTERAR ECHO DOS VOTES Echos n funcionam erro nonetyoe n tem epoch, n esta fixe rejoin 
init(autoreset=True)

class BlockchainNetworkNode:
    def __init__(self, node_id,host='127.0.0.1', port=5000, numOfNodes=0,numOfEpochs=0, delta=0,seed=0):
        initialBlock = Block.Block(previous_hash=0,hash=0,epoch=-1,length=0,transactions=[])
        self.host = host
        self.num_of_peers = int(numOfNodes)
        self.port = port
        self.node_id = node_id              # Unique identifier for the node
        self.blockchain = [initialBlock]    # Local blockchain for the node
        self.biggestNtChain = 0             
        self.pending_transactions = []      # Transactions pending to be included in a block
        self.current_epoch = 0              # Current epoch number
        self.numOfEpochs =int(numOfEpochs)
        self.notarized_blocks = []          # List of notarized blocks
        self.votes = []                      # Dictionary with Block --> Votes
        self.finalized_blocks = []          # List of finalized blocks
        self.biggest_finalized_block = []   # Biggest list of finalized blocks
        self.leader = False                 # Indicates if the node is the leader for the current epoch
        self.message_queue = []   
        self.echo_queue = []
        self.messages_to_read_queue = []          # Queue to store received messages
        self.peers = []         # List of peers connected to this node
        self.status =True              # Current status of the node
        self.lock = threading.Lock()
        self.delta = delta
        self.epochBlock = None
        self.didUpdateEpoch= False
        self.hashMapIdAdress={}
        self.hashMapIdSocket ={}
        self.seed =seed
        self.updated= False
        self.canFinalize=False
        self.receivedRejoin=[]
        self.rejoinData={'epoch':None,"lastBlockchain":None,"lastNotarized":None,"lastFinalized":None}
        self.ready=0
        self.rejoined= False

        threading.Thread(target=self.start_server, daemon=True).start()
        threading.Thread(target=self.finalize, daemon=True).start()

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen()
        while True:
            client_socket, address = server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

    def startEpoch(self, i ):
        if len(self.receivedRejoin)!=0:
                for id in self.receivedRejoin:
                    self.hashMapIdSocket[id]= None
        self.canFinalize=False
        received_time = datetime.datetime.now()
        formatted_time = received_time.strftime("%M:%S") + f".{received_time.microsecond // 1000:03d}"
        print(f"-----------------epoch {self.current_epoch} started at {formatted_time}---------------------")
        leader = self.generateLeader()
        print(f"leader is {leader}")
        if leader == self.node_id:
           print("I am the leader")
           self.leader=True
           time.sleep(0.2)
           self.advance_epoch()     

    def generateLeader(self):
        seed = int(hashlib.sha256(str(self.current_epoch).encode()).hexdigest(), 16)
        leader = seed % self.num_of_peers
        return leader
    

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
        # Ensure the socket is closed even if there's an error
            try:
                client_socket.close()
            except:
                pass    



    def process_message(self, message):
        message_type = message.msg_type
        data = message.content
        received_time = datetime.datetime.now()
        formatted_time = received_time.strftime("%M:%S") + f".{received_time.microsecond // 1000:03d}"
        print(f'Node {self.node_id} received {message_type} from {message.sender} and was received at {formatted_time}\n')
        if message_type=="Ready":
            self.ready+=1
            return
        if message_type == "RejoinResponse":
            if self.updated==False:
                self.updateToReceiveData(data,message.sender)
                self.updated=True
                return
        elif message_type=="Rejoin":
            #self.hashMapIdSocket[message.sender]= None
            self.processRejoin(data,message.sender)
            return

        if  (message_type=='Propose' or message_type=='Vote')and data.epoch> self.current_epoch:
            return
        if message_type =='Echo' and data.content.epoch> self.current_epoch:
            return 
        if message_type!='Echo':
            messageId = f"{message.msg_type}{message.content}{message.sender}"
        else:
            messageId = f"{data.msg_type}{data.content}{data.sender}"   

        if messageId in self.message_queue or messageId in self.echo_queue:
            return
        if message_type == 'Echo':
            self.echo_queue.append(messageId)  # Add Echo messages to echo_queue
        else:
            self.message_queue.append(messageId)
        if message_type == 'Propose':

            self.receivedRejoin=[]
            self.rejoinData={'epoch': None,'lastBlockchain':None,'lastNotarized':None,'lastFinalized':None}
            if data!=None:
                self.epochBlock= data
            print("block received")
            self.current_epoch = data.epoch 
            self.didUpdateEpoch=True          
            #self.broadcast_echo(message)
            if (self.biggestNtChain<len(message.longestChain)) or self.biggestNtChain==0 and len(message.longestChain)==0:
                self.biggestNtChain=len(message.longestChain)
                self.notarized_blocks=message.longestChain
                if message.sender not in self.votes:
                    self.votes.append(message.sender)
                self.vote_block(data)
            self.notorize_block_votes(data, message.sender)     
        elif message_type == 'Vote':
            #self.broadcast_echo(message)
            self.notorize_block_votes(data, message.sender)
        elif message_type == 'Echo':
            if data.msg_type=='Propose':
                self.current_epoch = data.content.epoch
                self.vote_block(data.content)
            elif data.msg_type=='Vote': 
                self.notorize_block_votes(data.content,data.sender)
        else: 
            return
        
    def updateToReceiveData(self,data,id):
        with self.lock:
            self.current_epoch = data.get("epoch",[])
            self.blockchain.extend(reversed(data.get("blockchain",[])))
            self.notarized_blocks.extend(reversed(data.get("notarized",[])))
            self.finalized_blocks.extend(reversed(data.get("finalized",[])))
        received_time = datetime.datetime.now()
        formatted_time = received_time.strftime("%M:%S") + f".{received_time.microsecond // 1000:03d}"
        print(f"-----------------epoch {self.current_epoch} started at {formatted_time}---------------------")    
        self.broadcastTo(Message.Message("Ready",None,self.node_id,None),id)
            
           

    def processRejoin(self, data,id):
        self.rejoinData["epoch"] = data.get('epoch')
        self.rejoinData["lastBlockchain"] = data.get('lastBlockBlockChain')
        self.rejoinData["lastNotarized"] = data.get('lastBlockNotarized')
        self.rejoinData["lastFinalized"] = data.get('lastFinalized')
        if self.rejoinData.get("epoch")< self.current_epoch:
            self.receivedRejoin.append(id)
            print(self.receivedRejoin)   

    """ def makeRejoinRespMessage(self):
        data={"epoch":None,"blockchain":None,"notarized": None, "finalized":None}
        filename = f"Node {self.node_id}"
        if not os.path.exists(filename):
            print("File does not exist")
            return
        with open(filename,"rb") as f:
            updatedNodeData = pickle.load(f)
            data["epoch"] = updatedNodeData.get("epoch", [])
            data["blockchain"] = self.processChain(updatedNodeData.get("blockchain", []),1)
            data["notarized"] = self.processChain(updatedNodeData.get("notarized", []),2)
            data["finalized"] = self.processChain(updatedNodeData.get("finalized", []),3)

        message = Message.Message("RejoinResponse",content=data,sender=self.node_id,longestChain=[])
        return message """
    
    def processChain(self,chain,num):
        processedChain=[]
        if num==1:
            processedChain = self.chainPrecidingGivenhash(self.rejoinData.get("lastBlockchain"),chain)
        elif num ==2:
            processedChain = self.chainPrecidingGivenhash(self.rejoinData.get("lastNotarized"),chain)
        elif num==3:
            processedChain = self.chainPrecidingGivenhash(self.rejoinData.get("lastFinalized"),chain)
        return processedChain
    
    def chainPrecidingGivenhash(self, hash, chain):
        if hash==None:
            return chain
        processedChain = []
        for i in reversed(range(len(chain))):
            if chain[i].hash == hash:
                break
            processedChain.append(chain[i])
        return processedChain
            


    def propose_block(self):
        self.generate_random_transaction()
        if not self.leader: # Not the leader of this epoch( Only the leader can propose a block)
            print(f"Node {self.node_id} is not the leader for epoch {self.current_epoch}")
            return 
    
        # Create a new block containing the pending transactions
        proposed_block = Block.Block(
            # Returns the hash of the last block ,if the list is empty , returns 0
            previous_hash=self.blockchain[-1].hash if self.blockchain else "0",  # Hash of the last block
            hash = 0, # this value serves just to create the block, it will be updated right away
            epoch=self.current_epoch,
            length=len(self.blockchain)+1,
            transactions=self.pending_transactions
            )
        self.votes.append(self.node_id)
        proposed_block.hash = proposed_block.calculate_hash()
        self.blockchain.append(proposed_block)
        for i in self.peers:
            if i in self.receivedRejoin:
                self.hashMapIdSocket[i] = None
                self.receivedRejoin.remove(i)
                self.broadcastTo(Message.Message(msg_type="RejoinResponse", content=self.makeRejoinData(), sender=self.node_id,longestChain=[]),i)
            while len(self.receivedRejoin)!= self.ready:
                continue   
            else:    
                self.broadcastTo(Message.Message(msg_type="Propose", content=proposed_block, sender=self.node_id,longestChain=self.notarized_blocks),i)

    def makeRejoinData(self):
        data={"epoch":None,"blockchain":None,"notarized": None, "finalized":None}
        filename = f"Node {self.node_id}"
        if not os.path.exists(filename):
            print("File does not exist")
            return
        with open(filename,"rb") as f:
            updatedNodeData = pickle.load(f)
            data["epoch"] = int(updatedNodeData.get("epoch", []))+1
            data["blockchain"] = self.processChain(updatedNodeData.get("blockchain", []),1)
            data["notarized"] = self.processChain(updatedNodeData.get("notarized", []),2)
            data["finalized"] = self.processChain(updatedNodeData.get("finalized", []),3)
        return data

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
        if self.node_id not in self.votes:
            self.votes.append(self.node_id)
        self.broadcast(Message.Message(msg_type="Vote", content=newBlock, sender=self.node_id,longestChain=[]))

    def notorize_block_votes(self, block,id):
        
        """Records a vote for a given block and checks if it is notarized.
        
        Args:
            block (Block): The block for which the vote is being recorded. 
                        This block should be an instance of the Block class.

        Returns:
            None"""
        
        with self.lock:
            if block in self.notarized_blocks:
                return
            if id not in self.votes:
                    self.votes.append(id)
            print(self.votes)
            if len(self.votes) > len(self.peers)/ 2:
                self.did_notorize=True
                epoch = block.epoch
                for blockInChain in self.blockchain:
                    if blockInChain.epoch == epoch:
                        if blockInChain not in self.notarized_blocks:
                            print(f"Node {self.node_id} notarized block {block.length}\n")
                            self.notarized_blocks.append(blockInChain)

    def finalize(self):
        while True:
            while self.canFinalize==True:
                if len(self.notarized_blocks)>=3 and (self.notarized_blocks[:-1] not in self.finalized_blocks):
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

    def send_message(self, node, message):
        if self.hashMapIdSocket[node] == -1:
            return
        if not message:
            print("Attempted to send an empty message.")
            return
        if self.hashMapIdSocket[node]==None:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(self.delta)
            self.hashMapIdSocket[node] = client_socket
            try:
                client_socket.connect(self.hashMapIdAdress[node])
            except ConnectionRefusedError:
                client_socket.close()
                print(f"Node {node} disconnected")    
        try:
            client_socket = self.hashMapIdSocket[node]
            serialized_message = pickle.dumps(message)
            message_length = len(serialized_message)
            client_socket.sendall(message_length.to_bytes(4, 'big') + serialized_message)
            received_time = datetime.datetime.now()
            formatted_time = received_time.strftime("%M:%S") + f".{received_time.microsecond // 1000:03d}"
            print(f"message {message.msg_type} from {message.sender} was sent at {formatted_time} from {self.current_epoch}")
        except Exception as e:
            self.hashMapIdSocket[node] = -1
            client_socket.close()
            #aqui
            print(f'Connection refused by {node}. The node may be offline.{e}')

    def broadcast(self, msg):
        print(f"Node {self.node_id} sent {msg.msg_type}\n")
        messageId = f"{msg.msg_type}{msg.content}{msg.sender}" 
        self.message_queue.append(messageId)
        for node in self.peers:
            threading.Thread(target=self.send_message(node,msg), daemon=True).start()
            #self.send_message(node, msg)

    def broadcastTo(self,msg,id):
        print(f"Node {self.node_id} sent {msg.msg_type} to {id}\n")
        messageId = f"{msg.msg_type}{msg.content}{msg.sender}" 
        self.message_queue.append(messageId)
        self.send_message(id, msg)

    def broadcast_echo(self, msg):
        print(f"Node {self.node_id} sent echo\n")
        messageId = f"{msg.msg_type}{msg.content}{msg.sender}"
        if messageId not in self.echo_queue: 
            self.echo_queue.append(messageId)
            for node in self.peers:
                threading.Thread(target=self.send_message(node,Message.Message(msg_type="Echo",content=msg,sender=self.node_id,longestChain=[])), daemon=True).start()
                #self.send_message(node,Message.Message(msg_type="Echo",content=msg,sender=self.node_id,longestChain=[],rejoinData=None))
    
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
        # Propose a block
        self.propose_block()

    def resetState(self):
        self.echo_queue=[]
        self.votes=[]
        self.pending_transactions=[]
        self.leader=False
        self.message_queue=[]
        self.epochBlock= None
        self.didUpdateEpoch=False    
        print()

    def updateFile(self):
        filename= f"Node {self.node_id}"
        node_data={
            "epoch" : self.current_epoch,
            "blockchain": self.blockchain,
            "notarized" :self.notarized_blocks,
            "finalized": self.finalized_blocks
        }
        with open(filename,'wb') as f:
            pickle.dump(node_data,f)

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

    def setAdressMap(self):
        with open("Sockets", "r") as socketsFile:
            # Iterate through each line in the file
            for line in socketsFile:
                # Strip the line of any extra spaces or newline characters
                line = line.strip()
                
                # Split the line into node_id and address part
                parts = line.split(":")
                
                if len(parts) == 2: 
                    node_id = int(parts[0])  
                    address = parts[1] 
                    ip, port = address.split(",")
                    port = int(port)
                    if node_id != self.node_id:
                        self.hashMapIdAdress[node_id] = (ip,port)

    def setSocketMap(self):
        if self.current_epoch==0:
            for i in range(self.num_of_peers):
                if i != self.node_id:
                    self.peers.append(i)
                    self.hashMapIdSocket[i]=None

    def updateNode(self):
        filename = f"Node {self.node_id}"
        if not os.path.exists(filename):
            print("File does not exist")
            return
        with open(filename,"rb") as f:
            if os.stat(filename).st_size!=0:
                updatedNodeData = pickle.load(f)
                self.current_epoch = updatedNodeData.get("epoch",[])
                self.blockchain= updatedNodeData.get("blockchain",[])
                self.notarized_blocks = updatedNodeData.get("notarized",[])
                self.finalized_blocks = updatedNodeData.get("finalized",[])
            print("Updated from file")
        return
    
    def rejoin(self):
        epoch = self.current_epoch
        lastBlockBlockChain = self.blockchain[len(self.blockchain)-1]
        lastBlockNotarized = self.notarized_blocks[len(self.notarized_blocks)-1]
        if len(self.finalized_blocks)!=0:
            lastFinalized = self.finalized_blocks[len(self.finalized_blocks)-1]
        else:
            lastFinalized=[]  
        if lastFinalized==[]:
             data = {"epoch":epoch,
                "lastBlockBlockChain": lastBlockBlockChain.hash,
                "lastBlockNotarized" : lastBlockNotarized.hash,
                "lastFinalized" : None
        }
        else:
            data = {"epoch":epoch,
                    "lastBlockBlockChain": lastBlockBlockChain.hash,
                    "lastBlockNotarized" : lastBlockNotarized.hash,
                    "lastFinalized" : lastFinalized.hash
            }
        self.broadcast(Message.Message("Rejoin",data,sender=self.node_id,longestChain=[]))
        while self.updated==False:
            continue

def main():
    infoFile = open("info","r")
    numberOfNodes = int(infoFile.readline())
    numberOfEpochs= int(infoFile.readline())
    delta = int(infoFile.readline())
    seed = int(infoFile.readline())
    node_id = int(sys.argv[1])
    port = int(sys.argv[2])
    if not os.path.exists(f"Node {node_id}"):
        name = f"Node {node_id}"
        createFile(name)  
        start_time_str = sys.argv[3]
        start_time = datetime.datetime.strptime(start_time_str, "%H:%M").time()
        current_time = datetime.datetime.now()
        start_time_today = datetime.datetime.combine(current_time.date(), start_time)
        if start_time_today <= current_time:
            print(f"The specified time {start_time_str} has already passed for today.")
            return
        delay = (start_time_today - current_time).total_seconds()
        threading.Timer(delay, start_epoch_thread, args=(node_id, port, numberOfNodes, numberOfEpochs, delta,seed)).start()
    else:
       node = BlockchainNetworkNode(node_id, "127.0.0.1", port,numberOfNodes,numberOfEpochs,delta,seed)
       node.setAdressMap()
       node.setSocketMap()
       node.updateNode()
       node.rejoin()
       print(node.current_epoch)
       node.finalized_blocks = reversed(node.finalized_blocks)
       print("updated to the newest version")
       startEpochRejoin(node)

def startEpochRejoin(node):
    time.sleep((2*node.delta)-1.155)
    node.canFinalize=True
    if len(node.receivedRejoin)!=0:
        for id in node.receivedRejoin:
            node.hashMapIdSocket[id]= None
    node.resetState()
    node.updateFile()
    received_time = datetime.datetime.now()
    formatted_time = received_time.strftime("%M:%S") + f".{received_time.microsecond // 1000:03d}"
    print(f"--------------epoch {node.current_epoch} ended at {formatted_time}---------------")
    for epoch in range(node.current_epoch+1, node.numOfEpochs):
            node.current_epoch = epoch
            threading.Thread(target=node.startEpoch, args=(epoch,), daemon=True).start()
            time.sleep(2*node.delta)
            node.canFinalize=True
            if len(node.receivedRejoin)!=0:
                for id in node.receivedRejoin:
                    node.hashMapIdSocket[id]= None
            node.resetState()
            node.updateFile()
            received_time = datetime.datetime.now()
            formatted_time = received_time.strftime("%M:%S") + f".{received_time.microsecond // 1000:03d}"
            print(f"--------------epoch {node.current_epoch} ended at {formatted_time}---------------")
    node.canFinalize=True
    node.resetState()
    node.print_chain(node.notarized_blocks)
    node.print_chain(node.finalized_blocks)
    os.remove(f"Node {node.node_id}")            
 
def createFile(name):
    with open(name,'w') as file:
        return   

def start_epoch_thread(node_id, port, numberOfNodes, numberOfEpochs, delta,seed):    
    node=BlockchainNetworkNode(node_id, "127.0.0.1", port,numberOfNodes,numberOfEpochs,delta,seed)
    createFile(f"Node {node_id}")
    received_time = datetime.datetime.now()
    formatted_time = received_time.strftime("%M:%S") + f".{received_time.microsecond // 1000:03d}"
    print(f"-----------------epoch {node.current_epoch} started at {formatted_time}---------------------")
    time.sleep(1)
    node.setAdressMap()
    print(node.hashMapIdAdress)
    node.setSocketMap()
    print(node.hashMapIdSocket)
    for i in range(numberOfEpochs):
        if i>0:
            time.sleep(2*delta)
            node.canFinalize=True
            node.resetState()
            node.updateFile()
            received_time = datetime.datetime.now()
            formatted_time = received_time.strftime("%M:%S") + f".{received_time.microsecond // 1000:03d}"
            print(f"--------------epoch {node.current_epoch} ended at {formatted_time}---------------")
        node.current_epoch=i
        threading.Thread(target=node.startEpoch, args=(i,), daemon=True).start()    
    time.sleep(2*delta)
    node.canFinalize=True
    node.resetState()
    node.print_chain(node.notarized_blocks)
    node.print_chain(node.finalized_blocks)
    os.remove(f"Node {node.node_id}")

if __name__ == "__main__":
        main()  
