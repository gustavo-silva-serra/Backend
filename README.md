# Backend

Olá!

Obrigado pela sua visita. Este é um projeto interessante para considerar diferentes aspectos de escalabilidade. Em alguns pontos também é possível optar por maior controle sobre os dados recebidos e enviados em detrimento de performance ou simplicidade do código.

Para acessar o projeto em Docker, [acessar aqui](https://hub.docker.com/r/gustavosilvaserra/backend-test)

Disponibilizei o arquivo docker-compose.yml aqui no github.

Considerando o escopo do projeto, todo o desenvolvimento foi realizado no arquivo main.py.

Para executar o projeto basta configurar as variáveis de ambiente **LISTEN_PORT** (porta em que o serviço receberá as conexões) e **GRPC_IP_PORT** (IP:porta do serviço de descontos). Também é possível definir **DISCOUNT_CACHE** com o valor em segundos para o tempo para a cache de descontos, utilizando 0 (zero) para desabilitar.

Segue o exemplo abaixo:

CMD no Windows:

```
> set GRPC_IP_PORT=192.168.0.12:50051
> set LISTEN_PORT=8081
> .\main.py
```
Linux:
```
$ GRPC_IP_PORT=192.168.0.12:50051 LISTEN_PORT=8081 ./main.py
```

Também é possível executar os testes unitários, exportando apenas a variável GRPC_IP_PORT e executando test_main.py
