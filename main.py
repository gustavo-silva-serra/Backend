#!/usr/bin/python3
#TODO: tentar reconectar de quanto em quanto tempo caso o serviço tenha ficado offline?
#TODO: o que posso fazer em termos de validacao de input?
#TODO: sinalizar no JSON de resposta erros de acesso?
#OTOD: parametros do meu servico: porta http, tempo para cache, tamanho da fila
#TODO: banco está sempre inicializando
#TODO: posso trocar facilmente autenticação/protocolo da minha interface HTTP?
#TODO: posso trocar o insecure_channel?

# -----------------------------------------------------------------------------
# Possíveis pontos de melhoria e customização:
#
#1) Timeout configurável para buscar descontos via gRPC
#2) Sinalizar no JSON de resposta erros de acesso para que o chamador decida o
# o que deve ser feito


import discount_pb2_grpc
import discount_pb2
import grpc
import json
import cherrypy
import time
import abc

class ProductDatabase:
    """ Atua como proxy no acesso ao banco de mercadorias.

        Conforme a evolução do banco em termos de quantidade de produtos  dispo-
        níveis, pode ser  que seja necessário um  mecanismo mais sofisticado que 
        não carregue todas  em memória. Outro ponto a se  considerar é a  possi-
        bilidade de mercadorias terem seus preços atualizados ao longo do dia.
    """
    products_map = {}
    
    def __init__(self):
        """ Carrega em memória as mercadorias disponíveis """
        if not self.products_map:
            products_db = json.loads(open('products.json').read())
            self.products_map = {product['id']:product for product in products_db}
    
    def get_price_gift(self,product_id):
        """Retorna o preço e a flag is_gift para um determinado id"""
        return int(self.products_map[product_id]['amount']),bool(self.products_map[product_id]['is_gift'])

class EventNotifier(abc.ABC):
    """ Classe abstrata para tratar notificação de eventos .
    
        Essa classe permite  que se registre um  listener para eventos em pontos
        específicos da execução.Cada listener é livre para tomar quaisquer ações 
        para o evento recebido. Útil para implementar handlers que possam gravar
        eventos em um banco de dados para relatórios.
    """
    @abc.abstractmethod
    def notify_event(self,event):
        """ Método que deve implementar o tratamento ao receber o evento """
        pass

class PrintToScreenNotifier(EventNotifier):
    """ Esse handler joga na tela o evento recebido """
    def notify_event(self,event):
        print(event)

class SaveToFileNotifier(EventNotifier):
    """ Esse handler joga o evento em um arquivo de log """
    def notify_event(self,event):
        with open('application_log.txt', 'a') as f:
            f.write(str(event))

class EventNotifierManager:
    """ Implementa um versão rudimentar de observer para eventos do sistema.
    
        Possui uma lista de handlers de eventos associados a um tipo de evento
    """
    listeners = {}
    
    def add_event_listener(self, event_type, listener):
        """ Adiciona um handler associado a um tipo de evento """
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)
    
    def notify_event(self,event_type, event):
        """ Notifica o evento a quem estiver cadastrado ao tipo respectivo """
        if event_type in self.listeners:
            for l in self.listeners[event_type]:
                l.notify_event(event)

class DiscountEngine:
    """ Serve de proxy para acessar o webservice de descontos em produtos.
    
        Além de atuar como proxy a classe provê um mecanismo simples de cache de 
        descontos  para evitar  acesso constante ao serviço.  No futuro pode ser
        evoluído para mecanismos mais sofisticados de cache.
    """
    
    cache_timeout = 0
    cached = {}    
    
    def __init__(self, cache_t):
        """ Inicializa a cache com cache_t segundos """
        self.cache_timeout = cache_t 

    def get_discount(self,product_id):
        """ Retorna o desconto associado a um produto """
        
        # Se existe uma cache, procura primeiro nela
        if self.cache_timeout > 0:
            if product_id in self.cached.keys():
                if time.time() - self.cached[product_id][0] < self.cache_timeout:
                    return self.cached[product_id][1]
        
        # Nao existe desconto em cache ou expirou 
        try:
            channel = grpc.insecure_channel('192.168.0.12:50050')
            stub = discount_pb2_grpc.DiscountStub(channel)
            perc = float(stub.GetDiscount(discount_pb2.GetDiscountRequest(productID = product_id), timeout=2).percentage)
        except Exception as e:
            EventNotifierManager().notify_event("error", e)
            return 0
        
        # Atualiza o desconto na cache. Apesar de não ser um mecanismo sofisticado,
        # é simples de entender e manter e não compromete o tempo de execução como 
        # uma lista circular. Um meio termo seria o acesso com mutex (read ou 
        # write lock) com uma thread de análise a cada X segundos
        if self.cache_timeout > 0:
            if len(self.cached) > 10000: # Limite facilmente parametrizavel
                self.cached = {}
            self.cached[product_id] = (time.time(), perc)
            
        return perc

class Product:
    """ Representa um produto a ser retornado para o chamador do serviço """
    def __init__(self, prod_id, quantity, amount, discount_percentage):
        self.id = int(prod_id)
        self.quantity = int(quantity)
        self.unit_amount = int(amount)
        self.total_amount = self.quantity * self.unit_amount
        self.discount = int(float(discount_percentage) * self.total_amount)
        self.is_gift = False

class Cart:
    """ Representa os totais de compra a serem retornados para o chamador """
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

class DefaultBlackFridayEngine:
    """ Implementa um critério de seleção para qual produto deve ser dado de brinde
    
        Seria possível trocar  por outros mecanismos com base  na preferência da
        loja: produto mais barato, produto menos vendido, etc.
    """
    def apply(self, products):
        """ Escolhe o produto mais barato, independente da quantidade """
        if len(products) <= 0:
            return None
        return sorted(products, key=lambda x: x.total_amount)[0]

class ShopCart:
    """ Implementa a lógica que atende o serviço.
    
        Classe  principal, varre os produtos do carrinho retornando preço e des-
        contos. Também invoca o método seletor para black friday.
    """
        
    def __init__(self):
        self.black_friday_engine = DefaultBlackFridayEngine() # Facilita manutenção futura, caso mude a politica
        self.black_friday_products = [] # Evita de colocar informação de is_gift direto no produto, pode levar a erros
        
    def process(self, input_json):
        try:
            input_json = json.loads(input_json)
            cart = Cart()
            
            # Varre os produtos recebidos no carrinho
            for product in input_json['products']:
                prod_id,prod_qnt = product['id'],product['quantity']
                
                # Busca preço e desconto
                try:
                    amount,is_gift = ProductDatabase().get_price_gift(prod_id)
                except KeyError:
                    # Mercadoria não encontrada, não retorna. Ideal seria possibilidade de
                    # avisar o chamador que essa mercadoria precisa ser removida do carrinho
                    continue

                discount_percentage = DiscountEngine(5).get_discount(prod_id)
                
                product = Product(prod_id, prod_qnt, amount, discount_percentage)
                cart.add_product(product)
                if is_gift:
                    self.black_friday_products.append(product)                
            
            # No futuro pode ser interessante expandir para uma lista de regras de negócio
            # para pré e pós processamento da venda
            p = self.black_friday_engine.apply(self.black_friday_products)
            if p is not None:
                p.is_gift = True
                EventNotifierManager().notify_event("debug", "Produto {0} retornado como gift".format(p.id))

            return json.dumps(cart, default=lambda o: o.__dict__)
        except Exception as e:
            EventNotifierManager().notify_event("error", e)
            raise

class ShopCartServer(object):

    """ Implementa um handler do CherryPy para tratar o serviço
    
        A opção pelo CherryPy foi feita devido a sua  escalabilidade e simplici-
        dade. Exceções são tratadas de maneira relativamente graciosa por ele e
        há a possibilidade de parametrizar inclusive acesso via certificado  di-
        gital.
    """

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
    
    EventNotifierManager().add_event_listener("error", SaveToFileNotifier())
    EventNotifierManager().add_event_listener("error", PrintToScreenNotifier())
    EventNotifierManager().add_event_listener("debug", PrintToScreenNotifier())
    
    cherrypy.config.update({'server.socket_host':"0.0.0.0", 'server.socket_port':8181, 'log.screen': False, 'log.access_file': "access1.log", 'log.error_file': "error1.log"})
    cherrypy.quickstart(ShopCartServer(), '/')

