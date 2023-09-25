import Pyro5.api
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA


class Client(object):
    def __init__(self):
        self.name = 'client1'
        self.public_key = RSA.import_key(open('keys/public_key.der').read())
        self.remote_object_reference = 'PYRONAME:product.stock'
        self.connection = None

    def connect(self):
        self.connection = Pyro5.api.Proxy(self.remote_object_reference)

    def register_client(self, name, public_key, remote_object_reference):
        self.connection.register_client(name, str(public_key), remote_object_reference)

    def post_product(self, code, name, description, quantity, price, stock):

        message = bytes(code + name + description + str(quantity) + str(price) + str(stock), 'utf-8')
        key = RSA.import_key(open('keys/private_key.der').read())
        h = SHA256.new(message)
        signature = pkcs1_15.new(key).sign(h)

        self.connection.register_product(code, name, description, quantity, price, stock, signature)

    def remove_product(self, code, quantity):
        self.connection.remove_product(code, quantity)

    def get_product(self):
        a = self.connection.get_product()
        print(a)
        return a

    def get_stock_log(self, initial_date, final_date):
        a = self.connection.get_stock_log(initial_date, final_date)
        print(a)
        return a

    def get_products_withouth_movement(self, initial_date, final_date):
        a = self.connection.get_products_withouth_movement(initial_date, final_date)
        print(a)
        return a



def main():
    client = Client()
    client.connect()
    # client.register_client(client.name, client.public_key, client.remote_object_reference)
    # client.post_product('123', 'test', 'test', 1, 1, 1)
    # client.get_product()
    # client.get_stock_log('2023-09-20', '2023-09-22')
    # client.get_products_withouth_movement('2023-09-20', '2023-09-22')
    client.remove_product('120', 1)

if __name__ == "__main__":
    main()
