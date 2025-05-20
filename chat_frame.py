from ui_classes  import ThemeHandler, TkHandler, Label, Button, AdvEntry, Notebook, Frame, Color, Scrollframe, Canvas, PilImage, ImageTk, Scrollbar, Menu
from tkinterdnd2 import DND_FILES
from io          import BytesIO

from socket    import socket, timeout
from sockio    import send, recv
from threading import Thread
from uuid      import UUID, uuid4

from shared_classes import Contact, Message

from log_in_frame         import init_log_in_frame
from sign_up_frame        import init_sign_up_frame
from settings_frame       import init_settings_frame
from friend_request_frame import init_friend_request_frame

from typing import Callable
def init_chat_frame(conn_main:socket, conn_help:socket, tab_switch:Notebook, callback:Callable[[], None]):
    if 'chat_frame' in ''.join(tab_switch.tabs()): return

    f_main = Frame(tab_switch, name='chat_frame', bg=Color.BACK)
    f_sub = Frame(f_main, bg=Color.BACK)
    stop_help_thread: bool = False
    frame_widgets = [f_main, f_sub]


    # - - - UPPER FRAME - - - - - - - - - - - - - - - - - - - - - - - - - - -
    f_upper = Frame(f_main, bg=Color.MAIN)

    l_main = Label(f_upper, text='Chatting',
                   fg=Color.BACK, bg=Color.MAIN,
                   font=('Unispace', 24))

    def log_out() -> None:
        nonlocal stop_help_thread
        stop_help_thread = True
        TkHandler.close_all()
        for i in tab_switch.tabs()[1:]:
            tab_switch.forget(i)
        init_log_in_frame(conn_main, tab_switch, callback)
        init_sign_up_frame(conn_main, tab_switch, callback)
        send(conn_main, {'route':'log_out'})

    c_profile = Canvas(f_upper, bg=Color.MAIN, width=300, height=40, highlightthickness=0)
    def update_profile():
        send(conn_main, {'route':'get_profile'})
        res = recv(conn_main)
        login = res['login']
        color = res['color']
        c_profile.delete('all')
        c_profile.create_oval(5,2,41,38, fill=color, outline='#0F0F0F')
        c_profile.create_oval(28,25,41,38, fill=Color.GREEN, outline='#0F0F0F')
        c_profile.create_text(50,2, text=login, fill='#FFFFFF', font=('Arial', 12, 'bold'), anchor='nw', width=250)
    update_profile()

    f_upper_buttons = Frame(f_upper, height=42, width=300, bg=Color.MAIN)
    f_upper_buttons.pack_propagate(False)

    l_log_out = Label(f_upper_buttons, bg=Color.MAIN, cursor='hand2')
    img_log_out = ImageTk.PhotoImage(PilImage.open('img_log_out.png').resize((40, 40)))
    l_log_out.config(image=img_log_out)
    l_log_out.image = img_log_out
    l_log_out.pack(side='right', padx=(0, 20))

    l_settings = Label(f_upper_buttons, bg=Color.MAIN, cursor='hand2')
    img_setting = ImageTk.PhotoImage(PilImage.open('img_wrench.png').resize((40, 40)))
    l_settings.config(image=img_setting)
    l_settings.image = img_setting
    l_settings.pack(side='right', padx=(0, 10))

    l_log_out.bind('<Button-1>', lambda _: log_out())

    settings_open = False
    def settings_callback():
        nonlocal settings_open
        settings_open = False
        update_profile()
    def open_settings():
        nonlocal settings_open
        if settings_open: return
        settings_open = True
        init_settings_frame(conn_main, settings_callback)

    l_settings.bind('<Button-1>', lambda _: open_settings())

    c_profile.pack(side='left')
    l_main.pack(fill='x', side='left', expand=True)
    f_upper_buttons.pack(side='left')

    f_upper.pack(fill='x', pady=(10, 0))
    frame_widgets += [f_upper, l_main, c_profile, f_upper_buttons, l_settings, l_log_out]
    f_sub.pack(fill='both', expand=True)


    # - - - LIST FRAME - - - - - - - - - - - - - - - - - - - - - - - - - - -
    f_list = Scrollframe(f_sub, width=250, fg_color=Color.BACK, scrollbar_button_color=Color.MAIN, scrollbar_button_hover_color=Color.MAIN)
    f_list.pack(fill='y', side='left')

    selected_contact: Contact = None

    def update_list(l:list[Contact]) -> None:
        for widget in f_list.winfo_children():
            widget.destroy()

        def on_contact_click(c:Contact):
            nonlocal selected_contact
            selected_contact = c

            if not f_chat_main.winfo_manager():
                f_chat_main.pack(fill='both', side='left', expand=True)

            update_chat_up(c.color, c.name, c.is_online, c.last_seen)
            update_chat(c)

        for i in l:
            f_contact = Frame(f_list, bg=Color.BACK, cursor='hand2')

            c_color = Canvas(f_contact, bg=Color.BACK, width=40, height=40, highlightthickness=0)
            c_color.create_oval(1,1,39,39, fill=i.color)
            c_color.pack(side='left', fill='y', pady=(3,0))

            f_sub = Frame(f_contact, bg=Color.BACK)
            l_name = Label(f_sub, text=i.name, fg=Color.FORE, bg=Color.BACK, font=('Arial', 12, 'bold'), justify='left')
            l_name.grid(row=0, column=0, columnspan=2, sticky='ws')

            c_is_online = Canvas(f_sub, bg=Color.BACK, width=50, height=20, highlightthickness=0)
            c_is_online.create_oval(2,5,12,15, fill=(Color.GREEN if i.is_online else Color.RED))
            c_is_online.create_text(16,4, anchor='nw', text=('Online' if i.is_online else 'Offline'),
                                    fill=(Color.GREEN if i.is_online else Color.RED), font=('Unispace', 10))
            c_is_online.grid(row=1, column=0, sticky='nesw')

            l_last_seen = Label(f_sub, text=i.last_seen, fg=Color.FORE, bg=Color.BACK, font=('Arial', 10, 'bold'))
            if not i.is_online: l_last_seen.place(x=80, y=25, anchor='nw')
            f_sub.columnconfigure(0, minsize=80)
            f_sub.pack(side='left', fill='x', expand=True)

            f_contact.pack(fill='x')

            f_contact.bind('<Enter>', lambda _, i_=i: f_contact.bind_all('<Button-1>', lambda _: on_contact_click(i_)))
            f_contact.bind('<Leave>', lambda _: f_contact.unbind_all('<Button-1>'))

            f_split_contact = Frame(f_list, bg=Color.MAIN, height=3)
            f_split_contact.pack(fill='x', pady=(3, 0))

            if selected_contact and i == selected_contact: update_chat_up(i.color, i.name, i.is_online, i.last_seen)

            ThemeHandler.add(f_contact, c_color, f_sub, l_name, c_is_online, l_last_seen, f_split_contact)

    send(conn_main, {'route':'get_contacts'})
    update_list(recv(conn_main)['res'])

    def f_list_scrollbar_command(*args):
        if 'scroll' in args: return
        f_list._parent_canvas.yview(*args)
    f_list._scrollbar.configure(command=f_list_scrollbar_command, cursor='sb_v_double_arrow')

    (f_split := Frame(f_sub, width=3, bg=Color.MAIN)).pack(fill='y', side='left')
    frame_widgets += [f_list, f_split]


    # - - - CHAT FRAME - - - - - - - - - - - - - - - - - - - - - - - - - - -
    f_chat_main = Frame(f_sub, bg=Color.BACK, height=40)

    f_chat_up = Frame(f_chat_main, bg=Color.BACK)
    c_color = Canvas(f_chat_up, bg=Color.BACK, width=40, height=40, highlightthickness=0)
    f_chat_up_sub = Frame(f_chat_up, bg=Color.BACK)
    l_name = Label(f_chat_up_sub, text='', bg=Color.BACK, fg=Color.FORE, font=('Consolas', 16, 'bold'), justify='left', anchor='nw')
    c_is_online = Canvas(f_chat_up_sub, bg=Color.BACK, width=80, height=16, highlightthickness=0)
    l_last_seen = Label(f_chat_up_sub, text='', bg=Color.BACK, fg=Color.FORE, font=('Arial', 12, 'bold'), justify='left')
    f_chat_up_split = Frame(f_chat_main, bg=Color.MAIN, height=3)

    c_color.pack(side='left', pady=(5, 0))
    f_chat_up_sub.pack(side='left', fill='x', expand=True)
    l_name.grid(row=0, column=0, columnspan=2, sticky='we')
    c_is_online.grid(row=1, column=0, sticky='we')
    l_last_seen.place(x=80, y=28)

    def unfriend():
        if (not selected_contact or
            not __import__('tkinter.messagebox', fromlist=[...]).askyesno('', f'Are you sure you want to unfriend "{selected_contact.name}"')): return
        send(conn_main, {'route':'del_contact', 'friend_uuid':selected_contact.uuid})
        send(conn_main, {'route':'get_contacts'})
        update_list(recv(conn_main)['res'])
        f_chat_main.pack_forget()
        for widget in f_chat.winfo_children():
            widget.destroy()

    l_unfriend = Label(f_chat_up, bg=Color.BACK, cursor='hand2')
    img_unfriend = ImageTk.PhotoImage(PilImage.open('img_unfriend.png').resize((40, 40)))
    l_unfriend.config(image=img_unfriend)
    l_unfriend.image = img_unfriend
    l_unfriend.pack(side='right', padx=(0, 10), pady=(3, 0))

    l_unfriend.bind('<Button-1>', lambda _: unfriend())

    def update_chat_up(color:str, name:str, is_online:bool, last_seen:str) -> None:
        c_color.delete('all')
        c_color.create_oval(2,2,39,39, fill=color, outline='#0F0F0F')
        l_name.config(text=name)
        c_is_online.delete('all')
        c_is_online.create_oval(3,3,15,15, fill=(Color.GREEN if is_online else Color.RED))
        c_is_online.create_text(20,4, anchor='nw', text=('Online' if is_online else 'Offline'), font=('Unispace', 10),
                                fill=(Color.GREEN if is_online else Color.RED))
        l_last_seen.config(text=('' if is_online else last_seen))

    f_chat_up.pack(fill='x')
    f_chat_up_split.pack(fill='x', pady=(6, 0))

    f_chat_sub = Frame(f_chat_main, bg=Color.BACK)
    f_chat = Scrollframe(f_chat_sub, fg_color=Color.BACK, scrollbar_button_color=Color.MAIN, scrollbar_button_hover_color=Color.MAIN)
    f_chat._scrollbar.grid_forget()
    f_chat.pack(side='left', fill='both', expand=True)


    msg_menu = Menu(f_chat_main, tearoff=False, bg=Color.BACK, fg=Color.FORE, activebackground=Color.MAIN, activeforeground=Color.FORE)
    def msg_menu_appear(event, msg_type:str, msg:Message) -> None:
        msg_menu.delete(0, 'end')

        def copy_text():
            f_chat.clipboard_clear()
            f_chat.clipboard_append(msg.text)

        def download_img():
            from tkinter.filedialog import askdirectory
            from os.path import join, exists

            path = askdirectory(title='Select install location:')
            if not path: return

            img_bin = msg.image
            img = PilImage.open(BytesIO(img_bin))
            img_ext = (img.format or 'png').lower()

            def get_unique_filename(path, base, ext):
                filename = f"{base}.{ext}"
                counter = 1
                while exists(join(path, filename)):
                    filename = f"{base}-{counter}.{ext}"
                    counter += 1
                return filename

            with open(join(path, get_unique_filename(path, "img", img_ext)), 'wb') as f:
                f.write(img_bin)

        def del_msg():
            send(conn_main, {'route':'del_message', 'friend_uuid':selected_contact.uuid, 'msg_uuid':msg.uuid})
            update_chat(selected_contact)

        match msg_type:
            case 'txt_left':
                msg_menu.add_command(label='Copy text', command=copy_text)

            case 'txt_right':
                msg_menu.add_command(label='Copy text', command=copy_text)
                msg_menu.add_command(label='Delete message', command=del_msg)

            case 'img_left':
                msg_menu.add_command(label='Download image', command=download_img)

            case 'img_right':
                msg_menu.add_command(label='Download image', command=download_img)
                msg_menu.add_command(label='Delete message', command=del_msg)

        msg_menu.tk_popup(event.x_root, event.y_root)

    def update_chat_view():
        f_chat._parent_canvas.update()
        f_chat._parent_canvas.yview_moveto(0.0)
        f_chat._parent_canvas.update()
        f_chat._parent_canvas.yview_moveto(1.0)
        f_chat._parent_canvas.update()

    def update_chat(c:Contact|UUID|list[Message]) -> None:
        if type(c) in [Contact, UUID]:
            send(conn_main, {'route':'get_messages', 'friend_uuid':(c.uuid if type(c) == Contact else c)})
            messages: list[Message] = recv(conn_main)['res']
        else:
            messages: list[Message] = c

        for widget in f_chat.winfo_children():
            widget.destroy()

        messages.sort(key = lambda i: i.date)

        for i in messages:
            
            f_msg = Frame(f_chat, bg=Color.BACK)
            l_msg = Label(f_msg)

            left: bool = i.uuid_from == selected_contact.uuid

            if i.text:
                l_msg.config(text=i.text, bg=Color.MAIN, fg=Color.BACK, font=('Arial', 12, 'bold'), wraplength=300)
                l_msg.bind('<Button-3>', lambda e, l=left, i_=i: msg_menu_appear(e, ('txt_left' if l else 'txt_right'), i_))
            else:
                img = PilImage.open(BytesIO(i.image))
                x, y = img.size
                resize = max(img.size)/300
                img = ImageTk.PhotoImage(img.resize((int(x/resize), int(y/resize))))
                l_msg.config(image=img, text='', bg=Color.BACK)
                l_msg.image = img
                l_msg.bind('<Button-3>', lambda e, l=left, i_=i: msg_menu_appear(e, ('img_left' if l else 'img_right'), i_))

            l_msg.pack(side=('left' if left else 'right'))
            f_msg.pack(fill='x')

            ThemeHandler.add(f_msg, l_msg)

        update_chat_view()
            
    sb_chat = Scrollbar(f_chat_sub, command=f_chat._parent_canvas.yview, cursor='sb_v_double_arrow',
                        button_color=Color.MAIN, button_hover_color=Color.MAIN)
    f_chat._parent_canvas.config(yscrollcommand=sb_chat.set)
    sb_chat.pack(side='left', fill='y')
    f_chat_sub.pack(fill='both', expand=True)
    
    e_msg = AdvEntry(f_chat_main, 'Message: ...', 0, font=('Arial', 16), bg=Color.BACK)
    e_msg.pack(fill='x')
    
    ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'tif', 'ppm', 'pgm', 'pbm', 'pnm', 'ico', 'webp']
    def send_image_msg(event):
        path = event.data
        if path.split('.')[-1].lower() not in ALLOWED_IMAGE_EXTENSIONS: return
        with open(path, 'br') as f: img_bin = f.read()
        msg_uuid = uuid4()
        send(conn_main, {'route':'send_message', 'friend_uuid':selected_contact.uuid, 'text':None, 'image':img_bin, 'uuid':msg_uuid})

        f_msg = Frame(f_chat, bg=Color.BACK)
        l_msg = Label(f_msg, bg=Color.BACK)

        img = PilImage.open(BytesIO(img_bin))
        x, y = img.size
        resize = max(img.size)/300
        img = ImageTk.PhotoImage(img.resize((int(x/resize), int(y/resize))))
        l_msg.config(image=img, text='')
        l_msg.image = img

        l_msg.pack(side='right')
        f_msg.pack(fill='x')
        l_msg.bind('<Button-3>', lambda e: msg_menu_appear(e, 'img_right', Message(msg_uuid, selected_contact.uuid, selected_contact.uuid, None, img_bin, None)))

        ThemeHandler.add(f_msg, l_msg)
        update_chat_view()
    f_chat._parent_canvas.drop_target_register(DND_FILES)
    f_chat._parent_canvas.dnd_bind('<<Drop>>', send_image_msg)

    def send_text_msg(event):
        if (event.keycode != 13 or not selected_contact
            or not (text := e_msg.get())): return
        msg_uuid = uuid4()
        send(conn_main, {'route':'send_message', 'friend_uuid':selected_contact.uuid, 'text':text, 'image':None, 'uuid':msg_uuid})

        e_msg.delete(0, 'end')

        f_msg = Frame(f_chat, bg=Color.BACK)
        l_msg = Label(f_msg, text=text, bg=Color.MAIN, fg=Color.BACK, font=('Arial', 12, 'bold'), wraplength=300)

        l_msg.pack(side='right')
        f_msg.pack(fill='x')
        l_msg.bind('<Button-3>', lambda e: msg_menu_appear(e, 'txt_right', Message(msg_uuid, selected_contact.uuid, selected_contact.uuid, text, None, None)))

        ThemeHandler.add(f_msg, l_msg)
        update_chat_view()
    e_msg.bind('<Key>', send_text_msg, '+')

    sb_msg = Scrollbar(f_chat_main, command=e_msg.xview, cursor='sb_h_double_arrow', orientation='horizontal',
                       button_color=Color.MAIN, button_hover_color=Color.MAIN)
    sb_msg.pack(fill='x')
    e_msg.config(xscrollcommand=sb_msg.set)

    frame_widgets += [msg_menu, f_chat_main, f_chat_up, c_color, l_name, c_is_online, f_chat_up_sub, l_last_seen, f_chat_sub, f_chat, e_msg, sb_chat, sb_msg, f_chat_up_split, l_unfriend]


    tab_switch.add(f_main, text='Chatting')

    update_friend_requests = init_friend_request_frame(conn_main, tab_switch, update_list)

    ThemeHandler.add(*frame_widgets)
    frame_widgets.clear()


    def help_thread() -> None:
        conn_help.settimeout(1)
        while not stop_help_thread:
          try:
            match (req := recv(conn_help))['route']:
                case 'list':
                    update_list(req['list'])
                    if not len(req['list']):
                        f_chat_main.pack_forget()
                    else:
                        if not f_chat_main.winfo_manager() and selected_contact:
                            f_chat_main.pack(fill='both', side='left', expand=True)

                case 'requests':
                    update_friend_requests(req['out'], req['in'])

                case 'chat':
                    if selected_contact and selected_contact.uuid == req['from']:
                        update_chat(req['res'])

          except timeout:
              continue

    Thread(target=help_thread, daemon=True).start()