Este projeto tem dois ficheiros de setup:
-info: ficheiro de configuração sendo a primeira linha numero de nós, segunda numero de epocas e a terceira o delta. Ou seja se
tivermos um ficheiro assim:
3
15
3
os nós vão executar 15 epocas, epocas de 6 segundos e iram executar para 3 nós.
-Sockets: Ficheiro com os id:ip,port de cada nó. Ou seja com o exemplo anterior teriamos de ter 3 linhas diferentes deste ficheiro.

O programa tem algumas restrições no que conta a estes ficheiros. Estes ficheiros tem de ser bem configurados antes de uma execução, os nós tem de
ter uma ordem ascendente e tem de começar no 0. Um tempo de epoca que recomendamos é 2 e 3. Não temos a certeza se o programa irá funcionar em diferentes computadores,
mas em principio sim desde que no ficheiro sockets se meta o ip,port desse computador. Um nó que crasha não consegue ter confusão. Devido a algumas mudanças o echo ficou instavel dando varios erros no programa as vezes. Nos decidimos comentar para não afetar o programa, mas o professor consegue ver onde fariamos os echos.