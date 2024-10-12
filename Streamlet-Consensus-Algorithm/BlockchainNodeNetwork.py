

class BlockchainNetworkNode:
    def __init__(self, node_id):
        self.node_id = node_id  # Unique identifier for the node
        self.blockchain = []     # Local blockchain for the node
        self.pending_transactions = []  # Transactions pending to be included in a block
        self.current_epoch = 0   # Current epoch number
        self.notarized_blocks = []  # List of notarized blocks
        self.votes = {}          # Dictionary with Block --> Votes
        self.leader = False      # Indicates if the node is the leader for the current epoch
        self.message_queue = []          # Queue to store received messages
        self.peers = []          # List of peers connected to this node
        self.status = "active"   # Current status of the node


    def __repr__(self):
        return (f"BlockchainNetworkNode(node_id={self.node_id}, current_epoch={self.current_epoch}, "
                f"blockchain_length={len(self.blockchain)}, status={self.status})")
        
    def process_message (self, message):
        
        """Processes incoming messages (Propose, Vote, Echo).

        Args:
            message (Message): The message received from another node.

        Returns:
        None"""
        
        if message.msg_type == "Propose":
            block = message.content
            print(f"Node {self._node_id} received a block proposal.")
            self.vote_block(block) 
            
        elif message.msg_type == "Echo":
            block = message.content
            print(f"Node {self._node_id} received an echo message.")
            self.notorize_vote(block)

        elif message.msg_type == "Vote":
            block = message.content
            print(f"Node {self._node_id} received a vote for block {block.length}.")

        else:
            print(f"Node {self._node_id} received an unknown message type: {message.msg_type}.")
            
            
        
    def propose_block(self):
        
        """Proposes a new block to the blockchain.

        This method is called by the leader node at the start of the current epoch. 
        It creates a new block and broadcasts it to all peers.
    
        Returns:
        None"""
        
        if not self._leader: # Not the leader of this epoch( Only the leader can propose a block)
            print(f"Node {self._node_id} is not the leader for epoch {self._current_epoch}")
            return  
    
        # Create a new block containing the pending transactions
        proposed_block = Block(
            # retunrs the hash of the last block ,if the list is empty , returns 0
            previous_hash=self._blockchain[-1].calculate_hash() if self._blockchain else "0",  # Hash of the last block
            epoch=self._current_epoch,
            length=len(self._blockchain) + 1,
            transactions=self._pending_transactions
            )
    
        # Broadcast the proposed block to all peers
        self.broadcast(Message(msg_type="Propose", content=proposed_block, sender=self._node_id))
        print(f"Node {self._node_id} proposed a block for epoch {self._current_epoch}")
        
        
    def vote_block(self, block):
        
        """Votes for a proposed block if it extends the longest notarized chain.

        Args:
            block (Block): The proposed block to vote for.

        Returns:
        None """
        
        # Check if the block is valid for voting
        if len(block.transactions) == 0:
            print(f"Node {self._node_id} cannot vote for an empty block.")
            return  

        # We only add a block if it is longer than the blockchain
        if block.length > len(self._blockchain):
            self._blockchain.append(block)
            
        # Broadcast the vote to all peers
        self.broadcast(Message(msg_type="Vote", content=block, sender=self._node_id))
        print(f"Node {self._node_id} voted for block in epoch {self._current_epoch}.")
        
    
    def notorize_vote(self, block):
        
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
    
    def add_transaction(self, transaction):
        
        """ Adds a transaction to the pending transactions list.

        Args:
            transaction (Transaction): The transaction to be added.

        Returns:
            None """
        
    if isinstance(transaction, Transaction):
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
    if self.node_id == self.current_epoch % len(self.peers):
        self.leader = True
        print(f"Node {self.node_id} is now the leader for epoch {self.current_epoch}.")
    else:
        self.leader = False
        
        
    def broadcast(self, message):
        
        """Broadcasts/Echoing a message to all connected peers.

        Args:
            message (Message): The message to be sent to peers.

        Returns:
        None"""
    
        for peer in self._peers:
            peer.process_message(message)
            print(f"Node {self._node_id} broadcasted message to Node {peer._node_id}.")
    
    
    # Getter for the unique identifier of the node
    @property
    def node_id(self):
        return self._node_id

    # Setter for the unique identifier of the node
    @node_id.setter
    def node_id(self, value):
        self._node_id = value

    # Getter for the local blockchain
    @property
    def blockchain(self):
        return self._blockchain

    # Setter for the local blockchain
    @blockchain.setter
    def blockchain(self, value):
        self._blockchain = value

    # Getter for the pending transactions
    @property
    def pending_transactions(self):
        return self._pending_transactions

    # Setter for the pending transactions
    @pending_transactions.setter
    def pending_transactions(self, value):
        self._pending_transactions = value

    # Getter for the current epoch number
    @property
    def current_epoch(self):
        return self._current_epoch

    # Setter for the current epoch number
    @current_epoch.setter
    def current_epoch(self, value):
        self._current_epoch = value

    # Getter for the notarized blocks
    @property
    def notarized_blocks(self):
        return self._notarized_blocks

    # Setter for the notarized blocks
    @notarized_blocks.setter
    def notarized_blocks(self, value):
        self._notarized_blocks = value

    # Getter for the votes received
    @property
    def votes(self):
        return self._votes

    # Setter for the votes received
    @votes.setter
    def votes(self, value):
        self._votes = value

    # Getter for the leader status
    @property
    def leader(self):
        return self._leader
    
    # Getter for the queue
    @property
    def queue(self):
        return self._queue

    # Setter for the queue
    @queue.setter
    def queue(self, value):
        self._queue = value

    # Getter for the list of peers
    @property
    def peers(self):
        return self._peers

    # Setter for the list of peers
    @peers.setter
    def peers(self, value):
        self._peers = value

    # Getter for the node's status
    @property
    def status(self):
        return self._status

    # Setter for the node's status
    @status.setter
    def status(self, value):
        self._status = value
    







