from ui_classes import ThemeHandler, Label, Notebook, Frame, Color

def init_connect_error_frame(tab_switch:Notebook):

    f_main = Frame(tab_switch, name='connect_error_frame', bg=Color.BACK)

    l1 = Label(f_main, text='Server connection error!',
               fg=Color.BACK, bg=Color.MAIN,
               font=('Unispace', 24))
    l1.pack(pady=(60, 0), fill='x')

    l2 = Label(f_main, text=("We couldn't connect you to the server\n"
                             'Please try again later'),
               font=('Consolas', 18, 'bold'), fg=Color.FORE, bg=Color.BACK)
    l2.pack(pady=(30, 0), fill='x')

    tab_switch.add(f_main, text='Connection error')

    ThemeHandler.add(f_main, l1, l2)