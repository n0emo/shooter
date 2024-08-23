import socket
import threading

from ..shared.game import Game
from ..shared.settings import SERVER_ADDRESS

from . import thread


game = Game()
client_threads = []


def check_threads():
    global client_threads

    while True:
        client_threads = [t for t in client_threads if t.is_alive()]

def stop_all():
    global client_threads

    for thread in client_threads:
        thread.stop()

    client_threads.clear()


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(SERVER_ADDRESS)
    sock.listen(5)

    threading.Thread(target=check_threads)

    try:
        while True:
            client_sock, address = sock.accept()
            client_thread = thread.ClientThread(client_sock, address, game)
            client_thread.start()
            client_threads.append(client_thread)
    except KeyboardInterrupt:
        exit(1)
    except Exception as e:
        print(e)
        exit(1)
    finally:
        stop_all()
        sock.close()

