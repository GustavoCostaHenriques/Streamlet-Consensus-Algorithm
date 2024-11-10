Para correr 5 replicas (5 instancias do BlockchainNetworkNode) tem de se fazer os seguintes passos:
-  Abrir um terminal e entrar na pasta em que esta o projeto.
-  Correr o seguinte comando python Main.py que irá abrir a main. Este comando vai executar a main que vai perguntar ao utilizador informações para correr o projeto
-  Introduzir o numeros de nodes (neste caso serão 5), numero de epocas e o valor do delta. Depois de passar estas informações este main irá abrir n (neste caso 5) terminais cada um sendo um node.
- Introduzir o numero de transações que o bloco proposto pelo lider irá ter. Ao colocar este valor o programa vai executar uma epoca.
- Ou avançar para a proxima epoca (colocar -1) ou ver algum valor de um respetivo nó(colocar o id do nó).
- Quando iniciar nova epoca colocar o numero de transações e o programa irá executar de maneira igual. 
- O programa vai continuar a executar assim até a epoca final. Na epoca final ao colocarmos -1 para avançarmos para a proxima epoca ele ira encerrar.

Limitações:
- O programa tem uma limitação de cerca de 1000 nós.
