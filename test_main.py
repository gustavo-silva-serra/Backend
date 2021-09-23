#!/usr/bin/python3

import unittest

from main import *

class TestMain(unittest.TestCase):

    def test_empty_products(self):
        """ Testa o tratamento de black friday para uma lista vazia """
        self.assertEqual(DefaultBlackFridayEngine().apply([]), None)

    def test_no_gift_products(self):
        """ Testa o tratamento de black friday padrão """
        products = [Product(1, 1, 1, 0), Product(2, 1, 500, 0), Product(3, 1, 10, 0)]
        self.assertEqual(DefaultBlackFridayEngine().apply(products).id, 1)

    def test_discount(self):
        """ Testa o comportamento para descontos em produtos """
        self.assertEqual(Product(prod_id=1, quantity=1, amount=123, discount_percentage=1).discount, 0)
        self.assertEqual(Product(prod_id=1, quantity=1, amount=123, discount_percentage=0.5).discount, 61)
        self.assertEqual(Product(prod_id=1, quantity=1, amount=123, discount_percentage=0).discount, 0)
        self.assertEqual(Product(prod_id=1, quantity=1, amount=123, discount_percentage=-0.5).discount, 0)

    def test_cart_total(self):
        """ Testa os valores totais do carrinho """
        cart1 = Cart()
        self.assertEqual(cart1.total_amount, 0)
        self.assertEqual(cart1.total_discount, 0)
        self.assertEqual(cart1.total_amount_with_discount, 0)
        cart1.add_product(Product(prod_id=1, quantity=1, amount=1, discount_percentage=0))
        self.assertEqual(cart1.total_amount, 1)
        self.assertEqual(cart1.total_discount, 0)
        self.assertEqual(cart1.total_amount_with_discount, 1)
        cart1.add_product(Product(prod_id=2, quantity=10, amount=5000, discount_percentage=0.2))
        self.assertEqual(cart1.total_amount, 50001) # R$ 501,01
        self.assertEqual(cart1.total_discount, 10000)
        self.assertEqual(cart1.total_amount_with_discount, 40001)

    def test_discount_engine(self):
        """ Testa o comportamento da engine de descontos para produto inexistente """
        self.assertEqual(DiscountEngine().get_discount(-1), 0)

if __name__ == '__main__':

    if 'GRPC_IP_PORT' not in os.environ:
        raise Exception('Você deve configurar a variável GRPC_IP_PORT com o IP do serviço de desconto no formato IP:PORTA')
            
    unittest.main()
