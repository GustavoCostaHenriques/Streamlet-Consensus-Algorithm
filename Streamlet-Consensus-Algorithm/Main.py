import BlockchainNetworkNode

def run_network(BlockchainNetworkNode):

    #Runs the network for a given number of rounds.
        
        # Gere uma transação aleatória
        BlockchainNetworkNode.generate_random_transaction()
        # Apenas o líder propõe um bloco
        if (BlockchainNetworkNode.is_leader()):
            BlockchainNetworkNode.propose_block()
        
        # Verifica se o nó pode finalizar um bloco
        BlockchainNetworkNode.finalize()  
        print(BlockchainNetworkNode)  

        # Avança para o próximo epoch
        BlockchainNetworkNode.advance_epoch()  
        
        # Exibe o estado do nó após cada rodada
        print()  # Linha em branco para separaçãoc

def main():
    # Inicializa os nós da rede
    node1 = BlockchainNetworkNode.BlockchainNetworkNode(node_id=1)
    node2 = BlockchainNetworkNode.BlockchainNetworkNode(node_id=2)
    node3 = BlockchainNetworkNode.BlockchainNetworkNode(node_id=3)

    # Conecta os nós entre si
    node1.peers = [node2, node3]
    node2.peers = [node1, node3]
    node3.peers = [node1, node2]

    # Define o líder para o primeiro epoch
    rounds_number=5
    leaderId = node1.update_current_leader()
    for round in range(rounds_number):
        print(f"round{round}")
        for node in [node1, node2, node3]:
            if(leaderId == node.get_node_id()):
                node.set_leader(True)
                run_network(node)


    """ # Executa a rede por um número de rodadas
    total_rounds = 5  # Você pode ajustar o número de rodadas conforme necessário
    for node in [node1, node2, node3]:
        run_network(node, rounds=total_rounds) """

if __name__ == "__main__":
    main()