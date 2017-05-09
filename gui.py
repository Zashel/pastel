from tkinter import *
from tkinter.ttk import *
from collections import OrderedDict

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
        posible = {"index": IntVar(),
                   "fecha_aplicacion": StringVar(),
                   "codigo_ciclo": IntVar(),
                   "cliente": StringVar(),
                   "nif": StringVar(),
                   "id_factura": IntVar(),
                   "fecha_operacion": StringVar(),
                   "importe": IntVar(),
                   "importe_str": StringVar(),
                   "periodo_facturado": StringVar(),
                   "metodo": StringVar(),
                   "via": StringVar()}
        self._active_pago = {"link": StringVar(),
                            "index": IntVar(),
                            "fecha": StringVar(),
                            "importe": IntVar(),
                            "importe_str": StringVar(),
                            "observaciones": StringVar(),
                            "dni": StringVar(),
                            "id_cliente": IntVar(),
                            "tels": StringVar(),
                            "oficina": IntVar(),
                            "posibles": [posible for x in range(50)],
                            "total_posibles": IntVar(),
                            "estado": StringVar}
        self._pagos_list = [dict(self._active_pago) for x in range(50)]
        self._total_pagos_list = int()
        self.none_dict = {type(str()): "",
                          type(int()): 0,
                          type(float()): 0.0,
                          type(bool()): False}

        self.widgets()
        self.set_menu()

    def clean_pago(self, pago):
        for field in pago:
            if field == "posibles":
                for posible in pago[field]:
                    for posible_field in posible:
                        none = self.none_dict[type(posible[posible_field])]
                        posible[posible_field].set(none)
            else:
                none = self.none_dict[type(pago[field])]
                pago[field].set(none)

    def clean_pagos_list(self):
        for item in self._pagos_list:
            self.clean_pago(item)
        self._total_pagos_list = int()

    def set_pago(self, pago, data):
        pago["link"].set(data["_links"]["self"]["href"])
        pago["fecha"].set(data["fecha"])
        pago["importe"].set(int(data["importe"]))
        importe_str = str(data["importe"])
        importe_str = "{},{} €".format(importe_str[:-2], importe_str[-2:])
        pago["importe_str"].set(importe_str)
        pago["observaciones"].set(data["observaciones"])
        pago["dni"].set(data["dni"])
        pago["id_cliente"].set(data["id_cliente"])
        pago["tels"].set(", ".join(data["tels"]))
        pago["oficina"].set(data["oficina"])
        pago["estado"].set(data["estado"])
        pago["total_posibles"].set(len(data["posibles"]))
        for s_index, posible in enumerate(data["posibles"]):
            pago["posible"][s_index]["index"].set(s_index)
            datos = posible.split(";")
            heads = ["fecha_aplicacion",
                     "codigo_ciclo",
                     "cliente",
                     "nif",
                     "id_factura",
                     "fecha_operacion",
                     "importe",
                     "importe_str",
                     "periodo_facturado",
                     "metodo",
                     "via"]
            for h_index, head in enumerate(heads):
                dato = datos[h_index]
                if head in ("importe", "id_factura"):
                    dato = int(dato)
                elif head == "importe_str":
                    dato = str(pago["posible"][s_index][head]["importe"].get())
                    dato = "{},{} €".format(dato[:-2], dato[-2:])
                pago["posible"][s_index][head].set(dato)

    def set_pagos_list(self, data):
        self.clean_pagos_list()
        for index, item in enumerate(data):
            self._pagos_list[index]["index"].set(index)
            self.set_pago(self.pagos_list[index], item)
        self._total_pagos_list = len(data)

    def widgets(self):
        #TABS
        self.tabs = {"init": Frame(self),
                     "configuration": Frame(self),
                     "payments": Frame(self)}

        #Payments Tree
        columns = OrderedDict({"estado": [100, "Estado"],
                               "fecha": [100, "Fecha Pago"],
                               "importe_str": [100, "Importe"],
                               "dni": [100, "DNI"],
                               "id_cliente": [100, "ID Cliente"],
                               "tels": [100, "Teléfonos"],
                               "oficina": [100, "Oficina"],
                               "observaciones": [100, "Observaciones"]})
        self.payments_tree_frame = Frame(self.tabs["payments"])
        self.payments_tree_frame.pack()
        self.payments_tree = Treeview(self.payments_tree_frame, columns=list(columns.keys()))
        self.payments_tree.column("#0", width=100)
        self.payments_tree.heading("#0", text="ID")
        for column in columns:
            self.payments_tree.column(column, width=columns[column][0])
            self.payments_tree.heading(column, text=columns[column][1])
        self.payments_tree.column("estado", width=100)
        self.payments_tree.pack()

        self.payment_frame = Frame(self.tabs["payments"])
        self.payment_frame.tkraise(self.payments_tree_frame)
        Button(self.payment_frame, text="Cerrar", command=self.hide_payment).pack()

    def hide_payment(self):
        self.payment_frame.pack_forget()
        self.payments_tree.pack()

    def hide_payment_tree(self):
        self.payments_tree.pack_forget()
        self.payment_frame.pack()

    def update_payments_tree(self):
        for index in range(self._total_pagos_list):
            pass

    def set_menu(self):
        self.option_add("*tearOff", FALSE)
        win = self.winfo_toplevel()
        self.menubar = Menu(win)
        win["menu"] = self.menubar

        self.menu_file = Menu(self.menubar)
        self.menu_edit = Menu(self.menubar)
        self.menu_open = Menu(self.menubar)
        self.menu_new = Menu(self.menubar)
        self.menu_load = Menu(self.menubar)

        self.menubar.add_cascade(menu=self.menu_file, label="Archivo")
        self.menubar.add_cascade(menu=self.menu_edit, label="Edición")

        self.menu_file.add_cascade(menu=self.menu_new, label="Nuevo")
        self.menu_file.add_cascade(menu=self.menu_open, label="Abrir")
        self.menu_file.add_cascade(menu=self.menu_load, label="Cargar")
        self.menu_file.add_command(label="Exportar...")
        self.menu_file.add_separator()
        self.menu_file.add_command(label="Cambiar Usuario")

        self.menu_new.add_command(label="Compromiso")
        self.menu_new.add_command(label="Localización")
        self.menu_new.add_command(label="Pago Pasarela")
        self.menu_new.add_command(label="Usuario")

        self.menu_open.add_command(label="Compromisos")
        self.menu_open.add_command(label="Pagos")
        self.menu_open.add_command(label="Usuarios")

        self.menu_load.add_command(label="Pagos ISM")
        self.menu_load.add_command(label="PARI...")
        self.menu_load.add_command(label="Último PARI")

        self.menu_edit



    @property
    def vars(self):
        return self._vars


if __name__ == "__main__":
    root = Tk()
    app = App(root)
    print(Frame.__module__)
    app.mainloop()