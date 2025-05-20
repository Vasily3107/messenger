from ui_classes import ThemeHandler, Notebook, Frame, Label, Button, Checkbox, AdvEntry, Color

from socket import socket
from sockio import send, recv

from jsonpickle import (encode as jp_encode,
                        decode as jp_decode)

from collections.abc import Callable

def init_sign_up_frame(conn:socket, tab_switch:Notebook, callback: Callable[[], None]):
    if 'sign_up_frame' in ''.join(tab_switch.tabs()): return

    f_main = Frame(tab_switch, name='sign_up_frame', bg=Color.BACK)

    l_main = Label(f_main, text='Signing up:',
                   fg=Color.BACK, bg=Color.MAIN,
                   font=('Unispace', 24))
    l_main.pack(pady=(10, 0), fill='x')

    e_login = AdvEntry(f_main, 'Login: ...', 0, width=30, font=('Arial', 16), bg=Color.BACK)
    e_login.pack(pady=(30, 0))

    e_passw = AdvEntry(f_main, 'Password: ...', 1, width=30, font=('Arial', 16), bg=Color.BACK)
    e_passw.pack(pady=(10, 0))

    e_confp = AdvEntry(f_main, 'Confirm password: ...', 1, width=30, font=('Arial', 16), bg=Color.BACK)
    e_confp.pack(pady=(10, 0))

    allowed_chars = set('_0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    def is_valid_input() -> bool:
        login = e_login.get()
        passw = e_passw.get()
        confp = e_confp.get()
        if not login                      : set_msg("Error: login can't be empty")                                      ; return False
        if not passw                      : set_msg("Error: password can't be empty")                                   ; return False
        if len(login) > 30                : set_msg("Error: login can't be longer than 30 characters")                  ; return False
        if len(passw) > 30                : set_msg("Error: password can't be longer than 30 characters")               ; return False
        if len(set(login) - allowed_chars): set_msg("Error: login can only contain letters, digits, or underscores")    ; return False
        if len(set(passw) - allowed_chars): set_msg("Error: password can only contain letters, digits, and underscores"); return False
        if passw != confp                 : set_msg("Error: passwords don't match")                                     ; return False
        return True

    def send_sign_up_request() -> None:
        clr_msg()

        if not is_valid_input(): return

        login = e_login.get()
        passw = e_passw.get()
        
        send(conn, {'route':'sign_up', 'login':login, 'password':passw})

        res = recv(conn)['res']

        if not res:
            set_msg(f'Error: name "{login}" is already taken')
            return

        with open('config.txt', 'r') as f:
            data = jp_decode(f.read())
        if remember_me:
            data['login'] = login
            data['password'] = passw
            data['remember'] = True
        else:
            if not data['login'] and not data['password']:
                data['remember'] = False
        with open('config.txt', 'w') as f:
            f.write(jp_encode(data, indent=2))

        set_msg(f'Logged in as {login}', Color.GREEN)
        callback()
    b_sign_up = Button(f_main, text='Sign up', width=30, font=('Unispace', 14), fg=Color.MAIN, bg=Color.BACK,
                       command=send_sign_up_request)
    b_sign_up.pack(pady=(30, 0))

    remember_me = False
    def toggle_remember_me():
        nonlocal remember_me
        remember_me = not remember_me
        cb_rember_me.configure(hover_color=(Color.MAIN if remember_me else Color.BACK))
    cb_rember_me = Checkbox(f_main, command=toggle_remember_me, text='Remember me', font=('Arial', 20, 'bold'),
                            fg_color=Color.MAIN, bg_color=Color.BACK, text_color=Color.MAIN,
                            hover_color=Color.BACK, checkmark_color=Color.BACK, border_color=Color.MAIN)
    cb_rember_me.pack(pady=(10, 0))

    def clr_msg() -> None:
        l_info.pack_forget()
        l_info.config(text='')
    def set_msg(msg:str, bg_color:Color = Color.RED) -> None:
        l_info.pack_forget()
        l_info.pack(pady=(15, 0), fill='x')
        l_info.config(text=msg, fg=Color.BACK, bg=bg_color)
    l_info = Label(f_main, text='', font=('Unispace', 16), wraplength=600)

    def __key_trigger_sign_up_req(e):
        if e.keycode == 13: send_sign_up_request()
    def __key_trigger_on_e_login(e):
        if   e.keycode == 38: e_confp.focus_set()
        elif e.keycode == 40: e_passw.focus_set()
    def __key_trigger_on_e_passw(e):
        if   e.keycode == 38: e_login.focus_set()
        elif e.keycode == 40: e_confp.focus_set()
    def __key_trigger_on_e_confp(e):
        if   e.keycode == 38: e_passw.focus_set()
        elif e.keycode == 40: e_login.focus_set()

    e_login.bind('<Key>', __key_trigger_sign_up_req, 1)
    e_passw.bind('<Key>', __key_trigger_sign_up_req, 1)
    e_confp.bind('<Key>', __key_trigger_sign_up_req, 1)
    e_login.bind('<Key>', __key_trigger_on_e_login, 1)
    e_passw.bind('<Key>', __key_trigger_on_e_passw, 1)
    e_confp.bind('<Key>', __key_trigger_on_e_confp, 1)

    if 'sign_up_frame' not in ''.join(tab_switch.tabs()):
        tab_switch.add(f_main, text='Sign up')

    ThemeHandler.add(f_main, l_main, e_login, e_passw, e_confp, b_sign_up, l_info, cb_rember_me)