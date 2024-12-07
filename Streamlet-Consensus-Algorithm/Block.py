import hashlib
import Transaction
class Block:
    def __init__(self, previous_hash, hash, epoch, length, transactions):
        self.previous_hash = previous_hash
        self.hash = hash  
        self.epoch = epoch                   
        self.length = length                 
        self.transactions = transactions    

    # Method that calculates the hash of the current block.
    def calculate_hash(self):
        # Creates a string with the content of the block
        block_string = f"{self.previous_hash}{self.epoch}{self.length}{self.transactions}"
        # Calculates the hash of that string
        return hashlib.sha1(block_string.encode()).hexdigest()

    # Returns an informative representation of the Block object.
    def __repr__(self):
        return (f"Block(epoch={self.epoch}, length={self.length}, transactions={self.transactions})")
    
    # Getter for the previous block's hash
    @property
    def previous_hash(self):
        return self._previous_hash

    # Setter for the previous block's hash
    @previous_hash.setter
    def previous_hash(self, value):
        self._previous_hash = value
        
    # Getter for the block's hash
    @property
    def hash(self):
        return self._hash

    # Setter for the block's hash
    @hash.setter
    def hash(self, value):
        self._hash = value

    # Getter for the epoch number
    @property
    def epoch(self):
        return self._epoch

    # Setter for the epoch number
    @epoch.setter
    def epoch(self, value):
        self._epoch = value

    # Getter for the block's number
    @property
    def length(self):
        return self._length

    # Setter for the block's number
    @length.setter
    def length(self, value):
        self._length = value

    # Getter for the list of transactions
    @property
    def transactions(self):
        return self._transactions
    
    # Setter for the block's number
    @transactions.setter
    def transactions(self, value):
        self._transactions = value

    def to_dict(self):
        return{
            'previous_hash' : self.previous_hash ,  
            'epoch' :self.epoch,                   
            'length' : self.length,                 
            'transactions': [tx.to_dict() for tx in self.transactions],     
        }
    @classmethod
    def from_dict(cls, data):
        transactions = [Transaction.Transaction(**tx) for tx in data['transactions']]
        return cls(data['previous_hash'], data['epoch'], data['length'], transactions)