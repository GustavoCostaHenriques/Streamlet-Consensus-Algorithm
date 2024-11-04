class Message:
    def __init__(self, msg_type, content, sender,longestChain):
        self.msg_type = msg_type  # (Propose, Vote, Echo)
        self.content = content      
        self.sender = sender
        self.longestChain=longestChain
    
    # Returns an informative representation of the Message object.
    def __repr__(self):
        return (f"Message(type={self.msg_type}, sender={self.sender}, "
                f"content={self.content})")
    
    @property
    def msg_type(self):
        return self._msg_type

    # Setter to msg_type
    @msg_type.setter
    def msg_type(self, value):
        self._msg_type = value

    # Getter to content
    @property
    def content(self):
        return self._content

    # Setter to content
    @content.setter
    def content(self, value):
        self._content = value

    # Getter to sender
    @property
    def sender(self):
        return self._sender

    # Setter to sender
    @sender.setter
    def sender(self, value):
        self._sender = value

    def to_dict(self):
        """Converts the Message object to a dictionary for JSON serialization."""
        return {
            'msg_type': self.msg_type,
            'content': self.content.to_dict,
            'sender': self.sender
        }