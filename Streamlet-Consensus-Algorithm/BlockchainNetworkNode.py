import Block
import Message
import Transaction
import random


class BlockchainNetworkNode:
    def __init__(self, node_id):
        self.node_id = node_id              # Unique identifier for the node
        self.blockchain = []                # Local blockchain for the node
        self.pending_transactions = []      # Transactions pending to be included in a block
        self.current_epoch = 0              # Current epoch number
        self.notarized_blocks = []          # List of notarized blocks
        self.votes = {}                     # Dictionary with Block --> Votes
        self.finalized_blocks = []          # List of finalized blocks
        self.biggest_finalized_block = []   # Biggest list of finalized blocks
        self.leader = False                 # Indicates if the node is the leader for the current epoch
        self.message_queue = []             # Queue to store received messages
        self.peers = []                     # List of peers connected to this node
        self.status = "active"              # Current status of the node


    def __repr__(self):
        return (f"BlockchainNetworkNode(node_id={self.node_id}, current_epoch={self.current_epoch}, "
                f"blockchain_length={len(self.blockchain)}, pending_tx={len(self.pending_transactions)}, "
                f"biggest_finalized_block={len(self.biggest_finalized_block)}, leader={self.leader}, status={self.status})")

    def process_message (self, message):
        
        """Processes incoming messages (Propose, Vote, Echo).

        Args:
            message (Message): The message received from another node.

        Returns:
        None"""
        print(f"{self.node_id} has received{message.msg_type}")
        self.message_queue.append(message) #add the msg to the queue
        if(message in self.message_queue):      #check if the message is already in the queue
            return

        if message.msg_type == "Propose":
            block = message.content
            print(f"Node {self.node_id} received a block proposal.")
            self.vote_block(block) 
            
        elif message.msg_type == "Echo":
            echoMessage = message.content
            print(f"Node {self.node_id} received an echo message.")
            
            if echoMessage.msg_type == "Propose":
                block = echoMessage.content
                print(f"Node {self.node_id} received a block proposal.")
                self.vote_block(block) 
                
            elif echoMessage.msg_type == "Vote":
                block = echoMessage.content
                print(f"Node {self.node_id} received a vote for block {block.length}.")
                self.notorize_block_votes(block)
                
            self.broadcast(Message(msg_type="Echo", content=echoMessage, sender=self.id))
            return
            
        elif message.msg_type == "Vote":
            block = message.content
            print(f"Node {self._node_id} received a vote for block {block.length}.")
            self.notorize_block_votes(block)

        else:
            print(f"Node {self.node_id} received an unknown message type: {message.msg_type}.")
            
        self.broadcast(Message(msg_type="Echo", content=message, sender=self.id))
            
            
        
    def propose_block(self):
        
        """Proposes a new block to the blockchain.

        This method is called by the leader node at the start of the current epoch. 
        It creates a new block and broadcasts it to all peers.
    
        Returns:
        None"""
        
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
    
        # Broadcast the proposed block to all peers
        self.broadcast(Message.Message(msg_type="Propose", content=proposed_block, sender=self.node_id))
        print(f"Node {self.node_id} proposed a block for epoch {self.current_epoch}")
        
        
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
        if block.length > len(self.notarized_blocks):
            self.blockchain.append(block)
            
        # Broadcast the vote to all peers
        self.broadcast(Message(msg_type="Vote", content=block, sender=self.node_id))
        print(f"Node {self.node_id} voted for block in epoch {self.current_epoch}.")
        
    
    def notorize_block_votes(self, block):
        
        """Records a vote for a given block and checks if it is notarized.
        
        Args:
            block (Block): The block for which the vote is being recorded. 
                        This block should be an instance of the Block class.

        Returns:
            None"""
            
        # if the block does not have votes yet
        if block not in self.votes:
            self.votes[block] = 0  

        self.votes[block] += 1  # Increment the vote counter for the block

        # Check if the block has more than half of the votes
        if self.votes[block] > len(self.peers) / 2:
            print(f"Node {self.node_id} notarized block {block.length}.")
        self.notarized_blocks.append(block)
        self.check_blockchain_notarization()
        
    
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
    
    def finalize(self):
        
        """Finalizes a block if three consecutive notarized blocks are observed.

        This method checks the notarized blocks for consecutive epochs and 
        finalizes the second block in the sequence.

        Returns:
            None"""
    
        if len(self.notarized_blocks) < 3:
            return  # We need at least three notarized blocks to finalize

        for i in range(len(self.notarized_blocks) - 2):
            block1 = self.notarized_blocks[i]
            block2 = self.notarized_blocks[i + 1]
            block3 = self.notarized_blocks[i + 2]

            # Check if blocks have consecutive epoch numbers
            if (block1.epoch + 1 == block2.epoch and
                block2.epoch + 1 == block3.epoch):
                # Finalize the second block
                self.finalized_blocks = block2
                print(f"Node {self.node_id} finalized block {block2.length} from epoch {block2.epoch}.")
                
            self.finalize_parents(block2)
            
        self.compare_finalized_blocks()

        return
            
    
    def finalize_parents(self, block):
        
        """Finalizes the given block and all its parent blocks.

        Args:
            block (Block): The block to be finalized along with its parent blocks.

        Returns:
            None """
        
        index_notorized = self.notarized_blocks.index(block) #save the block index
        while index_notorized >= 0:
            self.finalized_blocks.append(self.notarized_blocks[index_notorized]) # add the block
            if index_notorized == 0: 
                break
            index_notorized -= 1
        return 
    
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
        

    def update_current_leader(self):
        
        """Updates the leader status for the current epoch.
        The leader is determined based on the node's ID and the current epoch.
    
        Returns:
        None"""
    
        # Our way to update de lider system 
        leaderId = random.randint(1, len(self.peers))
        if self.node_id == leaderId:
            self.leader = True
            print(f"Node {self.node_id} is now the leader for epoch {self.current_epoch}.")
        else:
            print(f"Node {leaderId} is now the leader for epoch {self.current_epoch}.")
            self.leader = False
        return leaderId
        
        
    def broadcast(self, message):
        
        """Broadcasts/Echoing a message to all connected peers.

        Args:
            message (Message): The message to be sent to peers.

        Returns:
        None"""
    
        for peer in self.peers:
            peer.process_message(message)
            print(f"Node {self.node_id} broadcasted message to Node {peer.node_id}.")
            
    def print_finalized_blocks(self):
        
        """Prints the current list of finalized blocks."""
        
        print(f"Finalized blocks for Node {self.node_id}:")
        for block in self.finalized_blocks:
            print(f" - Block {block.length} from epoch {block.epoch}")
            
    
    def advance_epoch(self):

        """Advances to the next epoch and elects a new leader."""

        self.current_epoch += 1
        print(f"Node {self.node_id} will advance to epoch {self.current_epoch}.")
        self.update_current_leader()  


    def simulate_failure(self):
        """Randomly simulates a failure of the node."""
        if random.random() < 0.1:  # 10% to fail
            self.status = "failed"
            print(f"Node {self.node_id} has crashed!")

    def recover(self):
        """Recovers the node from a failure."""
        if self.status == "failed":
            self.status = "active"
            self.blockchain = self.load_last_blockchain()  # Método que você deve implementar para carregar a blockchain
            print(f"Node {self.node_id} has recovered and is now active.")
    
    def generate_random_transaction(self):

        """Generates and adds a random transaction."""

        # Simulação simples de transação
        transaction = Transaction.Transaction(sender=self.node_id, receiver=random.randint(1, 3), transaction_id=random.randint(1000, 9999), amount=random.uniform(1.0, 100.0))
        self.add_transaction(transaction)

    
            
    # Getter for node_id
    def get_node_id(self):
        return self.node_id 

    # Setter for node_id
    def set_node_id(self, node_id):
        self.node_id = node_id  

    # Getter for blockchain
    def get_blockchain(self):
        return self.blockchain  

    # Setter for blockchain
    def set_blockchain(self, blockchain):
        self.blockchain = blockchain  

    # Getter for pending_transactions
    def get_pending_transactions(self):
        return self.pending_transactions  

    # Setter for pending_transactions
    def set_pending_transactions(self, transactions):
        self.pending_transactions = transactions  

    # Getter for current_epoch
    def get_current_epoch(self):
        return self.current_epoch  

    # Setter for current_epoch
    def set_current_epoch(self, epoch):
        self.current_epoch = epoch  

    # Getter for notarized_blocks
    def get_notarized_blocks(self):
        return self.notarized_blocks  

    # Setter for notarized_blocks
    def set_notarized_blocks(self, blocks):
        self.notarized_blocks = blocks  

    # Getter for votes
    def get_votes(self):
        return self.votes  

    # Setter for votes
    def set_votes(self, votes):
        self.votes = votes  

    # Getter for finalized_blocks
    def get_finalized_blocks(self):
        return self.finalized_blocks  

    # Setter for finalized_blocks
    def set_finalized_blocks(self, blocks):
        self.finalized_blocks = blocks  

    # Getter for leader
    def is_leader(self):
        return self.leader  

    # Setter for leader
    def set_leader(self, leader_status):
        self.leader = leader_status 

    # Getter for message_queue
    def get_message_queue(self):
        return self.message_queue  

    # Setter for message_queue
    def set_message_queue(self, messages):
        self.message_queue = messages  

    # Getter for peers
    def get_peers(self):
        return self.peers 

    # Setter for peers
    def set_peers(self, peers):
        self.peers = peers 

    # Getter for status
    def get_status(self):
        return self.status  

    # Setter for status
    def set_status(self, status):
        self.status = status 
