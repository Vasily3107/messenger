from pyodbc import connect as connect_to_db
server   = 'localhost\SQLEXPRESS'
database = 'test_db'
dsn      =f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'

from uuid   import UUID, uuid4
from typing import Literal

from shared_classes import Contact, Request, Message

class DBHandler:

    def log_in(login:str, password:str) -> UUID | None:
        con = connect_to_db(dsn)
        cur = con.cursor()

        cur.execute('SELECT id FROM Users WHERE [login] = ? AND [password] = ?',
                    (login, password))
        try   : res = UUID(cur.fetchone()[0])
        except: res = None

        cur.close()
        con.close()
        return res


    def sign_up(login:str, password:str) -> UUID | None:
        con = connect_to_db(dsn)
        cur = con.cursor()

        cur.execute('SELECT id FROM Users WHERE [login] = ?', (login))
        if cur.fetchone():
            cur.close()
            con.close()
            return None

        def rand_color() -> str:
            r, g, b = __import__('colorsys').hsv_to_rgb(__import__('random').random(), .66, 1)
            return '#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255))

        new_user_uuid = uuid4()
        cur.execute('INSERT INTO Users VALUES (?, ?, ?, DEFAULT, DEFAULT, ?)',
                    (new_user_uuid, login, password, rand_color()))
        con.commit()

        cur.close()
        con.close()
        return new_user_uuid


    def name_availability(login:str) -> bool:
        con = connect_to_db(dsn)
        cur = con.cursor()

        cur.execute('SELECT * FROM Users WHERE [login] = ?', (login,))
        res = bool(cur.fetchone())

        cur.close()
        con.close()
        return res


    def select_user(user_uuid:UUID, column:Literal['login', 'password', 'last_seen', 'is_online', 'color']) -> str | bool:
        con = connect_to_db(dsn)
        cur = con.cursor()

        cur.execute(f'SELECT [{column}] FROM Users WHERE id = ?', (user_uuid,))
        res = cur.fetchone()[0]

        if column == 'last_seen': res = str(res).split('.')[0]

        cur.close()
        con.close()
        return res


    def update_user(user_uuid:UUID, column:Literal['login', 'password', 'last_seen', 'is_online', 'color'], value:str|bool = None) -> None:
        con = connect_to_db(dsn)
        cur = con.cursor()

        cur.execute((f'UPDATE Users SET [{column}] = {"?" if (value != None) else "GETDATE()"} '
                     f'WHERE id = ?'), ((value, user_uuid) if (value != None) else (user_uuid,)))
        con.commit()

        cur.close()
        con.close()


    def get_contacts(user_uuid:UUID) -> list[Contact]:
        con = connect_to_db(dsn)
        cur = con.cursor()

        cur.execute('SELECT [friend_id] FROM Contacts WHERE [user_id] = ?', (user_uuid,))
        friend_uuids = list(map(lambda i: i[0], cur.fetchall()))

        res: list[Contact] = []
        for uuid in friend_uuids:
            cur.execute('SELECT [login], last_seen, is_online, color FROM Users WHERE id = ?', (uuid,))
            res.append(Contact(uuid, *cur.fetchone()))

        cur.close()
        con.close()
        return res


    def add_contact(user_uuid:UUID, friend_uuid:UUID) -> None:
        con = connect_to_db(dsn)
        cur = con.cursor()

        cur.executemany('INSERT INTO Contacts VALUES (?, ?)',
                        ((user_uuid, friend_uuid), (friend_uuid, user_uuid)))
        con.commit()

        cur.close()
        con.close()


    def del_contact(user_uuid:UUID, friend_uuid:UUID) -> None:
        con = connect_to_db(dsn)
        cur = con.cursor()

        cur.executemany('DELETE FROM Contacts WHERE [user_id] = ? AND [friend_id] = ?',
                        ((user_uuid, friend_uuid), (friend_uuid, user_uuid)))
        cur.executemany('DELETE FROM [Messages] WHERE [from] = ? AND [to] = ?',
                        ((user_uuid, friend_uuid), (friend_uuid, user_uuid)))
        con.commit()

        cur.close()
        con.close()


    def get_messages(user_uuid:UUID, friend_uuid:UUID) -> list[Message]:
        con = connect_to_db(dsn)
        cur = con.cursor()

        res = []
        cur.execute('SELECT * FROM [Messages] WHERE [from] = ? AND [to] = ?', (user_uuid, friend_uuid))
        res += [Message(*i) for i in cur.fetchall()]
        cur.execute('SELECT * FROM [Messages] WHERE [from] = ? AND [to] = ?', (friend_uuid, user_uuid))
        res += [Message(*i) for i in cur.fetchall()]

        cur.close()
        con.close()
        return res


    def add_message(user_uuid:UUID, friend_uuid:UUID, uuid:UUID, text:str = None, image:bytes = None) -> None:
        con = connect_to_db(dsn)
        cur = con.cursor()

        cur.execute('INSERT INTO [Messages] VALUES (?, ?, ?, ?, ?, GETDATE())',
                    (uuid, user_uuid, friend_uuid, text, image))
        con.commit()

        cur.close()
        con.close()


    def del_message(msg_uuid:UUID) -> None:
        con = connect_to_db(dsn)
        cur = con.cursor()

        cur.execute('DELETE FROM [Messages] WHERE id = ?', (msg_uuid,))
        con.commit()

        cur.close()
        con.close()


    def find_friends(user_uuid:UUID, name:str) -> list[Contact]:
        con = connect_to_db(dsn)
        cur = con.cursor()

        cur.execute('SELECT id, [login], last_seen, is_online, color FROM Users WHERE [login] LIKE ? AND id != ?', (f'%{name}%', user_uuid))
        res = set(Contact(*i) for i in cur.fetchall())

        filler = [None for _ in range(4)]
        cur.execute('SELECT [to] FROM FriendRequests WHERE [from] = ?', (user_uuid,))
        out_req = set(Contact(*i, *filler) for i in cur.fetchall())
        cur.execute('SELECT [from] FROM FriendRequests WHERE [to] = ?', (user_uuid,))
        in_req  = set(Contact(*i, *filler) for i in cur.fetchall())
        cur.execute('SELECT friend_id FROM Contacts WHERE [user_id] = ?', (user_uuid,))
        friends = set(Contact(*i, *filler) for i in cur.fetchall())

        res -= out_req | in_req | friends

        cur.close()
        con.close()
        return list(res)


    @classmethod
    def get_friend_requests(cls, user_uuid:UUID) -> tuple[list[Request], list[Request]]:
        '''first: out, second: in'''
        con = connect_to_db(dsn)
        cur = con.cursor()

        cur.execute('SELECT * FROM FriendRequests WHERE [from] = ?', (user_uuid))
        out_req = [Request(*i) for i in cur.fetchall()]
        cur.execute('SELECT * FROM FriendRequests WHERE [to] = ?'  , (user_uuid))
        in_req  = [Request(*i) for i in cur.fetchall()]

        for i in out_req + in_req:
            name_from = cls.select_user(i.uuid_from, 'login')
            name_to   = cls.select_user(i.uuid_to  , 'login')
            i.name_from = name_from
            i.name_to   = name_to

        cur.close()
        con.close()
        return out_req, in_req


    def add_friend_request(u_from:UUID, u_to:UUID) -> None:
        con = connect_to_db(dsn)
        cur = con.cursor()

        cur.execute('INSERT INTO FriendRequests VALUES (?, ?)',
                    (u_from, u_to))
        con.commit()

        cur.close()
        con.close()


    def del_friend_request(u_from:UUID, u_to:UUID) -> None:
        con = connect_to_db(dsn)
        cur = con.cursor()

        cur.execute('DELETE FROM FriendRequests WHERE [from] = ? AND [to] = ?',
                    (u_from, u_to))
        con.commit()

        cur.close()
        con.close()


    def on_server_wake_up() -> None:
        con = connect_to_db(dsn)
        cur = con.cursor()

        cur.execute('UPDATE Users SET is_online = 0')
        con.commit()

        cur.close()
        con.close()