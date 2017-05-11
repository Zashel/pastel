from tkinter import *
from tkinter.ttk import *
from collections import OrderedDict
from functools import partial
from zashel.utils import copy, paste
from definitions import local_config, admin_config, LOCAL, SHARED
import getpass

class TkVars:
    reference = dict()
    def __init__(self, name, r=None, w=None, u=None):
        self._vars = dict()
        self._name = name
        if r is None:
            r = self.nothing
        if w is None:
            w = self.nothing
        if u is None:
            u = self.nothing
        self.r = r
        self.w = w
        self.u = u

    def __getattr__(self, item):
        if item in self._vars:
            return self._vars[item]

    def __setattr__(self, item, value):
        if item in ("_vars", "_name", "r", "w", "u"):
            object.__setattr__(self, item, value)
        else:
            try:
                tk_var_class = {type(str()): StringVar,
                                type(int()): IntVar,
                                type(float()): DoubleVar,
                                type(bool()): BooleanVar
                                }[type(value)]
            except KeyError:
                print(value)
                print(type(value))
                raise ValueError
            if (item not in self._vars or
                    (item in self._vars and not isinstance(self._vars[item], tk_var_class))):
                self._vars[item] = tk_var_class()
                self._vars[item].trace("r", partial(self.r, var_name="{}.{}".format(self._name, item)))
                self._vars[item].trace("w", partial(self.w, var_name="{}.{}".format(self._name, item)))
                self._vars[item].trace("u", partial(self.u, var_name="{}.{}".format(self._name, item)))
            self._vars[item].set(value)

    def nothing(self, *args, **kwargs):
        pass
    
    def set(self, name, value=None):
        if value == None:
            value = str()
        self.__setattr__(name, value)
        
    def get(self, name):
        return self.__getattr__(name)

class EasyFrame(Frame):
    def __init__(self, *args, master=None, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.to_save = dict()
        self.clean_to_save()
        self._undo = {"var": None,
                      "last": None}
        self._vars = dict()
        self.set_widgets()
        self.set_menu()

    @property
    def vars(self):
        return self._vars

    def set_widgets(self):
        pass

    def set_menu(self):
        pass

    def set_var(self, route, value=None):
        cat, name = route.split(".")
        if cat not in self._vars:
            self._vars[cat] = TkVars(cat)
        self._vars[cat].set(name, value)
        return self._vars[cat].get(name)

    def get_var(self, route):
        cat, name = route.split(".")
        if cat not in self._vars:
            raise KeyError()
        return self._vars[cat].get(name)

    def Entry(self, route, *args, **kwargs):
        try:
            var = self.get_var(route)
        except KeyError:
            var = self.set_var(route)
        last_entry_validation = (self.register(self.entered_entry), "%P", route, str(var))
        return Entry(*args, textvariable=var, validate="all", validatecommand=last_entry_validation, **kwargs)

    def Checkbutton(self, route, *args, **kwargs):
        try:
            var = self.get_var(route)
        except KeyError:
            var = self.set_var(route)
        last_entry_validation = partial(self.entered_entry, not var.get(), route, str(var))
        return Checkbutton(*args, variable=var, command=last_entry_validation, **kwargs)

    def clean_to_save(self, category=None):
        template = {"old": dict(),
                    "var": dict()}
        if category is None:
            for category in self.to_save:
                self.to_save[category] = dict(template)
        else:
            self.to_save[category] = dict(template)

    def save_and_close(self, category, dialog):
        self.save(category)
        dialog.destroy()

    def entered_entry(self, value, route, var, *args):
        cat, item = route.split(".")
        var = self.getvar(var)
        if cat not in self.to_save:
            self.clean_to_save(cat)
        if not item in self.to_save[cat]["old"]:
            self.to_save[cat]["old"][item] = value
        if not item in self.to_save[cat]["var"]:
            self.to_save[cat]["var"][item] = var
        if self._undo["var"] != str(var):
            self._undo["var"] = str(var)
            self._undo["last"] = value

    def undo(self):
        self.getvar(self._undo["var"]).set(self._undo["last"])

    def copy(self):
        copy(self.master.selection_get())

    def cut(self):
        self.copy()
        self.master.selection_own_get().delete(SEL_FIRST, SEL_LAST)

    def paste(self):
        self.master.focus_get().insert(INSERT, paste())

    def save(self, category):
        try:
            save = self.__getattribute__("save_{}".format(category))
        except AttributeError:
            raise
        save()
        self.clean_to_save(category)

    def category(self, category):
        return list(self.to_save[category]["var"].keys())

    def get_var_in_category(self, category, name):
        return self.get_var(".".join((category, name)))

    def clean_changes(self, category):
        for item in self.to_save[category]["var"]:
            if item in self.to_save[category]["old"]:
                self.to_save[category]["var"][item].set(self.to_save[category]["old"][item])


class App(EasyFrame):
    def __init__(self, master=None):
        super().__init__(master=master, padding=(3, 3, 3, 3))
        self.pack()

        posible = OrderedDict({"index": IntVar(),
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
                               "via": StringVar()})
        self._active_pago = OrderedDict({"link": StringVar(),
                                         "index": IntVar(),
                                         "fecha": StringVar(),
                                         "importe": IntVar(),
                                         "importe_str": StringVar(),
                                         "observaciones": StringVar(),
                                         "dni": StringVar(),
                                         "id_cliente": IntVar(),
                                         "tels": StringVar(),
                                         "oficina": IntVar(),
                                         "posibles": [dict(posible) for x in range(50)],
                                         "total_posibles": IntVar(),
                                         "estado": StringVar()})

        self._pagos_list = [dict(self._active_pago) for x in range(50)]
        self._total_pagos_list = int()
        self.none_dict = {type(str()): "",
                          type(int()): 0,
                          type(float()): 0.0,
                          type(bool()): False}
        for item in self._pagos_list:
            for field in item:
                if field in ("estado", "total_posibles"):
                    item[field].trace("w",
                                      partial(self.changed_data,
                                       var_name="pagos.{}.{}".format(str(item["index"]),
                                                                         item[field])))
                for posible in item["posibles"]:
                    for field in posible:
                        if field != "index":
                            posible[field].trace("w",
                                                 partial(self.changed_data,
                                                          var_name="pagos.{}.posibles.{}.{}".format(str(item["index"]),
                                                                                                    str(posible["index"]),
                                                                                                    posible[field])))
        for field in self._active_pago:
            if field in ("estado", "total_posibles"):
                item[field].trace("w",
                                  partial(self.changed_data,
                                          var_name="active_pago.{}".format(item[field])))
            for posible in item["posibles"]:
                for field in posible:
                    if field != "index":
                        posible[field].trace("w",
                                             partial(self.changed_data,
                                                     var_name="active_pago.posibles.{}.{}".format(str(posible["index"]),
                                                                                                  posible[field])))
        self.usuario =  getpass.getuser()
        self.rol = "Operador"
        self.set_var("config.nombre_usuario", "")
        #Widgets
        self.set_var("test.test", "Hola Caracola")
        self.Entry("test.test", self).pack()

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

    def set_widgets(self):
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
        self.menu_open.add_command(label="Pagos Pendientes")
        self.menu_open.add_command(label="Pagos Ilocalizables")
        self.menu_open.add_command(label="Usuarios")

        self.menu_load.add_command(label="Pagos ISM")
        self.menu_load.add_command(label="PARI...")
        self.menu_load.add_command(label="Último PARI")

        self.menu_edit.add_command(label="Deshacer", command=self.undo)
        self.menu_edit.add_separator()
        self.menu_edit.add_command(label="Cortar", command=self.cut)
        self.menu_edit.add_command(label="Copiar", command=self.copy)
        self.menu_edit.add_command(label="Copiar página")
        self.menu_edit.add_command(label="Pegar", command=self.paste)
        self.menu_edit.add_separator()
        self.menu_edit.add_command(label="Preferencias", command=self.win_propiedades)

        self.menu_edit

    def win_propiedades(self):
        self.set_config()
        self.clean_to_save("config")
        dialog = Toplevel(self.master)
        dialog.focus_set()
        dialog.grab_set()
        dialog.transient(master=self.master)
        notebook = Notebook(dialog)
        notebook.grid(column=0, row=0, columnspan=4)
        save_and_close = partial(self.save_and_close, "config", dialog)
        save = partial(self.save, "config")
        clean_changes = partial(self.clean_changes, "config")

        usuario = Frame(notebook)
        servidor = Frame(notebook)
        rutas = Frame(notebook)
        datos = Frame(notebook)

        #Usuario
        usuario.grid(sticky=(N, S, E, W))
        Label(usuario, text="Login: ").grid(column=0, row=1, sticky=(N, W))
        Label(usuario, text=self.usuario).grid(column=1, row=1, sticky=(N, W))
        Label(usuario, text="Rol: ").grid(column=5, row=1, sticky=(N, E))
        Label(usuario, text=self.rol).grid(column=6, row=1, sticky=(N, E,))
        Label(usuario, text="Nombre: ").grid(column=0, row=2, sticky=(N, W))
        self.Entry("config.nombre_usuario",
                   usuario).grid(column=1, row=2, columnspan=5, sticky=(N, E))

        #Servidor
        servidor.grid(sticky=(N, S, E, W))
        self.Checkbutton("config.INIT_SERVER_STARTUP",
                         servidor,
                         text="Init server at StartUp").grid(column=0, row=0, columnspan=5)
        Label(servidor, text="Host: ").grid(column=0, row=1)
        self.Entry("config.HOST",
                   servidor).grid(column=1, row=1, columnspan=2)
        Label(servidor, text="Port: ").grid(column=3, row=1)
        self.Entry("config.PORT",
                   servidor).grid(column=4, row=1, columnspan=1)

        #Rutas
        rutas.grid(sticky=(N, S, E, W))
        Label(rutas, text="Admin Local: ").grid(column=0, row=0, sticky=(N, W))
        self.Entry("config.ADMIN_DB",
                   rutas).grid(column=1, row=0, sticky=(N, E))
        Label(rutas, text="Path: ").grid(column=0, row=1, sticky=(N, W))
        self.Entry("config.PATH",
                   rutas).grid(column=1, row=1, sticky=(N, E))
        Label(rutas, text="Exportaciones: ").grid(column=0, row=2, sticky=(N, W))
        self.Entry("config.EXPORT_PATH",
                   rutas).grid(column=1, row=2, sticky=(N, E))
        Label(rutas, text="Exportaciones diarias: ").grid(column=0, row=3, sticky=(N, W))
        self.Entry("config.DAILY_EXPORT_PATH",
                   rutas).grid(column=1, row=3, sticky=(N, E))
        Label(rutas, text="Reportes: ").grid(column=0, row=4, sticky=(N, W))
        self.Entry("config.REPORT_PATH",
                   rutas).grid(column=1, row=4, sticky=(N, E))
        Label(rutas, text="Base de Datos: ").grid(column=0, row=5, sticky=(N, W))
        self.Entry("config.DATABASE_PATH",
                   rutas).grid(column=1, row=5, sticky=(N, E))
        #Datos

        notebook.add(usuario, text="Usuario")
        notebook.add(servidor, text="Servidor")
        notebook.add(rutas, text="Rutas")
        #notebook.add(datos, text="Datos")

        #Botones
        Button(dialog, text="Aceptar", command=save_and_close).grid(column=0, row=1)
        Button(dialog, text="Aplicar", command=save).grid(column=1, row=1)
        Button(dialog, text="Borrar Cambios", command=clean_changes).grid(column=2, row=1)
        Button(dialog, text="Cancelar", command=dialog.destroy).grid(column=3, row=1)
        dialog.wait_window(dialog)

    def save_config(self):
        get_var = partial(self.get_var_in_category, "config")
        for item in self.category("config"):
            if item in LOCAL:
                local_config.set(item, get_var(item).get())
            elif item in SHARED:
                admin_config.set(item, get_var(item).get())

    def changed_data(self, var, void, action, var_name): #I don't know if I need it...
        pass

    def set_config(self):
        self.set_var("config.HOST", local_config.HOST)
        self.set_var("config.PORT", local_config.PORT)
        self.set_var("config.INIT_SERVER_STARTUP", local_config.INIT_SERVER_STARTUP)
        self.set_var("config.PATH", local_config.PATH)
        self.set_var("config.EXPORT_PATH",local_config.EXPORT_PATH)
        self.set_var("config.ADMIN_DB", local_config.ADMIN_DB)
        self.set_var("config.DATABASE_PATH", admin_config.DATABASE_PATH)
        self.set_var("config.REPORT_PATH", admin_config.REPORT_PATH)
        self.set_var("config.DAILY_EXPORT_PATH", admin_config.DAILY_EXPORT_PATH)

if __name__ == "__main__":
    root = Tk()
    app = App(root)
    app.mainloop()