from ui_classes  import Tk, Notebook, Style, Color, ThemeHandler, TkHandler, Frame, Button
from tkinterdnd2 import TkinterDnD

from connect_error_frame  import init_connect_error_frame
from log_in_frame         import init_log_in_frame
from sign_up_frame        import init_sign_up_frame
from chat_frame           import init_chat_frame

from socket import socket, AF_INET, SOCK_STREAM, error as socket_error
from sockio import send
IP = "127.0.0.1"
PORT = 12345

ThemeHandler.add(
    root := TkinterDnD.Tk(),
    tab_switch := Notebook(root),
    b_theme := Button(root, text='Change theme', bg=Color.BACK, fg=Color.FORE,
                      command=ThemeHandler.change_theme)
)

Style().theme_use('alt')
Style().configure('TNotebook', background=Color.BACK)
Style().configure('TNotebook.Tab', font=('Arial', 10, 'bold'), background=Color.BACK, foreground=Color.MAIN)
Style().map('TNotebook.Tab', background=[('selected', Color.MAIN)], foreground=[('selected', Color.BACK)])
root.config(bg=Color.BACK)
tab_switch.add(Frame(), state='disabled', text=' '*24)
b_theme.place(x=10, y=0)

def custom_excepthook(self, exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, socket_error):
        TkHandler.close_all()
        for i in tab_switch.tabs()[1:]:
            tab_switch.forget(i)
        init_connect_error_frame(tab_switch)
    global original_report_callback_exception
    original_report_callback_exception(self, exc_type, exc_value, exc_traceback)
original_report_callback_exception = Tk.report_callback_exception
root.report_callback_exception = custom_excepthook.__get__(root)

conn_main = socket(AF_INET, SOCK_STREAM)
conn_help = socket(AF_INET, SOCK_STREAM)
connected = True

try:
    conn_main.connect((IP, PORT))
    conn_help.connect((IP, PORT))
except:
    connected = False
    init_connect_error_frame(tab_switch)

def callback():
    for i in tab_switch.tabs()[1:]:
        tab_switch.forget(i)
    init_chat_frame(conn_main, conn_help, tab_switch, callback)
    tab_switch.select('.!notebook.chat_frame')

if connected:
    init_log_in_frame(conn_main, tab_switch, callback)
    init_sign_up_frame(conn_main, tab_switch, callback)

def on_window_close():
    TkHandler.close_all()
    try: send(conn_main, {'route':'end'})
    except: ...
    conn_main.close()
    root.destroy()

root.protocol('WM_DELETE_WINDOW', on_window_close)

tab_switch.pack(expand=True, fill='both')
root.title('Chit-Chat')
#root.geometry('1000x600')
root.geometry('800x400')
root.minsize(800, 400)
root.mainloop()