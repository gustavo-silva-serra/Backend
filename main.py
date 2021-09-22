#!/usr/bin/python3
#TODO: deixar registro das consultas e dos erros?
#TODO: tentar reconectar de quanto em quanto tempo caso o serviço tenha ficado offline?
#TODO: o que posso fazer em termos de validacao de input?
#TODO: posso trocar facilmente o metodo de consulta do meu servico para banco de dados, por ex? strategy pattern
#TODO: timeout para processar a consulta, como implementar?
#TODO: sinalizar no JSON de resposta erros de acesso?
#TODO: tem como processar em lote?
#TODO: adicionar o brinde com regras variaveis (strategy)
#TODO: criar class abstrata para buscar produtos
#OTOD: parametros do meu servico: porta http, tempo para cache, tamanho da fila
#TODO: atender depois o REST
#TODO: tratar exceoes de maneira mais graciosa
#TOOD: salvar descontos em relatorios?

#TODO: posso trocar facilmente autenticação/protocolo da minha interface HTTP?
#TODO: posso trocar o insecure_channel?
import discount_pb2_grpc
import discount_pb2
import grpc
import json
import cherrypy
import time

class ProductDatabase:
    def __init__(self):
        products_db = json.loads(open('products.json').read())
        self.products_map = {product['id']:product for product in products_db}
    
    def get_price(self,product_id):
        return int(self.products_map[product_id]['amount'])

class DiscountEngine:
    cache_timeout = 0
    cached = {}    
    
    def __init__(self, cache_t):
        self.cache_timeout = cache_t 

    def get_discount(self,product_id):
        # Se existe uma cache, procura primeiro nela
        if self.cache_timeout > 0:
            if product_id in self.cached.keys():
                if time.time() - self.cached[product_id][0] < self.cache_timeout:
                    return self.cached[product_id][1]
        
        # Nao existe cache ou expirou    
        channel = grpc.insecure_channel('192.168.0.12:50051')
        stub = discount_pb2_grpc.DiscountStub(channel)
        perc = float(stub.GetDiscount(discount_pb2.GetDiscountRequest(productID = product_id)).percentage)
        
        # Atualiza o desconto na cache
        if self.cache_timeout > 0:
            if len(self.cached) > 10000: # Limite facilmente parametrizavel
                self.cached = {}
            self.cached[product_id] = (time.time(), perc)
            
        return perc

class Product:
    def __init__(self, prod_id, quantity, amount, discount_percentage):
        self.id = int(prod_id)
        self.quantity = int(quantity)
        self.unit_amount = int(amount)
        self.total_amount = self.quantity * self.unit_amount
        self.discount = int(float(discount_percentage) * self.total_amount)
        self.is_gift = False

class Cart:
    def __init__(self):
        self.total_amount = 0
        self.total_discount = 0
        self.total_amount_with_discount = 0
        self.products = []
    
    def add_product(self, product):
        self.total_amount += product.total_amount
        self.total_discount += product.discount
        self.total_amount_with_discount = self.total_amount - self.total_discount
        self.products.append(product)

class ShopCart:
    
    def process(self, input_json):
        input_json = json.loads(input_json)
        cart = Cart()
        
        for product in input_json['products']:
            prod_id,prod_qnt = product['id'],product['quantity']
            amount = ProductDatabase().get_price(prod_id)
            discount_percentage = DiscountEngine(5).get_discount(prod_id)
            cart.add_product(Product(prod_id, prod_qnt, amount, discount_percentage))
            
        return json.dumps(cart, default=lambda o: o.__dict__)

class ShopCartServer(object):

    @cherrypy.expose
    def index(self):
        # CherryPy não aceita que se receba um body de forma convencional para um GET. Como eu não sabia se implementar
        # o serviço no GET era um requisito, tive que contornar o problema fazendo leitura de linha a linha do body
        body = b''
        line = cherrypy.request.body.readline()
        while line:
            body = body + line
            line = cherrypy.request.body.readline()
        cart = ShopCart()
        return cart.process(body.decode("utf-8"))
    

if __name__ == "__main__":
    cherrypy.config.update({'server.socket_host':"0.0.0.0", 'server.socket_port':8181})
    cherrypy.quickstart(ShopCartServer(), '/')

