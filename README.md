# Backend

This is a POC that I developed to exercise a REST API that returns discounts and prices for a shopping cart.

The discount code is disabled since the original project was canceled.

# How to run
Configure environment variable **LISTEN_PORT**. 

~~It is also possible to define **DISCOUNT_CACHE** with the time in seconds for the cache, 0 to disable~~

CMD on Windows:

```
> set LISTEN_PORT=8081
> .\main.py
```
Linux:
```
$ GRPC_IP_PORT=192.168.0.12:50051 LISTEN_PORT=8081 ./main.py
```
