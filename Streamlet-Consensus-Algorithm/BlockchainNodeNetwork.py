
class BlockchainNetworkNode:
    def __init__(self, node_id):
        self.node_id = node_id  # Unique identifier for the node
        self.blockchain = []     # Local blockchain for the node
        self.pending_transactions = []  # Transactions pending to be included in a block
        self.current_epoch = 0   # Current epoch number
        self.notarized_blocks = []  # List of notarized blocks
        self.votes = {}          # Votes received for blocks
        self.leader = False      # Indicates if the node is the leader for the current epoch
        self.queue = []          # Queue to store received messages
        self.peers = []          # List of peers connected to this node
        self.status = "active"   # Current status of the node


    def __repr__(self):
        return (f"BlockchainNetworkNode(node_id={self.node_id}, current_epoch={self.current_epoch}, "
                f"blockchain_length={len(self.blockchain)}, status={self.status})")

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

    # Setter for the leader status
    @leader.setter
    def leader(self, value):
        self._leader = value

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
    







