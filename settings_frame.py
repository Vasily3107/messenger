from ui_classes import Tk, ThemeHandler, TkHandler, Label, AdvEntry, Button, Color, Scale, Canvas, Frame, ImageTk, PilImage
from typing     import Callable
from socket     import socket
from sockio     import send, recv
from jsonpickle import (encode as jp_encode,
                        decode as jp_decode)

def init_settings_frame(conn:socket, callback:Callable[[], None]):
    root = Tk()
    root.config(highlightcolor=Color.MAIN, highlightbackground=Color.MAIN, highlightthickness=3)
    root.config(bg=Color.BACK)

    l_main = Label(root, text='Settings',
               fg=Color.BACK, bg=Color.MAIN,
               font=('Unispace', 24))
    l_main.pack(fill='x')
    frame_widgets = [root, l_main]

    send(conn, {'route':'get_profile'})
    res = recv(conn)
    init_login = res['login']
    init_color = res['color']


    # - - - COLOR - - - - - - - - - - - - - - - - - - - - - - - - - - -
    f_change_color = Frame(root, bg=Color.BACK)
    cur_color = None
    def get_color(value) -> str:
        nonlocal cur_color
        r, g, b = __import__('colorsys').hsv_to_rgb(value, .66, 1)
        return (cur_color:='#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255)))
    def on_value_change(value):
        value = float(value)
        c_color.create_rectangle(0,0,359,39, fill=get_color(value))
    s_color = Scale(f_change_color, from_=0, to=1, resolution=0.001, orient='horizontal', showvalue=False,
                    font=('Arial', 16), label='Color slider:', command=on_value_change, length=363,
                    fg=Color.MAIN, bg=Color.BACK, troughcolor=Color.BACK, activebackground=Color.MAIN, highlightthickness=0)
    c_color = Canvas(f_change_color, width=360, height=40, bg=Color.BACK, highlightthickness=0)
    s_color.grid(row=0, column=0)
    c_color.grid(row=1, column=0)
    on_value_change(0)
    def change_color():
        send(conn, {'route':'set_profile', 'color':cur_color})
        recv(conn)
        callback()
        set_msg('Color has been changed', Color.GREEN)
    b_change_color = Button(f_change_color, text='Change color', fg=Color.BACK, bg=Color.MAIN, font=('Arial', 12, 'bold'),
                            width=20, command=change_color)
    b_change_color.grid(row=0, column=1, sticky='ns')
    f_change_color.pack()
    frame_widgets += [f_change_color, s_color, c_color, b_change_color]
    def hex_to_hsv(hex_color:str):
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return __import__('colorsys').rgb_to_hsv(r, g, b)
    s_color.set(hex_to_hsv(init_color)[0])


    # - - - LOGIN - - - - - - - - - - - - - - - - - - - - - - - - - - -
    allowed_chars = set('_0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

    f_change_login = Frame(root, bg=Color.BACK)
    e_login = AdvEntry(f_change_login, 'New login: ...', 0, width=30, font=('Arial', 16), bg=Color.BACK)
    e_login.grid(row=0, column=0)
    def change_login():
        login = e_login.get()
        if not login                      : set_msg("Error: login can't be empty")                                   ; return False
        if len(login) > 30                : set_msg("Error: login can't be longer than 30 characters")               ; return False
        if len(set(login) - allowed_chars): set_msg("Error: login can only contain letters, digits, and underscores"); return False

        send(conn, {'route':'name_availability', 'login':login})
        if recv(conn)['res']:
            set_msg('Error: name is already taken'); return

        with open('config.txt', 'r') as f:
            file_login = (data:=jp_decode(f.read()))['login']
            rember= data['remember']
        send(conn, {'route':'get_profile'})
        res = recv(conn)
        init_login = res['login']
        if rember and file_login == init_login:
            data['login'] = login
        with open('config.txt', 'w') as f:
            f.write(jp_encode(data, indent=2))

        send(conn, {'route':'set_profile', 'login':login})
        recv(conn)
        callback()
        set_msg('Name has been changed', Color.GREEN)
    b_change_login = Button(f_change_login, text='Change login', fg=Color.BACK, bg=Color.MAIN, font=('Arial', 12, 'bold'),
                            width=20, command=change_login)
    b_change_login.grid(row=0, column=1, sticky='ns')
    f_change_login.pack(pady=(30, 0))
    frame_widgets += [f_change_login, e_login, b_change_login]


    # - - - PASSWORD - - - - - - - - - - - - - - - - - - - - - - - - - - -
    f_change_passw = Frame(root, bg=Color.BACK)

    e_old_passw = AdvEntry(f_change_passw, 'Old password: ...', 1, width=30, font=('Arial', 16), bg=Color.BACK)
    e_old_passw.grid(row=0, column=0)

    e_new_passw = AdvEntry(f_change_passw, 'New password: ...', 1, width=30, font=('Arial', 16), bg=Color.BACK)
    e_new_passw.grid(row=1, column=0)

    e_new_confp = AdvEntry(f_change_passw, 'Confirm new password: ...', 1, width=30, font=('Arial', 16), bg=Color.BACK)
    e_new_confp.grid(row=2, column=0)

    def change_passw():
        old_passw = e_old_passw.get()
        new_passw = e_new_passw.get()
        new_confp = e_new_confp.get()

        send(conn, {'route':'get_password'})
        real_passw = recv(conn)['password']

        if old_passw != real_passw            : set_msg("Error: invalid old password")                                     ; return
        if not new_passw                      : set_msg("Error: password can't be empty")                                  ; return
        if len(new_passw) > 30                : set_msg("Error: password can't be longer than 30 characters")              ; return
        if len(set(new_passw) - allowed_chars): set_msg("Error: password can only contain letters, digits, or underscores"); return
        if new_passw != new_confp             : set_msg("Error: passwords don't match")                                    ; return

        with open('config.txt', 'r') as f:
            login = (data:=jp_decode(f.read()))['login']
            rember= data['remember']
        send(conn, {'route':'get_profile'})
        res = recv(conn)
        init_login = res['login']
        if rember and login == init_login:
            data['password'] = new_passw
        with open('config.txt', 'w') as f:
            f.write(jp_encode(data, indent=2))

        send(conn, {'route':'set_profile', 'password':new_passw})
        recv(conn)
        set_msg('Password has been changed', Color.GREEN)
    b_change_passw = Button(f_change_passw, text='Change password', fg=Color.BACK, bg=Color.MAIN, font=('Arial', 12, 'bold'),
                            width=20, command=change_passw)
    b_change_passw.grid(row=0, column=1)
    f_change_passw.pack(pady=(30, 0))
    frame_widgets += [f_change_passw, e_old_passw, e_new_passw, e_new_confp, b_change_passw]


    # - - - MISCELLANEOUS - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def clr_msg() -> None:
        l_info.pack_forget()
        l_info.config(text='')
    def set_msg(msg:str, bg_color:Color = Color.RED) -> None:
        l_info.pack_forget()
        l_info.pack(pady=(30, 0), fill='x')
        l_info.config(text=msg, fg=Color.BACK, bg=bg_color)
    l_info = Label(root, text='', font=('Unispace', 16), wraplength=600, height=2)

    l_close = Label(root, bg=Color.MAIN, cursor='hand2')
    img_close = ImageTk.PhotoImage(PilImage.open('img_close.png').resize((40, 40)), master=root)
    l_close.config(image=img_close)
    l_close.image = img_close
    l_close.place(x=750, y=0)
    def exit_settings():
        callback()
        root.destroy()
    l_close.bind('<Button-1>', lambda _: exit_settings())


    frame_widgets += [l_info, l_close]
    ThemeHandler.add(*frame_widgets)
    frame_widgets.clear()


    def start_move(event):
        root._drag_start_x = event.x
        root._drag_start_y = event.y
    def do_move(event):
        x = root.winfo_x() + event.x - root._drag_start_x
        y = root.winfo_y() + event.y - root._drag_start_y
        root.geometry(f"+{x}+{y}")
    l_main.bind("<ButtonPress-1>", start_move)
    l_main.bind("<B1-Motion>", do_move)

    root.overrideredirect(True)
    root.geometry('800x400')
    root.resizable(False, False)
    root.eval(f'tk::PlaceWindow {root._w} mouse')

    TkHandler.add(root)