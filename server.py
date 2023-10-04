import base64
import threading
import time
from datetime import datetime
import Pyro5.api
import pandas as pd
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15


class Server(object):
    def __init__(self):
        self.logged_on_clients = {}

        try:
            pd.read_csv('csvs/clients.csv')
        except FileNotFoundError:
            df = pd.DataFrame({'name': [],
                               'public_key': [],
                               'remote_object_reference': []})
            df.to_csv('csvs/clients.csv', index=False)

        try:
            pd.read_csv('csvs/products.csv')
        except FileNotFoundError:
            df = pd.DataFrame({'code': [],
                               'name': [],
                               'description': [],
                               'quantity': [],
                               'price': [],
                               'stock': [],
                               'date': [],
                               'hour': []})
            df.to_csv('csvs/products.csv', index=False)

        try:
            pd.read_csv('csvs/stock.csv')
        except FileNotFoundError:
            df = pd.DataFrame({'code': [],
                               'quantity': [],
                               'date': [],
                               'hour': []})
            df.to_csv('csvs/stock.csv', index=False)

        self.stock = pd.read_csv('csvs/stock.csv')
        self.clients = pd.read_csv('csvs/clients.csv')
        self.products = pd.read_csv('csvs/products.csv')

    @Pyro5.api.expose
    def register_client(self, name, public_key, remote_object_reference):
        # client_proxy = Pyro5.api.Proxy(remote_object_reference)
        # remote_object_reference = client_proxy._pyroUri.asString()
        # self.logged_on_clients[name] = client_proxy

        remote_object_reference2 = remote_object_reference
        self.logged_on_clients[name] = remote_object_reference

        remote_object_reference = str(remote_object_reference)

        print(f'Client {name} registered successfully')

        df = pd.DataFrame({'name': [name],
                           'public_key': [public_key],
                           'remote_object_reference': [remote_object_reference]})

        df.to_csv('csvs/clients.csv', mode='a', header=False, index=False)
        print('Client registered successfully')

        self.clients = pd.read_csv('csvs/clients.csv')

        # todo remove after test
        # self.notification(remote_object_reference2)
        self.notification_thread()

    @Pyro5.api.expose
    def register_product(self, code, name, description, quantity, price, stock, signature_string):
        signature = base64.b64decode(signature_string)

        # for key in self.clients['public_key'].values:
        key_string = self.clients['public_key'].values[-1]
        # use keys/public_key.der to verify signature
        message = bytes(f'{code}{name}{description}{quantity}{price}{stock}', encoding='utf8')
        # message = b'To be signed'
        key = RSA.import_key(key_string)
        h = SHA256.new(message)
        try:
            pkcs1_15.new(key).verify(h, signature)
            print("The signature is valid.")
        except (ValueError, TypeError):
            print("The signature is not valid.")

        df = pd.DataFrame({'code': [code],
                           'name': [name],
                           'description': [description],
                           'quantity': [quantity],
                           'price': [price],
                           'stock': [stock]})

        df['date'] = datetime.now().strftime("%d/%m/%Y")
        df['hour'] = datetime.now().strftime("%H:%M:%S")

        # save to csv file
        df.to_csv('csvs/products.csv', mode='a', header=False, index=False)
        print('Product registered successfully')

        self.products = pd.read_csv('csvs/products.csv')

        self.update_stock_log(code, quantity, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M:%S"))

    @Pyro5.api.expose
    def remove_product(self, code, quantity):
        code = str(code)
        quantity = int(quantity)
        # check if product exists
        if code in self.products['code'].values:
            # check if quantity is valid
            if quantity <= self.products.loc[self.products['code'] == code, 'quantity'].values[0]:
                self.products.loc[self.products['code'] == code, 'quantity'] -= quantity
                self.products.to_csv('csvs/products.csv', index=False)
                print('Product removed successfully')

                # update stock.csv with movement (add or remove) and quantity of products
                self.update_stock_log(code, quantity * -1, datetime.now().strftime("%d/%m/%Y"),
                                      datetime.now().strftime("%H:%M:%S"))
            else:
                print('Invalid quantity')
        else:
            print('Product not found')

    @Pyro5.api.expose
    def update_stock_log(self, code, quantity, date, hour):
        # update stock.csv with movement (add or remove) and quantity of products
        df = pd.DataFrame({'code': [code],
                           'quantity': [quantity],
                           'date': [date],
                           'hour': [hour]})
        df.to_csv('csvs/stock.csv', mode='a', header=False, index=False)

        self.stock = pd.read_csv('csvs/stock.csv')

        print('Stock log updated successfully')

    @Pyro5.api.expose
    def get_product(self):
        # return products with quantity > 0
        return self.products.loc[self.products['quantity'] > 0].to_string(index=False)

    @Pyro5.api.expose
    def get_stock_log(self, initial_date, final_date):
        self.stock['date'] = pd.to_datetime(self.stock['date'], format="%d/%m/%Y")

        return self.stock.loc[(self.stock['date'] >= initial_date) & (self.stock['date'] <= final_date)].to_string(
            index=False)

    @Pyro5.api.expose
    def get_products_withouth_movement(self, initial_date, final_date):
        # get products withouth movement in a period of time
        self.stock['date'] = pd.to_datetime(self.stock['date'], format="%d/%m/%Y")

        products_withouth_movement = self.products.loc[~self.products['code'].isin(
            self.stock.loc[(self.stock['date'] >= initial_date) & (self.stock['date'] <= final_date)]['code'])]

        return products_withouth_movement.to_string(index=False)

    @Pyro5.api.expose
    def notification(self):
        while True:
            products = self.products.loc[self.products['stock'] < self.products['quantity']]

            products_in_both = self.products.loc[self.products['code'].isin(self.stock['code'])]
            products_with_negative_movement = self.stock.loc[self.stock['quantity'] < 0]
            products_with_negative_movement_in_the_last_3_days = products_with_negative_movement.loc[
                products_with_negative_movement['date'] >= (datetime.now() - pd.Timedelta(days=3)).strftime("%d/%m/%Y")]
            products_withouth_movement = products_in_both.loc[~products_in_both['code'].isin(
                products_with_negative_movement_in_the_last_3_days['code'])]

            for client in self.logged_on_clients.values():
                try:
                    print(f'Notifying client {client}')
                    client._pyroClaimOwnership()
                    client.do_something_on_get_notification(products.to_string(index=False),
                                                            products_withouth_movement.to_string(
                                                                index=False))
                except Exception as e:
                    pass

            time.sleep(30)

    def notification_thread(self):
        threading.Thread(target=self.notification).start()

    @Pyro5.api.expose
    def notification2(self):
        # get products that haven't had negative movement in 3 days. Based on existing codes in self.products,
        # and movement / negative value are in self.stock
        products_in_both = self.products.loc[self.products['code'].isin(self.stock['code'])]
        products_with_negative_movement = self.stock.loc[self.stock['quantity'] < 0]
        products_with_negative_movement_in_the_last_3_days = products_with_negative_movement.loc[
            products_with_negative_movement['date'] >= (datetime.now() - pd.Timedelta(days=3)).strftime("%d/%m/%Y")]
        products_withouth_movement = products_in_both.loc[~products_in_both['code'].isin(
            products_with_negative_movement_in_the_last_3_days['code'])]
        return products_withouth_movement.to_string(index=False)

    def register_client_in_server(self, name, client_uri, remote_object_reference):
        client_proxy = Pyro5.api.Proxy(client_uri)


def main():
    daemon = Pyro5.api.Daemon()  # make a Pyro daemon
    ns = Pyro5.api.locate_ns()  # find the name server
    server = Server()
    uri = daemon.register(Server)  # register the greeting maker as a Pyro object
    ns.register("product.stock", uri)  # register the object with a name in the name server
    print("Ready.")
    daemon.requestLoop()  # start the event loop of the server to wait for calls


if __name__ == "__main__":
    main()
