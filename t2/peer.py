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
    heartbeat_s = 2
    timeout_s = 3 * heartbeat_s
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
        Peer()
    )  # register the Peer instance as a Pyro object
    name_server.register(
        peer_name, uri
    )  # register the object with a name in the name server

    print(f" [*] Peer is ready as {peer_name}")

    return daemon, name_server, peer_name


def _peer_request_worker(daemon: Daemon):
    daemon.requestLoop()


def _peer_heartbeat_worker():    
    while True:
        sleep(Peer.heartbeat_s)

        removed_keys: list[str] = []
        for key, value in Peer.peer_dict.items():
            now = time()
            
            if now - value > Peer.timeout_s:
                print(f" [*] {key} has died.")
                removed_keys.append(key)

        for removed_key in removed_keys:
            Peer.peer_dict.pop(removed_key)

        for key in list(Peer.peer_dict.keys()):
            print(f" [*] Connecting to {key}")
            
            name_server = locate_ns()
            t_uri = name_server.lookup(key)
            
            try:
                t_peer = Proxy(t_uri)
                t_peer.heartbeat(Peer.name)
            except Exception as e:
                print(f" [*] Error: {e}")


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
