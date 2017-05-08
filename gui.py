from tkinter import *

class TkVars:
    def __init__(self):
        self._vars = dict()

    def __getattr__(self, item):
        if item in self._vars:
            return self._vars[item]

    def __setattr__(self, item, value):
        if item == "_vars":
            object.__setattr__(self, item, value)
        else:
            try:
                tk_var_class = {type(str()): StringVar,
                                type(int()): IntVar,
                                type(float()): DoubleVar,
                                type(bool()): BooleanVar
                                }[type(value)]
            except KeyError:
                raise ValueError
            self._vars[item] = tk_var_class()
            self._vars[item].set(value)



class App(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self._vars = TkVars()
        self.vars.integer = 1
        self.vars.float = 1.0
        self.vars.boolean = True
        self.vars.string = "Hola mundo"
        self.widgets()

    def widgets(self):
        self.entry = Entry(self,
                           textvariable=self.vars.string)
        self.entry.pack()

    @property
    def vars(self):
        return self._vars


if __name__ == "__main__":
    root = Tk()
    app = App(root)
    print(app.vars.string.get())
    app.mainloop()