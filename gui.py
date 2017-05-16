from tkinter import *
from tkinter.ttk import *
from api import API
from functools import partial
from definitions import local_config, admin_config, LOCAL, SHARED
from tkutils import *
import getpass

class App(EasyFrame):
    def __init__(self, master=None):
        super().__init__(master=master, padding=(3, 3, 3, 3))
        self.pack()
        self.usuario =  getpass.getuser()
        self.rol = "Operador"
        self.set_var("config.nombre_usuario", "")
        #Widgets
        self.set_menu()
        self.set_widgets()
        self.set_var("test.test", "Hola Caracola")
        self.Entry("test.test", self).pack()
        self.update_pagos_tree(estado="PENDIENTE")

    def set_widgets(self):
        #TABS
        self.tabs = {"init": Frame(self),
                     "configuration": Frame(self),
                     "payments": Frame(self)}

        #Payments Tree
        columns = ["estado",
                   "fecha",
                   "importe",
                   "dni",
                   "id_cliente",
                   "tels",
                   "oficina",
                   "observaciones"]
        default_config = {"columns": {"width": 75},
                          "column": {"#0": {"width": 45},
                                     "oficina": {"width": 30},
                                     "observaciones": {"width": 400}},
                          "heading": {"#0": {"text": "ID"},
                                      "estado": {"text": "Estado"},
                                      "fecha": {"text": "Fecha Pago"},
                                      "importe": {"text": "Importe"},
                                      "dni": {"text": "DNI"},
                                      "id_cliente": {"text": "ID Cliente"},
                                      "tels": {"text": "Teléfonos"},
                                      "oficina": {"text": "Oficina"},
                                      "observaciones": {"text": "Observaciones"}},
                          "show": {"importe": lambda x: str(x)[:-2]+str(x)[-2:]+" €",
                                   "tels": lambda x: ", ".join(x)},
                          "validate": {"importe": lambda x: int(x.replace("\n", "").replace(" ", "").replace("€", ""))}}
        self.payments_tree_frame = Frame(self.tabs["payments"])
        self.payments_tree_frame.grid()
        treeScroll = Scrollbar()
        self.TreeView("pagos",
                      columns,
                      self.payments_tree_frame,
                      default_config=default_config,
                      yscrollcommand=treeScroll).grid(column=0, row=0, columnspan=5)
        self.payments_tree_first = self.LinkButton(self.payments_tree_frame,
                                                   command=lambda: self.update_pagos_tree("first"),
                                                   text="Primero",
                                                   state="disable")
        self.payments_tree_first.grid(column=0, row=1)
        self.payments_tree_prev = self.LinkButton(self.payments_tree_frame,
                                                  command=lambda: self.update_pagos_tree("prev"),
                                                  text="Anterior",
                                                  state="disable")
        self.payments_tree_prev.grid(column=1, row=1)
        self.payments_tree_label = Label(self.payments_tree_frame,
                                         text="Página 1 de 1")
        self.payments_tree_label.grid(column=2, row=1)
        self.payments_tree_next = self.LinkButton(self.payments_tree_frame,
                                                  command=lambda: self.update_pagos_tree("next"),
                                                  text="Siguiente",
                                                  state="disable")
        self.payments_tree_next.grid(column=3, row=1)
        self.payments_tree_last = self.LinkButton(self.payments_tree_frame,
                                                  command=lambda: self.update_pagos_tree("last"),
                                                  text="Último",
                                                  state="disable")
        self.payments_tree_last.grid(column=4, row=1)
        self.payment_frame = Frame(self.tabs["payments"])
        self.payment_frame.tkraise(self.payments_tree_frame)
        Button(self.payment_frame, text="Cerrar", command=self.hide_payment).pack()
        self.tabs["payments"].pack()

    def update_pagos_tree(self, link=None, **filter):
        if link is None:
            API.filter_pagos(link, **filter)
            pagos = API.get_pagos_list()
        else:
            pagos = API.get_pagos_list(link) #TODO: fix this shit
        pagos_dict = dict()
        if pagos is not None:
            for pago in pagos:
                pagos_dict[pago["_id"]] = pago
        self.set_tree_data("pagos", pagos_dict)
        for link in ("first", "prev", "next", "last"):
            self.__getattribute__("payments_tree_"+link)["state"] = "enable"
        page = API.get_this_pagos_page()
        last = API.get_total_pagos_page()
        if page == 1:
            self.payments_tree_first["state"] = "disable"
            self.payments_tree_prev["state"] = "disable"
        if page == last:
            self.payments_tree_next["state"] = "disable"
            self.payments_tree_last["state"] = "disable"
        self.payments_tree_label["text"] = "Página {} de {}".format(str(page), str(last))

    def hide_payment(self):
        self.payment_frame.pack_forget()
        self.payments_tree.pack()

    def hide_payment_tree(self):
        self.payments_tree.pack_forget()
        self.payment_frame.pack()

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