import random
import string
from time import sleep, time
from threading import Thread

import Pyro5
from Pyro5.api import locate_ns, Proxy
from Pyro5.server import Daemon
from simple_term_menu import TerminalMenu

# Global variables


class Peer(object):
    name: str
    heartbeat_ms = 200
    margin_ms = 5000
    peer_dict: dict[str, float] = {}

    @Pyro5.api.expose
    @Pyro5.api.oneway
    def heartbeat(self, t_peer_name):
        print(f" [*] Received heartbeat from {t_peer_name}")
        Peer.peer_dict[t_peer_name] = time()


def _init_peer():
    daemon = Daemon()  # make a Pyro daemon
    name_server = locate_ns()  # find the name server

    # List all existing peers
    existing_peer_list = name_server.list()
    existing_peer_list.pop("Pyro.NameServer")
    
    references_names = list(existing_peer_list.keys())
    
    # Populate all possible active peers
    print(list(existing_peer_list.keys()))
    for key in list(existing_peer_list.keys()):
        Peer.peer_dict[key] = time()

    # Initialize peer name
    while True:
        random_letter = random.choice(string.ascii_letters).upper()
        peer_name = "peer" + random_letter

        if peer_name in references_names:
            continue

        break

    uri = daemon.register(
        Peer.heartbeat
    )  # register the greeting maker as a Pyro object
    name_server.register(
        peer_name, uri
    )  # register the object with a name in the name server

    print(f" [*] Peer is ready as {peer_name}")

    return daemon, name_server, peer_name


def _peer_request_worker(daemon: Daemon):
    daemon.requestLoop()


def _peer_heartbeat_worker():    
    while True:
        sleep(Peer.heartbeat_ms / 1000)

        for key, value in Peer.peer_dict.items():
            now = time()
            
            print(f"Peer.margin_ms: ", Peer.margin_ms)
            print(f"now - value", now - value)
            
            if now - value > Peer.margin_ms:
                print(f" [*] {key} has died.")
                Peer.peer_dict.pop(key)

        for key in list(Peer.peer_dict.keys()):
            print(f" [*] Connecting to {key}")
            
            name_server = locate_ns()
            t_uri = name_server.lookup(key)
            print(t_uri, Peer.name)
            t_peer = Proxy(t_uri)
            print(t_peer.__annotations__)
            t_peer.heartbeat(Peer.name)


def _init_menu():
    while True:
        options = [
            "Requisitar recurso",
            "Liberar recurso",
            "Listar peers ativos",
            None,
            "Sair",
        ]

        terminal_menu = TerminalMenu(options)
        menu_entry_index = terminal_menu.show()
        menu_entry = options[menu_entry_index]

        if menu_entry == "Sair":
            break

        if menu_entry == "Requisitar recurso":
            continue

        if menu_entry == "Liberar recurso":
            continue

        if menu_entry == "Listar peers ativos":
            print(Peer.peer_dict)
            continue


def main():
    daemon, name_server, peer_name = _init_peer()

    Peer.name = peer_name

    peer_request_worker = Thread(
        target=_peer_request_worker, args=(daemon,), daemon=True
    )
    peer_request_worker.start()

    peer_heartbeat_worker = Thread(
        target=_peer_heartbeat_worker,
    )
    peer_heartbeat_worker.start()

    _init_menu()


if __name__ == "__main__":
    main()
