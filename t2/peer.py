import random
import string
from time import sleep, time
from PyThreadKiller import PyThreadKiller

import Pyro5
from Pyro5.api import locate_ns, Proxy
from Pyro5.server import Daemon
from simple_term_menu import TerminalMenu
from apscheduler.schedulers.background import BackgroundScheduler

# TODO: Quando um Peer morre, realiza tratamento caso o State = Wanted
# TODO: Monopolização do recurso do Peer, utilizando Scheduler + Release

scheduler = BackgroundScheduler()

class Peer(object):
    name: str
    heartbeat_s = 2
    timeout_s = 3 * heartbeat_s

    request_timestamp: float = -1
    reply_count = -1
    maximum_count = -1
    
    timeout_job = None
    state: str = "RELEASED"

    # Guarda as requisições pendentes, que serão respondidas no momento em que o SC for liberado
    # Sidequest: Caso tenha duplicados, prioriza elas (escalonamento)
    queued_request_list: set[str] = set()

    # Guarda todos os pares ativos, e seus respectivos tempos do último heartbeat/interação
    peer_dict: dict[str, float] = {}

    @Pyro5.api.expose
    @Pyro5.api.oneway
    def heartbeat(self, t_peer_name):
        Peer.peer_dict[t_peer_name] = time()

    def enter_section():
        if Peer.state != "RELEASED":
            return None

        Peer.state = "WANTED"
        peer_name_list = list(Peer.peer_dict.keys())

        Peer.maximum_count = len(peer_name_list)
        Peer.reply_count = 0
        Peer.request_timestamp = time()

        for peer_name in peer_name_list:
            name_server = locate_ns()
            t_uri = name_server.lookup(peer_name)

            try:
                t_peer = Proxy(t_uri)
                t_timestamp = time()
                answer: bool = t_peer.request(Peer.name, t_timestamp)

                if answer:
                    Peer.reply_count += 1
            except Exception as e:
                print(f" [*] Error: {e}")

        if Peer.reply_count == Peer.maximum_count:
            Peer.state = "HELD"
            Peer.timeout_job = scheduler.add_job(Peer.exit_section, 'interval', minutes=1)

    def exit_section():
        if Peer.state != "HELD":
            return None

        Peer.state = "RELEASED"

        for peer_name in Peer.queued_request_list:
            name_server = locate_ns()
            t_uri = name_server.lookup(peer_name)

            try:
                t_peer = Proxy(t_uri)
                t_peer.release()
            except Exception as e:
                print(f" [*] Error: {e}")
                
        Peer.queued_request_list.clear()
        Peer.timeout_job.remove()
        Peer.timeout_job = None

    @Pyro5.api.expose
    def request(self, peer_name: str, timestamp: float):
        if Peer.state == "HELD" or (
            Peer.state == "WANTED" and Peer.request_timestamp < timestamp
        ):
            Peer.queued_request_list.add(peer_name)
            return False

        return True

    @Pyro5.api.expose
    @Pyro5.api.oneway
    def release(self):
        Peer.reply_count += 1

        if Peer.reply_count == Peer.maximum_count:
            Peer.state = "HELD"
            Peer.timeout_job = scheduler.add_job(Peer.exit_section, 'interval', minutes=1)


def _init_peer():
    daemon = Daemon()  # make a Pyro daemon
    name_server = locate_ns()  # find the name server

    # List all existing peers
    existing_peer_list = name_server.list()
    existing_peer_list.pop("Pyro.NameServer")

    references_names = list(existing_peer_list.keys())

    # Populate all possible active peers
    for key in list(existing_peer_list.keys()):
        Peer.peer_dict[key] = time()

    # Initialize peer name
    while True:
        random_letter = random.choice(string.ascii_letters).upper()
        peer_name = "peer" + random_letter

        if peer_name in references_names:
            continue

        break

    uri = daemon.register(Peer())  # register the Peer instance as a Pyro object
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
                
                if Peer.state == "WANTED":
                    Peer.enter_section()

        for removed_key in removed_keys:
            Peer.peer_dict.pop(removed_key)

        for key in list(Peer.peer_dict.keys()):
            name_server = locate_ns()
            t_uri = name_server.lookup(key)

            try:
                t_peer = Proxy(t_uri)
                t_peer.heartbeat(Peer.name)
            except Exception as e:
                print(f" [*] Error: {e}")


def _init_menu(threads: list[PyThreadKiller]):
    while True:
        options = [
            "Requisitar recurso",
            "Liberar recurso",
            "Status atual",
            "Listar peers ativos",
            None,
            "Sair",
        ]

        terminal_menu = TerminalMenu(options)
        menu_entry_index = terminal_menu.show()
        menu_entry = options[menu_entry_index]

        if menu_entry == "Sair":
            for thread in threads:
                thread.kill()
            break

        if menu_entry == "Requisitar recurso":
            Peer.enter_section()

        if menu_entry == "Liberar recurso":
            Peer.exit_section()

        if menu_entry == "Status atual":
            print(Peer.state)
            continue

        if menu_entry == "Listar peers ativos":
            print(Peer.peer_dict)
            continue


def main():
    daemon, name_server, peer_name = _init_peer()

    Peer.name = peer_name

    peer_request_worker = PyThreadKiller(
        target=_peer_request_worker, args=(daemon,), daemon=True
    )
    peer_request_worker.start()

    peer_heartbeat_worker = PyThreadKiller(
        target=_peer_heartbeat_worker,
    )
    peer_heartbeat_worker.start()

    _init_menu([peer_request_worker, peer_heartbeat_worker])


if __name__ == "__main__":
    main()
