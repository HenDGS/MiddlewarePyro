import PySimpleGUI as sg
import os
import sys
import time
import threading
from client import Client


# create a gui for client methods
def gui():
    sg.theme('DarkAmber')
    layout = [[sg.Text('Client')],
              [sg.Text('Choose an option:')],
              [sg.Button('Register client'), sg.Button('Post product'), sg.Button('Remove product'), sg.Button('Get '
                                                                                                               'products in stock'),
               sg.Button('Get Stock Log'), sg.Button('Get products withouth movement'), sg.Button('Get Notification'), sg.Button('Get Notification2')], [sg.Button('Exit')]]

    # Create the Window
    window = sg.Window('Client', layout)

    client = Client()
    client.connect()

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Exit':
            break

        if event == 'Register client':
            client.register_client(client.name, client.public_key, client.remote_object_reference)
            sg.popup('Client registered successfully')

        if event == 'Post product':
            layout = [[sg.Text('Code:'), sg.InputText()],
                      [sg.Text('Name:'), sg.InputText()],
                      [sg.Text('Description:'), sg.InputText()],
                      [sg.Text('Quantity:'), sg.InputText()],
                      [sg.Text('Price:'), sg.InputText()],
                      [sg.Text('Stock:'), sg.InputText()],
                      [sg.Button('Submit'), sg.Button('Cancel')]]

            window2 = sg.Window('Post product', layout)

            while True:
                event2, values2 = window2.read()

                if event2 == sg.WIN_CLOSED or event2 == 'Cancel':
                    break

                if event2 == 'Submit':
                    client.post_product(values2[0], values2[1], values2[2], values2[3], values2[4], values2[5])
                    sg.popup('Product posted successfully')

            window2.close()

        if event == 'Remove product':
            layout = [[sg.Text('Code:'), sg.InputText()],
                      [sg.Text('Quantity:'), sg.InputText()],
                      [sg.Button('Submit'), sg.Button('Cancel')]]

            window2 = sg.Window('Remove product', layout)

            while True:
                event2, values2 = window2.read()

                if event2 == sg.WIN_CLOSED or event2 == 'Cancel':
                    break

                if event2 == 'Submit':
                    client.remove_product(values2[0], values2[1])
                    sg.popup('Product removed successfully')

            window2.close()

        if event == 'Get products in stock':
            response = client.get_product()
            sg.popup(response)

        if event == 'Get Stock Log':
            layout = [[sg.Text('Initial date:'), sg.InputText()],
                      [sg.Text('Final date:'), sg.InputText()],
                      [sg.Button('Submit'), sg.Button('Cancel')]]

            window2 = sg.Window('Get Stock Log', layout)

            while True:
                event2, values2 = window2.read()

                if event2 == sg.WIN_CLOSED or event2 == 'Cancel':
                    break

                if event2 == 'Submit':
                    response = client.get_stock_log(values2[0], values2[1])
                    sg.popup(response)

            window2.close()

        if event == 'Get products withouth movement':
            layout = [[sg.Text('Initial date:'), sg.InputText()],
                      [sg.Text('Final date:'), sg.InputText()],
                      [sg.Button('Submit'), sg.Button('Cancel')]]

            window2 = sg.Window('Get products withouth movement', layout)

            while True:
                event2, values2 = window2.read()

                if event2 == sg.WIN_CLOSED or event2 == 'Cancel':
                    break

                if event2 == 'Submit':
                    response = client.get_products_withouth_movement(values2[0], values2[1])
                    sg.popup(response)

            window2.close()

        if event == 'Get Notification':
            response = client.get_notification()
            sg.popup(response)

        if event == 'Get Notification2':
            response = client.get_notification2()
            sg.popup(response)

    window.close()


def main():
    gui()


if __name__ == "__main__":
    main()
