#!/usr/bin/python3

# import grpc
import json
import cherrypy
import time
import abc
import os

class ProductDatabase:
    """ Database proxy

        As the database gets bigger, it might be necessary a more sophisticated mechanism
        that does not load all products in memory. Another thing to consider is that 
        products may have their price updated.
    """
    products_map = {}
    
    def __init__(self):
        """ Load products in memory """
        if not ProductDatabase.products_map:
            products_db = json.loads(open('products.json').read())
            ProductDatabase.products_map = {product['id']:product for product in products_db}
    
    def get_price_gift(self,product_id):
        """Return price and gift flag for a given id"""
        return int(ProductDatabase.products_map[product_id]['amount']),bool(ProductDatabase.products_map[product_id]['is_gift'])

class EventNotifier(abc.ABC):
    """ 
        Abstract class for events notification
    """
    @abc.abstractmethod
    def notify_event(self,event):
        pass

class PrintToScreenNotifier(EventNotifier):
    def notify_event(self,event):
        print(event)

class SaveToFileNotifier(EventNotifier):
    def notify_event(self,event):
        with open('application_log.txt', 'a') as f:
            f.write(str(event))

class EventNotifierManager:
    """ 
        Implements a crude observer for system events
    """
    listeners = {}
    
    def add_event_listener(self, event_type, listener):
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)
    
    def notify_event(self,event_type, event):
        if event_type in self.listeners:
            for l in self.listeners[event_type]:
                l.notify_event(event)

class DiscountEngine:
    """ Proxy for the discount engine
    
        It implements a simple cache mechanism.
    """
    
    cache_timeout = 0
    cached = {}    
    last_error_time = 0 # timestamp of last network error
    
    def get_discount(self,product_id):
        
        # if a cache is set, search in it first
        if DiscountEngine.cache_timeout> 0:
            if product_id in DiscountEngine.cached.keys():
                if time.time() - DiscountEngine.cached[product_id][0] < self.cache_timeout:
                    return DiscountEngine.cached[product_id][1]
        
        if DiscountEngine.last_error_time > 0:
            if time.time() - DiscountEngine.last_error_time < 5:
                return 0
                
        # there is no cache or the product was not found
        try:
            # channel = grpc.insecure_channel(os.environ['GRPC_IP_PORT'])
            # stub = discount_pb2_grpc.DiscountStub(channel)
            # perc = float(stub.GetDiscount(discount_pb2.GetDiscountRequest(productID = product_id), timeout=2).percentage)
            DiscountEngine.last_error_time = 0
            perc = 0
        except Exception as e:
            DiscountEngine.last_error_time = time.time()
            EventNotifierManager().notify_event("error", e)
            return 0
        
        # Updates the cache. Even though is a very simple mechanism, it is easy to understand
        # and to maintain
        if DiscountEngine.cache_timeout> 0:
            if len(DiscountEngine.cached) > 10000: # Truncates cache
                DiscountEngine.cached = {}
            DiscountEngine.cached[product_id] = (time.time(), perc)
            
        return perc

class Product:
    def __init__(self, prod_id, quantity, amount, discount_percentage):
        assert(int(quantity) > 0)
        assert(int(amount) > 0)
        assert(int(prod_id) > 0)
        self.id = int(prod_id)
        self.quantity = int(quantity)
        self.unit_amount = int(amount)
        self.total_amount = self.quantity * self.unit_amount
        self.discount = 0
        if discount_percentage > 0 and discount_percentage < 1:
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

class DefaultBlackFridayEngine:
    def apply(self, products):
        """ Chooses the cheapest product """
        if len(products) <= 0:
            return None
        return sorted(products, key=lambda x: x.total_amount)[0]

class ShopCart:
    def __init__(self):
        self.black_friday_engine = DefaultBlackFridayEngine() # Easy to change for another stategy if necessary
        self.black_friday_products = [] # Avoids to put is_gift inside of the product
        
    def process(self, input_json):
        try:
            try:
                input_json = json.loads(input_json)
            except:
                raise cherrypy.HTTPError(500, 'Error parsing JSON')
            cart = Cart()
            
            for product in input_json['products']:
                prod_id,prod_qnt = product['id'],product['quantity']
                
                if prod_qnt <= 0:
                    continue
                
                try:
                    amount,is_gift = ProductDatabase().get_price_gift(prod_id)
                except KeyError:
                    # Product not found. Should tell caller that this product should be removed
                    continue

                discount_percentage = DiscountEngine().get_discount(prod_id)
                
                product = Product(prod_id, prod_qnt, amount, discount_percentage)
                cart.add_product(product)
                if is_gift:
                    self.black_friday_products.append(product)                
            
            p = self.black_friday_engine.apply(self.black_friday_products)
            if p is not None:
                p.is_gift = True
                EventNotifierManager().notify_event("debug", "Product {0} is a  gift".format(p.id))

            cherrypy.response.headers['Content-Type'] = 'application/json'
            return json.dumps(cart, default=lambda o: o.__dict__).encode('utf8')
        except Exception as e:
            EventNotifierManager().notify_event("error", e)
            raise

class ShopCartServer(object):

    """ Cherrypy handler

    """
    
    # @cherrypy.tools.json_out()
    @cherrypy.expose
    def index(self):
        cart = ShopCart()
        return cart.process(cherrypy.request.body.read().decode("utf-8"))

    # Não sabia qual o nome do endpoint esperado, então criei os dois abaixo
    @cherrypy.expose
    def checkout(self):
        cart = ShopCart()
        return cart.process(cherrypy.request.body.read().decode("utf-8"))
    
    @cherrypy.expose
    def carrinho(self):
        cart = ShopCart()
        return cart.process(cherrypy.request.body.read().decode("utf-8"))        
    

if __name__ == "__main__":
    
    if 'LISTEN_PORT' not in os.environ:
        raise Exception('Você deve configurar a variável LISTEN_PORT com a porta deste serviço')
    
    if 'DISCOUNT_CACHE' in os.environ:
        DiscountEngine.cache_timeout = int(os.environ['DISCOUNT_CACHE'])
    else:
        DiscountEngine.cache_timeout = 5
        
    EventNotifierManager().add_event_listener("error", SaveToFileNotifier())
    EventNotifierManager().add_event_listener("error", PrintToScreenNotifier())
    EventNotifierManager().add_event_listener("debug", PrintToScreenNotifier())

    print('Bem-vindo ao programa Backend')
    print('Estamos prontos e executando na porta',os.environ['LISTEN_PORT'])

    # if it is necessary to increase thread number, use 'server.thread_pool':x
    cherrypy.config.update({'server.socket_host':"0.0.0.0", 
                            'server.socket_port':int(os.environ['LISTEN_PORT']),
                            'log.screen': False, # dont print on screen
                            'log.access_file': "access1.log", 
                            'log.error_file': "error1.log",
                            'request.show_tracebacks': True}) # True to return stack trace, use False in production
    cherrypy.quickstart(ShopCartServer(), '/', {})

