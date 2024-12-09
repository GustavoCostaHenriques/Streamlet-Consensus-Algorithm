Configurar os ficheiros da maneira que quiser. Por exemplo:
info:
5
15
3
e sockets:
0:127.0.0.1,5000
1:127.0.0.1,5001
2:127.0.0.1,5002
3:127.0.0.1,5003
4:127.0.0.1,5004

Depois abrir 5 terminais e escrever em cada um:
 "python .\BlockchainNetworkNode.py x 500x 13:00 a b" onde o x é o node id a é o confusion_start e o b confusion_duration (IMPORTANTE TEM TODOS DE TER A MESMA HORA DE COMEÇO)
 o programa irá correr da maneira desejada.
 Para causar uma crash failure apenas feche um dos terminais. Depois volte a abrir e meta o seguinte comando.
 "python .\BlockchainNetworkNode.py x 500x " onde o x é o node id (este não necessita da hora de começo nem vai conseguir ter confusion)

 No final da execução iram ser impressas diferentes informações com seguinte ordem: 1ºblockchain geral, 2º blocos notorizados, 3ºblocos finalizados