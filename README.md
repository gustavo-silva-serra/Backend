# Backend

Olá!

Todo o projeto está desenvolvido no arquivo main.py.

Para executar o projeto basta configurar as variáveis de ambiente LISTEN_PORT (porta em que o serviço receberá as conexões) e GRPC_IP_PORT (IP:porta do serviço de descontos), conforme o exemplo abaixo:

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
