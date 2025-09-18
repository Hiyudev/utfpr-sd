import random
import string
from threading import Thread

from Pyro5.api import expose, locate_ns
from Pyro5.server import Daemon
from simple_term_menu import TerminalMenu

# Global variables
peer_list: dict[str, str] = []
heartbeat_ms = 200
daemon = None
nameserver = None
peer_name = None


class Peer(object):
    @expose
    def example_method():
        return "Hello World!"


# Pyro5.api.Proxy("PYRONAME:example.greeting")


def _init_peer():
    daemon = Daemon()  # make a Pyro daemon
    nameserver = locate_ns()  # find the name server

    # List all existing peers
    peer_list = nameserver.list()
    references_names = list(peer_list.keys())

    # Initialize peer name
    while True:
        random_letter = random.choice(string.ascii_letters).upper()
        peer_name = "peer" + random_letter

        if peer_name in references_names:
            continue

        break

    uri = daemon.register(
        Peer.example_method
    )  # register the greeting maker as a Pyro object
    nameserver.register(
        peer_name, uri
    )  # register the object with a name in the name server

    print(" [*] Peer is ready.")


def _peer_worker(daemon):
    daemon.requestLoop()


def _init_menu():
    while True:
        options = ["Requisitar SC", "Liberar SC", "Listar os pares", None, "Sair"]

        terminal_menu = TerminalMenu(options)
        menu_entry_index = terminal_menu.show()
        menu_entry = options[menu_entry_index]

        if menu_entry == "Sair":
            break

        if menu_entry == "Listar os pares":
            print(peer_list)
            continue

    nameserver.remove(peer_name)


if __name__ == "__main__":
    _init_peer()

    peer_thread = Thread(target=_peer_worker, args=(daemon,), daemon=True)
    peer_thread.start()

    _init_menu()
