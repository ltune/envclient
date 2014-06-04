from main.listener import Client

if __name__ == '__main__':
    client = Client('/dev/ttyUSB0')
    client.start()