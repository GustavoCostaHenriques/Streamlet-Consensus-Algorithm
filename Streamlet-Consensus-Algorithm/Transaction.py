class Transaction:
    def __init__(self, sender, receiver, transaction_id, amount):
        # Define os atributos privados diretamente
        self._sender = sender           
        self._receiver = receiver          
        self._transaction_id = transaction_id                
        self._amount = amount              
    
    # Returns an informative representation of the Transaction object.
    def __repr__(self):
        return (f"Transaction(sender={self.sender}, receiver={self.receiver}, "
                f"transaction_id={self.transaction_id}, amount={self.amount})")
    
    # Returns if the amount is valid    
    def is_valid(self):
        return self.amount > 0

    # Getter for the transaction sender
    @property
    def sender(self):
        return self._sender

    # Setter for the transaction sender
    @sender.setter
    def sender(self, value):
        self._sender = value

    # Getter for the transaction receiver
    @property
    def receiver(self):
        return self._receiver

    # Setter for the transaction receiver
    @receiver.setter
    def receiver(self, value):
        self._receiver = value

    # Getter for the transaction ID
    @property
    def transaction_id(self):
        return self._transaction_id

    # Setter for the transaction ID
    @transaction_id.setter
    def transaction_id(self, value):
        self._transaction_id = value

    # Getter for the transaction amount
    @property
    def amount(self):
        return self._amount

    # Setter for the transaction amount
    @amount.setter
    def amount(self, value):
        self._amount = value
