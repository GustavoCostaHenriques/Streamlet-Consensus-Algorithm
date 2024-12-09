import datetime
import json
import time
import pickle
import socket
import sys
import threading
import traceback
import Block
import Message
import Transaction
import hashlib
import random
import os
import queue
from colorama import Fore, Style, init

# Initialize colorama
#todo: ALTERAR ECHO DOS VOTES Echos n funcionam erro nonetyoe n tem epoch(acho que ta fixe), se no crashar no primeira epoca mandar none , erro estanho em que n manda msg 
init(autoreset=True)

class BlockchainNetworkNode:
    def __init__(self, node_id,confusion_start,confusion_duration,host='127.0.0.1', port=5000, numOfNodes=0,numOfEpochs=0, delta=0):
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
        self.leader = False                 # Indicates if the node is the 
        self.echo_queue = []
        self.message_queue=[]
        self.peers = []         # List of peers connected to this node
        self.status =True              # Current status of the node
        self.lock = threading.Lock()
        self.delta = delta
        self.epochBlock = None
        self.didUpdateEpoch= False
        self.hashMapIdAdress={}
        self.hashMapIdSocket ={}
        self.updated= False
        self.canFinalize=False
        self.receivedRejoin=[]
        self.rejoinData={'epoch':None,"lastBlockchain":None,"lastNotarized":None,"lastFinalized":None}
        self.ready=0
        self.rejoined= False
        self.confusion_start = int(confusion_start)
        self.confusion_duration =  int(confusion_duration)
        self.receivedForkReq=[]

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
        if leader == self.node_id:
           print("I am the leader")
           self.leader=True
           time.sleep(0.2)
           self.advance_epoch() 
        else:
            print(f"Leader is {leader}")


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
                    if self.current_epoch < self.confusion_start or self.current_epoch > self.confusion_start+self.confusion_duration-1:
                        self.process_message(message)
                    
                    # Clear the buffer of the processed message
                    buffer = buffer[message_length + 4:]

        except Exception as e:
            print(f'Error processing client: {e}')
            traceback.print_exc()

        finally:
        # Ensure the socket is closed even if there's an error
            try:
                client_socket.close()
            except:
                pass    


    def compareChains(self,data,type):
        if type==1:
            if data==self.blockchain:
                return
            with self.lock:
                self.blockchain=self.cmp(self.blockchain,data)
            
        elif type==2:
            if data ==self.notarized_blocks:
                return
            with self.lock:
                self.notarized_blocks=self.cmp(self.notarized_blocks,data)
            
        elif type==3:
            if data == self.finalized_blocks:
                return
            with self.lock:
                self.finalized_blocks=self.cmp(self.finalized_blocks,data)
            
    def cmp(self,node_chain,received_chain):
        if(received_chain == None):
            return node_chain
        if len(received_chain)>len(node_chain):
            return received_chain
        if len(received_chain)<len(node_chain):
            return node_chain
        node_index = 0
        received_index = 0
        newChain=[]
        while node_index < len(node_chain) and received_index < len(received_chain):
            node_block = node_chain[node_index]
            received_block = received_chain[received_index]
            if node_block.epoch == received_block.epoch:
                node_index += 1
                received_index += 1
                newChain.append(node_block)
            elif node_block.epoch < received_block.epoch:
                newChain.append(node_block)
                newChain.append(received_block)
                received_index += 1
                node_index +=1
            elif node_block.epoch > received_block.epoch:  
                newChain.append(received_block)   
                newChain.append(node_block)
                received_index += 1
                node_index +=1

        return newChain
    
    def process_message(self, message):
        message_type = message.msg_type
        data = message.content
        print(f'Node {self.node_id} received {message_type} from {message.sender}')
        if message_type =="ForkCheck":
            self.compareChains(data.get("blockchain"),1)
            self.compareChains(data.get("notorized"),2)
            self.compareChains(data.get("finalized"),3)
            return
        if message_type=="Ready":
            self.ready= self.ready+1
            return
        if message_type == "RejoinResponse":
            if self.updated==False:
                self.updateToReceiveData(data,message.sender)
                self.updated=True
                return
        elif message_type=="Rejoin":
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
            self.notorize_block_votes(data, message.sender)
            #self.broadcast_echo(message)
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
            print(f"Received rejoin request from node {id}")
    
    def processChain(self,chain,num):
        processedChain=[]
        if num==1:
            processedChain = self.chainPrecidingGivenHash(self.rejoinData.get("lastBlockchain"),chain)
        elif num ==2:
            processedChain = self.chainPrecidingGivenHash(self.rejoinData.get("lastNotarized"),chain)
        elif num==3:
            processedChain = self.chainPrecidingGivenHash(self.rejoinData.get("lastFinalized"),chain)
        return processedChain
    
    def chainPrecidingGivenHash(self, hash, chain):
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
        sentRejoinResponse=False
        for i in self.receivedRejoin:
            self.broadcastTo(Message.Message(msg_type="RejoinResponse", content=self.makeRejoinData(), sender=self.node_id,longestChain=[]),i)
            sentRejoinResponse= True
        if sentRejoinResponse==True:       
            while len(self.receivedRejoin)!= self.ready:
                continue
        self.receivedRejoin=[]
        self.ready=0
        for i in self.peers:
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
            print(f"Votes received: {self.votes}")
            if len(self.votes) > len(self.peers)/ 2:
                self.did_notorize=True
                epoch = block.epoch
                for blockInChain in self.blockchain:
                    if blockInChain==None:
                        continue
                    else:
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
        except Exception as e:
            self.hashMapIdSocket[node] = -1
            client_socket.close()
            print(f'Connection refused by {node}. The node may be offline.{e}')

    def broadcast(self, msg):
        print(f"Node {self.node_id} sent {msg.msg_type}\n")
        messageId = f"{msg.msg_type}{msg.content}{msg.sender}" 
        self.message_queue.append(messageId)
        for node in self.peers:
            threading.Thread(target=self.send_message(node,msg), daemon=True).start()

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
        
        lastBlockBlockChain = self.blockchain[-1] if self.blockchain else self.blockchain[0]
        lastBlockNotarized = self.notarized_blocks[-1] if self.notarized_blocks else []
        lastFinalized = self.finalized_blocks[-1] if self.finalized_blocks else []

        # Prepare the data dictionary
        data = {
            "epoch": epoch,
            "lastBlockBlockChain": lastBlockBlockChain.hash,
            "lastBlockNotarized": lastBlockNotarized.hash if lastBlockNotarized else None,
            "lastFinalized": lastFinalized.hash if lastFinalized else None
        }

        # Broadcast the message
        self.broadcast(Message.Message("Rejoin", data, sender=self.node_id, longestChain=[]))

        # Wait until the state is updated
        while not self.updated:
            pass

    def checkForFork(self):
        data={"blockchain": self.blockchain,
              "notarized": self.notarized_blocks,
              "finalized": self.finalized_blocks}
        self.broadcast(Message.Message("ForkCheck",data,self.node_id,len(self.blockchain)))
        time.sleep(0.5)

def main():
    try:
        infoFile = open("info","r")
        numberOfNodes = int(infoFile.readline())
        numberOfEpochs= int(infoFile.readline())
        delta = int(infoFile.readline())
        node_id = int(sys.argv[1])
        port = int(sys.argv[2])
        if not os.path.exists(f"Node {node_id}"):
            name = f"Node {node_id}"
            createFile(name)  
            start_time_str = sys.argv[3]
            confusion_start = sys.argv[4]
            confusion_duration = sys.argv[5]
            start_time = datetime.datetime.strptime(start_time_str, "%H:%M").time()
            current_time = datetime.datetime.now()
            start_time_today = datetime.datetime.combine(current_time.date(), start_time)
            if start_time_today <= current_time:
                print(f"The specified time {start_time_str} has already passed for today.")
                return
            delay = (start_time_today - current_time).total_seconds()
            threading.Timer(delay, start_epoch_thread, args=(node_id, port, numberOfNodes, numberOfEpochs, delta,confusion_start,confusion_duration)).start()
        else:
            node = BlockchainNetworkNode(node_id,0,0,"127.0.0.1", port,numberOfNodes,numberOfEpochs,delta)
            node.setAdressMap()
            node.setSocketMap()
            node.updateNode()
            node.rejoin()
            print("updated to the newest version")
            startEpochRejoin(node)
    except KeyboardInterrupt:
           os.remove(f"Node {node.node_id}") 
           print("Simulation will end")

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
    node.checkForFork()
    node.print_chain(node.blockchain)
    node.print_chain(node.notarized_blocks)
    node.print_chain(node.finalized_blocks)
    os.remove(f"Node {node.node_id}")
    time.sleep(5)            
 
def createFile(name):
    with open(name,'w') as file:
        return   

def start_epoch_thread(node_id, port, numberOfNodes, numberOfEpochs, delta,confusion_start,confusion_duration):    
    node=BlockchainNetworkNode(node_id,confusion_start ,confusion_duration,"127.0.0.1", port,numberOfNodes,numberOfEpochs,delta)
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
    node.checkForFork()
    node.print_chain(node.blockchain)
    node.print_chain(node.notarized_blocks)
    node.print_chain(node.finalized_blocks)
    os.remove(f"Node {node.node_id}")
    time.sleep(5)

if __name__ == "__main__":
        main()  
