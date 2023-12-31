import base64
import threading
import Pyro5.api
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
import queue


class Client(object):
    def __init__(self):
        self.name = 'client1'
        self.public_key = RSA.import_key(open('keys/public_key.der').read())
        self.remote_object_reference = 'PYRONAME:product.stock'
        self.connection = None
        self.q = queue.Queue()

    def connect(self):
        self.connection = Pyro5.api.Proxy(self.remote_object_reference)

    def register_client(self, name, public_key, remote_object_reference):
        pub_key_bytes = self.public_key.export_key()
        pub_key_string = pub_key_bytes.decode('utf-8')

        self.connection.register_client(name, pub_key_string, remote_object_reference)

    def post_product(self, code, name, description, quantity, price, stock):
        message = bytes(f'{code}{name}{description}{quantity}{price}{stock}', encoding='utf8')
        # message = b'To be signed'
        key = RSA.import_key(open("keys/private_key.der").read())
        h = SHA256.new(message)
        signature = pkcs1_15.new(key).sign(h)
        signature_string = base64.b64encode(signature).decode('utf-8')

        self.connection.register_product(code, name, description, quantity, price, stock, signature_string)

    def remove_product(self, code, quantity):
        message = bytes(f'{code}{''}{''}{quantity}{''}{''}', encoding='utf8')

        key = RSA.import_key(open("keys/private_key.der").read())
        h = SHA256.new(message)
        signature = pkcs1_15.new(key).sign(h)
        signature_string = base64.b64encode(signature).decode('utf-8')

        self.connection.remove_product(code, quantity, signature_string)

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

    @Pyro5.api.callback
    @Pyro5.api.expose
    def do_something_on_get_notification(self, notification1, notification2):
        print(f'Products With Stock Lower Than Quantity: {notification1}')
        print(f'Products Without Movement: {notification2}')
        # add to queue
        self.q.put(notification1)
        self.q.put(notification2)


def main():
    Pyro5.api.config.SERVERTYPE = "thread"
    client = Client()
    client.connect()

    daemon = Pyro5.api.Daemon()  # create a Pyro5 daemon
    client_uri = daemon.register(client)  # register the client as a Pyro object

    threading.Thread(target=daemon.requestLoop).start()

    client.register_client(client.name, client.public_key, client)


if __name__ == "__main__":
    main()
