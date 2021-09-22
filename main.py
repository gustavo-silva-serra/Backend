#!/usr/bin/python3
#TODO: deixar registro das consultas e dos erros?
#TODO: fazer a cache com tempo configurável e com tamanho limite
#TODO: tentar reconectar de quanto em quanto tempo caso o serviço tenha ficado offline?
#TODO: thread para atender clientes?
#TODO: o que posso fazer em termos de validacao de input?
#TODO: posso trocar facilmente o metodo de consulta do meu servico para banco de dados, por ex? strategy pattern
#TODO: timeout para processar a consulta, como implementar?
#TODO: sinalizar no JSON de resposta erros de acesso?
#TODO: tem como processar em lote?
#TODO: adicionar o brinde com regras variaveis (strategy)
#TODO: criar class abstrata para buscar produtos
#TODO: encapsular produtos do banco em um objeto
#OTOD: parametros do meu servico: porta http, tempo para cache, tamanho da fila
#TODO: atender depois o REST
#TODO: tratar exceoes de maneira mais graciosa
#TOOD: salvar descontos em relatorios?
#TODO: calcular totais com base nos produtos

#TODO: posso trocar facilmente autenticação/protocolo da minha interface HTTP?
#TODO: posso trocar o insecure_channel?
import discount_pb2_grpc
import discount_pb2
import grpc
import json
import cherrypy

class ProductDatabase:
    def __init__(self):
        products_db = json.loads(open('products.json').read())
        self.products_map = {product['id']:product for product in products_db}
    
    def get_product_price(self,product_id):
        return int(self.products_map[product_id]['amount'])

class DiscountEngine:
    def get_product_discount(self,product_id):
        channel = grpc.insecure_channel('192.168.0.12:50051')
        stub = discount_pb2_grpc.DiscountStub(channel)
        return float(stub.GetDiscount(discount_pb2.GetDiscountRequest(productID = product_id)).percentage)

class ShopCart:
    
    def process(self, input_json):
        total_amount = 0
        total_discount = 0
        
        input_json = json.loads(input_json)
        products = []
        
        for product in input_json['products']:
            amount = ProductDatabase().get_product_price(product['id'])
            total_amount += amount * int(product['quantity'])
            discount_percentage = DiscountEngine().get_product_discount(product['id'])
            discount = discount_percentage * amount
            total_discount += discount
            products.append(self.create_default_product_response(product['id'], int(product['quantity']), amount, discount))
            
            
        return self.create_default_response(int(total_amount),int(total_discount),products) 
    
    def create_default_response(self, total_amount, total_discount, products):
        response = {"total_amount": total_amount, "total_amount_with_discount": total_amount - total_discount, "total_discount": total_discount, "products": products}
        return json.dumps(response,indent=3)

    def create_default_product_response(self, id, qnt, unit, discount, gift = False):
        return {"id": int(id), "quantity": qnt, "unit_amount": unit, "total_amount": qnt*unit, "discount": discount, "is_gift": gift}
        

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

