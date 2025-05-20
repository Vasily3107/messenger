from tkinter       import Tk, Label, Entry, Button, Frame, Listbox, Canvas, Scale, Menu, Widget
from tkinter.ttk   import Notebook, Style
from customtkinter import CTkScrollableFrame as Scrollframe, CTkCheckBox as Checkbox, CTkScrollbar as Scrollbar
from PIL           import Image as PilImage, ImageTk
from io            import BytesIO


from jsonpickle import (encode as jp_encode,
                        decode as jp_decode)
class Color:
    _main_white = '#FF3366'
    _main_dark  = '#6633FF'
    _main = '' # temporary main color storage

    MAIN  = ... # see the end of the file
    FORE  = ...
    BACK  = ...
    GREEN = '#33EE33'
    RED   = '#EE3333'

    @classmethod
    def set_theme(cls, value:bool) -> None:
        '''False: WHITE, True: DARK'''
        if value:
            cls._main = cls.MAIN
            cls.MAIN  = cls._main_dark
            cls.FORE  = '#FFFFFF'
            cls.BACK  = '#101218'
        else:
            cls._main = cls.MAIN
            cls.MAIN  = cls._main_white
            cls.FORE  = '#101218'
            cls.BACK  = '#FFFFFF'
        with open('config.txt', 'r') as f:
            data = jp_decode(f.read())
        with open('config.txt', 'w') as f:
            data['theme'] = value
            f.write(jp_encode(data, indent=2))

class AdvEntry(Entry):
    '''advanced tkinter.Entry featuring placeholder text'''
    def __init__(self, master, placeholder:str, hide_input:bool, **kwargs):
        super().__init__(master, **kwargs, insertbackground=Color.MAIN, insertwidth=3,
                         selectbackground=Color.MAIN, selectforeground=Color.BACK)
        self.placeholder = placeholder
        self.hide_input = hide_input
        self.hide_char = '*'

        if hide_input: self.config(show=self.hide_char)

        self.bind('<FocusIn>',  lambda _: self.__clr_placeholder())
        self.bind('<FocusOut>', lambda _: self.__set_placeholder())
        self.__set_placeholder()

    def __clr_placeholder(self):
        if self.__get() == self.placeholder:
            self.delete(0, 'end')
            self.config(fg=Color.FORE, show=(self.hide_char if self.hide_input else ''))

    def __set_placeholder(self):
        if not self.__get():
            self.insert(0, self.placeholder)
            self.config(fg=Color.MAIN, show='')

    def __get(self) -> str: return super().get()

    def theme_switch(self) -> None:
        self.config(bg=Color.BACK)
        if self.get():
            self.config(fg=Color.FORE, insertbackground=Color.MAIN,
                        selectbackground=Color.MAIN, selectforeground=Color.BACK)
        else:
            self.config(fg=Color.MAIN, insertbackground=Color.MAIN,
                        selectbackground=Color.MAIN, selectforeground=Color.BACK)

    def get(self) -> str:
        if (text := self.__get()) == self.placeholder:
            return ''
        else:
            return text

    def set(self, text:str):
        self.delete(0, 'end')
        self.config(fg=Color.FORE, show=(self.hide_char if self.hide_input else ''))
        self.insert(0, text)

from weakref import WeakSet
class ThemeHandler:
    '''class responsible for changing widget theme colors'''
    __is_dark = False
    __widgets = WeakSet()

    @classmethod
    def set_theme(cls, value:bool) -> None:
        '''False: WHITE, True: DARK'''
        cls.__is_dark = value

    @classmethod
    def get_theme(cls) -> bool:
        '''False: WHITE, True: DARK'''
        return cls.__is_dark

    @classmethod
    def add(cls, *items:Widget):
        for i in items:
            if str(i) in map(str, cls.__widgets):
                cls.__widgets.remove(next(j for j in cls.__widgets if str(j) == str(i)))
            cls.__widgets.add(i)
        i = None

    @classmethod
    def change_theme(cls):
        cls.__is_dark = not cls.__is_dark
        Color.set_theme(cls.__is_dark)
        for widget in cls.__widgets:
            cls.__config_widget(widget)

    @classmethod
    def __config_widget(cls, w:Widget):

        if type(w) == Label:
            if (bg := w.cget('bg')) == Color._main:
                w.config(fg=Color.BACK, bg=Color.MAIN)
            elif bg in [Color.GREEN, Color.RED]:
                w.config(fg=Color.BACK)
            else:
                w.config(fg=Color.FORE, bg=Color.BACK)


        elif type(w) == AdvEntry:
            w.theme_switch()


        elif type(w) == Button:
            bg, fg = w.cget('bg'), w.cget('fg')
            if (bg, fg) == (Color.FORE, Color.BACK):
                w.config(bg=Color.BACK, fg=Color.FORE)
            elif bg == Color._main:
                w.config(bg=Color.MAIN, fg=Color.BACK)
            elif bg == Color.FORE:
                w.config(bg=Color.BACK, fg=Color.MAIN)
            else:
                w.config(fg=Color.BACK)


        elif type(w) == Listbox:
            w.config(bg=Color.BACK, fg=Color.MAIN, selectbackground=Color.MAIN, selectforeground=Color.BACK)


        elif type(w) in [Frame, Canvas]:
            if   w.cget('bg') == Color.FORE:
                w.config(bg = Color.BACK)
            elif w.cget('bg') == Color._main:
                w.config(bg = Color.MAIN)


        elif type(w) == Scrollframe:
            w.configure(fg_color=Color.BACK, scrollbar_button_color=Color.MAIN, scrollbar_button_hover_color=Color.MAIN)


        elif type(w) == Notebook:
            Style().configure('TNotebook', background=Color.BACK)
            Style().configure('TNotebook.Tab', font=('Arial', 10, 'bold'), background=Color.BACK, foreground=Color.MAIN)
            Style().map('TNotebook.Tab', background=[('selected', Color.MAIN)], foreground=[('selected', Color.BACK)])


        elif type(w) == Checkbox:
            w.configure(fg_color=Color.MAIN, bg_color=Color.BACK, text_color=Color.MAIN, checkmark_color=Color.BACK,
                        border_color=Color.MAIN, hover_color=(Color.MAIN if w._check_state else Color.BACK))


        elif type(w) == Scrollbar:
            w.configure(button_color=Color.MAIN, button_hover_color=Color.MAIN)


        elif type(w) == Scale:
            w.config(fg=Color.MAIN, bg=Color.BACK, troughcolor=Color.BACK, activebackground=Color.MAIN)


        elif type(w) == Menu:
            w.config(bg=Color.BACK, fg=Color.FORE, activebackground=Color.MAIN, activeforeground=Color.FORE)


        elif type(w) == Tk:
            w.config(bg=Color.BACK, highlightcolor=Color.MAIN, highlightbackground=Color.MAIN)


class TkHandler:
    '''class responsible for closing all additional windows'''
    __windows = WeakSet()

    @classmethod
    def add(cls, win:Tk):
        cls.__windows.add(win)

    @classmethod
    def close_all(cls):
        for i in cls.__windows:
            i.destroy()


try:
    with open('config.txt', 'r') as f:
        theme = jp_decode(f.read())['theme']
    Color.set_theme(theme)
    ThemeHandler.set_theme(theme)

except FileNotFoundError:
    with open('config.txt', 'w') as f:
        f.write(jp_encode({'theme':False}, indent=2))
    Color.set_theme(False)
    ThemeHandler.set_theme(False)