import pandas as pd
import numpy as np
import Pyro5.api
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from datetime import datetime


class Server(object):
    def __init__(self):
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
        df = pd.DataFrame({'name': [name],
                           'public_key': [public_key],
                           'remote_object_reference': [remote_object_reference]})
        # save to csv file
        df.to_csv('csvs/clients.csv', mode='a', header=False, index=False)
        print('Client registered successfully')

        self.clients = pd.read_csv('csvs/clients.csv')

    @Pyro5.api.expose
    def register_product(self, code, name, description, quantity, price, stock, signature):
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
        code = int(code)
        quantity = int(quantity)
        # check if product exists
        if code in self.products['code'].values:
            # check if quantity is valid
            if quantity <= self.products.loc[self.products['code'] == code, 'quantity'].values[0]:
                self.products.loc[self.products['code'] == code, 'quantity'] -= quantity
                self.products.to_csv('csvs/products.csv', index=False)
                print('Product removed successfully')

                # update stock.csv with movement (add or remove) and quantity of products
                self.update_stock_log(code, quantity, datetime.now().strftime("%d/%m/%Y"),
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

        # get products withouth movement in a period of time. So look for products that are in products.csv but not in stock.csv in the period of time, using stock.csv date as reference
        products_withouth_movement = self.products.loc[~self.products['code'].isin(
            self.stock.loc[(self.stock['date'] >= initial_date) & (self.stock['date'] <= final_date)]['code'])]

        return products_withouth_movement.to_string(index=False)

    @Pyro5.api.expose
    def notification(self):
        # get products that stock is lesser than quantity
        products = self.products.loc[self.products['stock'] < self.products['quantity']]
        # get products that haven't had negative movement in 3 days
        products_withouth_movement = self.products.loc[~self.products['code'].isin(
            self.stock.loc[(self.stock['date'] >= datetime.now().strftime("%d/%m/%Y")) & (
                    self.stock['date'] <= (datetime.now() - pd.DateOffset(days=3)).strftime("%d/%m/%Y"))][
                'code'])]




def main():
    daemon = Pyro5.api.Daemon()  # make a Pyro daemon
    ns = Pyro5.api.locate_ns()  # find the name server
    uri = daemon.register(Server)  # register the greeting maker as a Pyro object
    ns.register("product.stock", uri)  # register the object with a name in the name server

    print("Ready.")
    daemon.requestLoop()  # start the event loop of the server to wait for calls


if __name__ == "__main__":
    main()
