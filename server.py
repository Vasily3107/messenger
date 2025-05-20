from socket    import socket, AF_INET, SOCK_STREAM
from sockio    import send, recv
from threading import Thread
from uuid      import UUID, uuid4

from colorama  import init as colorama_init, Fore, Back, Style
colorama_init(autoreset=True)

from db_handler     import DBHandler
from shared_classes import Contact


IP = "127.0.0.1"
PORT = 12345
CLIENTS_LIMIT = 1024

server = socket(AF_INET, SOCK_STREAM)
server.bind((IP, PORT))
server.listen(CLIENTS_LIMIT)

class Client:
    def __init__(self, thread_uuid:UUID, conn_help:socket):
        self.thread_uuid = thread_uuid
        self.client_uuid = None
        self.name        = None
        self.conn_help   = conn_help

    def set_uuid(self, uuid:UUID|None) -> None:
        self.client_uuid = uuid
        if uuid: self.name = DBHandler.select_user(uuid, 'login')
        else   : self.name = None

    def __repr__(self):
        return f'{self.name}'

    def __hash__(self):
        if self.client_uuid:
            return hash(self.client_uuid)
        return hash(self.thread_uuid)

clients: list[Client] = []
waiting: bool = False

def print_clients() -> None:
    global clients
    from time import sleep
    list_snapshot = frozenset(clients)
    while True:
        sleep(1)
        if frozenset(clients) != list_snapshot:
            if not len(clients):
                print(Back.WHITE + Fore.BLACK + 'Clients:')
                print('no active clients...\n')
                list_snapshot = frozenset(clients)
            else:    
                print(Back.WHITE + Fore.BLACK + 'Clients:')
                offset = len(str(len(clients)))
                for i, c in enumerate(clients):
                    print(f'{i:{offset}}: {c}')
                print()
                list_snapshot = frozenset(clients)
Thread(target=print_clients, daemon=True).start()

DBHandler.on_server_wake_up()


def client_logic(thread_uuid:UUID, conn_main:socket, conn_help:socket) -> None:
    global clients

    client_uuid: UUID | None = None

    def print_error(error:Exception) -> None:
        print(Back.RED + Fore.WHITE + Style.BRIGHT + f'CLIENT ERROR: {error.__str__()}')
        for i in __import__('traceback').extract_tb(error.__traceback__):
            file = i.filename.split('\\')[-1]
            print(Fore.RED + Style.BRIGHT + f'line: {i.lineno} file: {file} path: {i.filename}')

    def update_client_uuid(uuid:UUID|None) -> None:
        nonlocal client_uuid
        client_uuid = uuid
        next(i for i in clients
             if i.thread_uuid == thread_uuid
             ).set_uuid(client_uuid)

    def send_update_to_friends(route:str, friend_uuid:UUID = None) -> None:
        if route == 'chat':
          if friend_thread := next((i for i in clients if i.client_uuid == friend_uuid), None):
            res = DBHandler.get_messages(friend_uuid, client_uuid)
            send(friend_thread.conn_help, {'route':route, 'res':res, 'from':client_uuid})

        elif route == 'list' and not friend_uuid:
          for friend in DBHandler.get_contacts(client_uuid):
            if friend_thread := next((i for i in clients if i.client_uuid == friend.uuid), None):
              send(friend_thread.conn_help, {'route':route, 'list':DBHandler.get_contacts(friend.uuid)})

        elif route == 'list':
          if friend_thread := next((i for i in clients if i.client_uuid == friend_uuid), None):
            send(friend_thread.conn_help, {'route':route, 'list':DBHandler.get_contacts(friend_uuid)})

        elif route == 'requests':
          if friend_thread := next((i for i in clients if i.client_uuid == friend_uuid), None):
            out, in_ = DBHandler.get_friend_requests(friend_uuid)
            send(friend_thread.conn_help, {'route':route, 'out':out, 'in':in_})

    try:
     while True:

       match (req := recv(conn_main))['route']:

        # AUTHORIZATION ROUTES
        case 'log_in':
            login = req['login']
            passw = req['password']

            if res := DBHandler.log_in(login, passw):
                if client_uuid: DBHandler.update_user(client_uuid, 'is_online', False)
                update_client_uuid(res)
                DBHandler.update_user(client_uuid, 'is_online', True)
                send_update_to_friends('list')

            send(conn_main, {'res':bool(res)})

        case 'log_out':
            if len([i for i in clients if i.client_uuid == client_uuid]) == 1:
                DBHandler.update_user(client_uuid, 'is_online', False)
                send_update_to_friends('list')
            update_client_uuid(None)

        case 'sign_up':
            login = req['login']
            passw = req['password']

            if res := DBHandler.sign_up(login, passw):
                if client_uuid: DBHandler.update_user(client_uuid, 'is_online', False)
                update_client_uuid(res)

            send(conn_main, {'res':bool(res)})


        # CONTACT ROUTES
        case 'get_contacts':
            res = DBHandler.get_contacts(client_uuid)
            send(conn_main, {'res':res})

        case 'del_contact':
            friend_uuid = req['friend_uuid']
            DBHandler.del_contact(client_uuid, friend_uuid)
            send_update_to_friends('list', friend_uuid)


        # MESSAGE ROUTES
        case 'get_messages':
            friend_uuid = req['friend_uuid']
            res = DBHandler.get_messages(client_uuid, friend_uuid)
            send(conn_main, {'res':res})

        case 'send_message':
            friend_uuid = req['friend_uuid']
            text = req['text']
            image = req['image']
            uuid = req['uuid']
            DBHandler.add_message(client_uuid, friend_uuid, uuid, text, image)
            send_update_to_friends('chat', friend_uuid)

        case 'del_message':
            friend_uuid = req['friend_uuid']
            msg_uuid = req['msg_uuid']
            DBHandler.del_message(msg_uuid)
            send_update_to_friends('chat', friend_uuid)


        # FRIEND REQUESTS ROUTES
        case 'find_friends':
            name = req['name']
            res = DBHandler.find_friends(client_uuid, name)
            send(conn_main, {'res':res})

        case 'get_friend_requests':
            out, in_ = DBHandler.get_friend_requests(client_uuid)
            send(conn_main, {'out':out, 'in':in_})

        case 'send_friend_request':
            friend_uuid = req['friend_uuid']
            DBHandler.add_friend_request(client_uuid, friend_uuid)
            send_update_to_friends('requests', friend_uuid)

        case 'cancel_friend_request':
            friend_uuid = req['friend_uuid']
            DBHandler.del_friend_request(client_uuid, friend_uuid)
            send_update_to_friends('requests', friend_uuid)

        case 'accept_friend_request':
            friend_uuid = req['friend_uuid']
            DBHandler.del_friend_request(friend_uuid, client_uuid)
            DBHandler.add_contact(client_uuid, friend_uuid)
            send_update_to_friends('requests', friend_uuid)
            send_update_to_friends('list', friend_uuid)

        case 'reject_friend_request':
            friend_uuid = req['friend_uuid']
            DBHandler.del_friend_request(friend_uuid, client_uuid)
            send_update_to_friends('requests', friend_uuid)


        # PROFILE ROUTES
        case 'get_profile':
            login = DBHandler.select_user(client_uuid, 'login')
            color = DBHandler.select_user(client_uuid, 'color')
            send(conn_main, {'login':login, 'color':color})

        case 'set_profile':
            visual_change = False
            try   : DBHandler.update_user(client_uuid, 'login'   , req['login']   ); visual_change = True
            except: ...
            try   : DBHandler.update_user(client_uuid, 'password', req['password'])
            except: ...
            try   : DBHandler.update_user(client_uuid, 'color'   , req['color']   ); visual_change = True
            except: ...
            send(conn_main, {'res':204})
            if visual_change: send_update_to_friends('list')


        # HELPER ROUTES
        case 'name_availability':
            login = req['login']
            res = DBHandler.name_availability(login)
            send(conn_main, {'res':res})

        case 'get_password':
            send(conn_main, {'password':DBHandler.select_user(client_uuid, 'password')})


        case 'end': break
        case _: print(f"{Back.YELLOW+Style.BRIGHT}ROUTE MISS: {req['route']=}"); raise Exception('route error: default case')

    except ConnectionResetError: ...
    except Exception as error: print_error(error)
        
    if client_uuid and len([i for i in clients if i.client_uuid == client_uuid]) == 1:
        DBHandler.update_user(client_uuid, 'is_online', False)
        send_update_to_friends('list')
    conn_main.close()
    thread_end(thread_uuid)


def thread_end(thread_uuid:UUID) -> None:
    global clients, waiting
    
    clients.remove(
        next(i for i in clients
             if i.thread_uuid == thread_uuid)
    )

    if not waiting: new_thread()


def new_thread() -> None:
    global clients, waiting

    waiting = True
    conn_main = server.accept()[0]
    conn_help = server.accept()[0]
    waiting = False

    thread_uuid = uuid4()

    Thread(target = client_logic,
           args   = (thread_uuid, conn_main, conn_help),
           daemon = True).start()
    clients.append(Client(thread_uuid, conn_help))

    if len(clients) < CLIENTS_LIMIT:
        new_thread()


new_thread()