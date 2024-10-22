import BlockchainNetworkNode

def main():
    # Inicializa os nós da rede
    node1 = BlockchainNetworkNode(node_id=1)
    node2 = BlockchainNetworkNode(node_id=2)
    node3 = BlockchainNetworkNode(node_id=3)

    # Conecta os nós entre si
    node1.peers = [node2, node3]
    node2.peers = [node1, node3]
    node3.peers = [node1, node2]

    # Define o líder para o primeiro epoch
    node1.update_current_leader()

    # Executa a rede por um número de rodadas
    total_rounds = 5  # Você pode ajustar o número de rodadas conforme necessário
    for node in [node1, node2, node3]:
        node.run_network(rounds=total_rounds)

if __name__ == "__main__":
    main()


def run_network(BlockchainNetworkNode, rounds=5):

    #Runs the network for a given number of rounds.
    
    for round_number in range(rounds):
        print(f"--- Round {round_number + 1} ---")
        
        # Gere uma transação aleatória
        BlockchainNetworkNode.generate_random_transaction() 
        
        # Apenas o líder propõe um bloco
        if BlockchainNetworkNode.leader:
            BlockchainNetworkNode.propose_block()
        
        # Processa mensagens na fila
        while BlockchainNetworkNode.message_queue:
            message = BlockchainNetworkNode.message_queue.pop(0)  # Retira a mensagem da fila
            BlockchainNetworkNode.process_message(message)
        
        # Verifica se o nó pode finalizar um bloco
        BlockchainNetworkNode.finalize()  
        
        # Avança para o próximo epoch
        BlockchainNetworkNode.advance_epoch()  
        
        # Simula uma possível falha
        BlockchainNetworkNode.simulate_failure()  
        
        # Exibe o estado do nó após cada rodada
        print(BlockchainNetworkNode)  
        print()  # Linha em branco para separação