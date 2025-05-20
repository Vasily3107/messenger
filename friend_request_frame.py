from ui_classes         import ThemeHandler, Label, Button, Notebook, Frame, Listbox, AdvEntry, Color
from tkinter.messagebox import showerror
from idlelib.tooltip    import Hovertip

from socket import socket
from sockio import send, recv

from jsonpickle import(encode as jp_encode,
                       decode as jp_decode)

from shared_classes import Contact, Request

from typing import Callable

def init_friend_request_frame(conn_main:socket, tab_switch:Notebook, update_list_callback:Callable[[list[Contact]], None]) -> Callable[[list[Request], list[Request]], None]:
    if 'friend_request_frame' in ''.join(tab_switch.tabs()): return

    f_main = Frame(tab_switch, name='friend_request_frame', bg=Color.BACK)

    l_main = Label(f_main, text='Friend requests',
                   fg=Color.BACK, bg=Color.MAIN,
                   font=('Unispace', 24))
    l_main.pack(pady=(10, 0), fill='x')

    f_sub = Frame(f_main, bg=Color.BACK)
    f_sub.pack(fill='both', expand=True)

    frame_widgets = [f_main, l_main, f_sub]


    # - - - FIND FRIENDS - - - - - - - - - - - - - - - - - - - - - - - - - - -
    f_find = Frame(f_sub, bg=Color.BACK)

    f_find_buttons = Frame(f_find, bg=Color.BACK)
    allowed_chars = set('_0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    found_friends: list[Contact] = []

    def find_friends():
        name = e_find.get()

        if len(name) > 30                : showerror('Name input error', 'Names can not be longer than 30 characters')
        if len(set(name) - allowed_chars): showerror('Name input error', 'Names can only contain letters, digits, and underscores')

        send(conn_main, {'route':'find_friends', 'name':name})
        nonlocal found_friends
        found_friends = recv(conn_main)['res']

        lb_find.config(state='normal')
        lb_find.delete(0, 'end')
        if not len(found_friends):
            lb_find.insert('end', 'Nothing was found...')
            lb_find.config(state='disabled')
            return
        for i in found_friends:
            lb_find.insert('end', i.name)

    b_find = Button(f_find_buttons, text='Find', width=1, font=('Unispace', 14), fg=Color.BACK, bg=Color.MAIN, command=find_friends)
    b_find.pack(side='left', fill='x', expand=True)

    def send_request():
        try   : index = lb_find.curselection()[0]
        except: return
        nonlocal found_friends

        friend: Contact = found_friends.pop(index)
        send(conn_main, {'route':'send_friend_request', 'friend_uuid':friend.uuid})

        lb_find.delete(index)

        nonlocal out_req
        out_req.append(Request(friend.uuid, friend.uuid, None, friend.name))
        lb_out.insert('end', friend.name)

    b_send = Button(f_find_buttons, text='Send', width=1, font=('Unispace', 14), fg=Color.BACK, bg=Color.MAIN, command=send_request)
    b_send.pack(side='left', fill='x', expand=True)
    f_find_buttons.pack(fill='x')

    e_find = AdvEntry(f_find, 'Name: ...', 0, width=1, font=('Arial', 16), bg=Color.BACK)
    e_find.pack(fill='x')
    Hovertip(e_find, 'Leave this entry empty to get all users', 0)

    lb_find = Listbox(f_find, font=('Arial', 16), exportselection=False, selectmode='single', width=1, highlightthickness=0,
                      bg=Color.BACK, fg=Color.MAIN, selectbackground=Color.MAIN, selectforeground=Color.BACK)
    lb_find.pack(fill='both', expand=True)

    f_find.pack(side='left', fill='both', expand=True)
    frame_widgets += [f_find, b_find, b_send, e_find, lb_find]


    # - - - OUT FRIEND REQUESTS - - - - - - - - - - - - - - - - - - - - - - - - - - -
    f_out_req = Frame(f_sub, bg=Color.BACK)
    out_req: list[Request] = []

    def cancel_request():
        try   : index = lb_out.curselection()[0]
        except: return
        nonlocal out_req
        friend: Request = out_req.pop(index)
        send(conn_main, {'route':'cancel_friend_request', 'friend_uuid':friend.uuid_to})
        lb_out.delete(index)

    b_cancel = Button(f_out_req, text='Cancel request', width=1, font=('Unispace', 14), fg=Color.BACK, bg=Color.RED, command=cancel_request)
    b_cancel.pack(fill='x')

    lb_out = Listbox(f_out_req, font=('Arial', 16), exportselection=False, selectmode='single', width=1, highlightthickness=0,
                    bg=Color.BACK, fg=Color.MAIN, selectbackground=Color.MAIN, selectforeground=Color.BACK)
    lb_out.pack(fill='both', expand=True)

    f_out_req.pack(side='left', fill='both', expand=True)
    frame_widgets += [f_out_req, b_cancel, lb_out]


    # - - - OUT FRIEND REQUESTS - - - - - - - - - - - - - - - - - - - - - - - - - - -
    f_in_req = Frame(f_sub, bg=Color.BACK)
    in_req: list[Request] = []
    f_in_buttons = Frame(f_in_req, bg=Color.BACK)

    def accept_request():
        try   : index = lb_in.curselection()[0]
        except: return
        nonlocal in_req
        friend: Request = in_req.pop(index)
        send(conn_main, {'route':'accept_friend_request', 'friend_uuid':friend.uuid_from})
        lb_in.delete(index)

        send(conn_main, {'route':'get_contacts'})
        update_list_callback(recv(conn_main)['res'])

    b_accept = Button(f_in_buttons, text='Accept', width=1, font=('Unispace', 14), fg=Color.BACK, bg=Color.GREEN, command=accept_request)
    b_accept.pack(side='left', fill='x', expand=True)

    def reject_request():
        try   : index = lb_in.curselection()[0]
        except: return
        nonlocal in_req
        friend: Request = in_req.pop(index)
        send(conn_main, {'route':'reject_friend_request', 'friend_uuid':friend.uuid_from})
        lb_in.delete(index)

    b_reject = Button(f_in_buttons, text='Reject', width=1, font=('Unispace', 14), fg=Color.BACK, bg=Color.RED, command=reject_request)
    b_reject.pack(side='left', fill='x', expand=True)
    f_in_buttons.pack(fill='x')

    lb_in = Listbox(f_in_req, font=('Arial', 16), exportselection=False, selectmode='single', width=1, highlightthickness=0,
                    bg=Color.BACK, fg=Color.MAIN, selectbackground=Color.MAIN, selectforeground=Color.BACK)
    lb_in.pack(fill='both', expand=True)

    f_in_req.pack(side='left', fill='both', expand=True)
    frame_widgets += [f_in_req, f_in_buttons, b_accept, b_reject, lb_in]


    send(conn_main, {'route':'get_friend_requests'})
    res = recv(conn_main)
    out_req = res['out']
    in_req  = res['in' ]
    lb_out.delete(0, 'end')
    for i in out_req: lb_out.insert('end', i.name_to  )
    lb_in .delete(0, 'end')
    for i in in_req : lb_in .insert('end', i.name_from)


    def requests_update_callback(out:list[Request], in_:list[Request]):
        nonlocal out_req, in_req
        out_req, in_req = out, in_

        lb_out.delete(0, 'end')
        for i in out: lb_out.insert('end', i.name_to  )
        lb_in .delete(0, 'end')
        for i in in_: lb_in .insert('end', i.name_from)

        names = [i.name_to for i in out]+[i.name_from for i in in_]
        for i, name in enumerate(lb_find.get(0, 'end')):
            if name in names: lb_find.delete(i)


    tab_switch.add(f_main, text='Friend requests')

    ThemeHandler.add(*frame_widgets)
    frame_widgets.clear()

    return requests_update_callback