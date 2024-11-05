import BlockchainNetworkNode
import random
import time

def main():
    
    NumberOfNodes = int(input("Enter the number of nodes: "))
    NumberOfEpoch = int(input("Enter the number of epochs: "))
    Delta = int(input("Enter the number of seconds per epoch: "))
    # Inicializa os nós da rede
    nodes = []
    for i in range(NumberOfNodes):
        node = BlockchainNetworkNode.BlockchainNetworkNode(i,"127.0.0.1" , 5000 + i)
        nodes.append(node)
        print("Criou e adicionou o node ", i)
   
    for node in nodes:
        for i in range(int(NumberOfNodes)):
            port = node.port
            if(port != 5000 + i):
                node.add_node(("127.0.0.1" , int(5000 + i)))
                print("Conectou o node ", port - 5000, " ao node ", i)
                
    for i in range(NumberOfEpoch):
        leader = generateRandomLeader(NumberOfNodes - 1)
        print(f"The leader for epoch {i} is node {leader}.")
        nodeL = nodes[leader]
        nodeL.menu("l")
        print("Epoch", i , "vai começar")
        start = time.time()
        nodeL.menu("s")
        while(time.time() - start < Delta):
            continue
        print(nodeL.notarized_blocks)
        nodeL.menu("e")
            
def generateRandomLeader(NumberOfNodes):
    leader_index = random.randint(0,NumberOfNodes)
    return leader_index

if __name__ == "__main__":
    main()