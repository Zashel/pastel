from tkinter import *
from tkinter.ttk import *
from api import API
from functools import partial
from definitions import local_config, admin_config, LOCAL, SHARED, PAYMENTS_FIELDS
from tkutils import *
from utils import *
import getpass
import json
import os
import datetime

class Images:
    def __init__(self):
        self.add = PhotoImage(file=os.path.join("icons", "add.gif"))
        self.remove = PhotoImage(file=os.path.join("icons", "remove.gif"))

class App(EasyFrame):
    def __init__(self, master=None):
        super().__init__(master=master, padding=(3, 3, 3, 3))
        self.pack()
        self.usuario =  getpass.getuser()
        self.rol = "Operador"
        self.set_var("config.nombre_usuario", "")
        #Widgets
        self.images = Images()
        self.set_variables()
        self.set_menu()
        self.set_widgets()

    def set_widgets(self):
        self.payment_data_frame_text = dict()
        self.tabs = {"init": Frame(self),
                     "configuration": Frame(self),
                     "payments": Frame(self)}
        self.set_payments_tree_frame()
        #TABS

    def payment_data_frame(self, parent):
        row = 0
        # Frame
        frame = Frame(parent)
        #Objects:
        LabelEntry = partial(self.LabelEntry, entrykwargs={"state": "readonly"})
        LabelEntry("pagos.fecha", "Fecha Pago: ", frame, ).grid(column=0, row=row)
        LabelEntry("pagos.oficina", "Oficina: ", frame).grid(column=1, row=row)
        LabelEntry("pagos.importe", "Importe: ", frame).grid(column=2, row=row)
        row += 1
        LabelEntry("pagos.dni", "DNI: ", frame).grid(column=0, row=row)
        LabelEntry("pagos.id_cliente", "Id_Cliente: ", frame).grid(column=1, row=row)
        LabelEntry("pagos.tels", "Teléfonos", frame).grid(column=2, row=row)
        row += 1
        self.payment_data_frame_text[parent] = Text(frame, width=80, height=5, state="disable")
        self.payment_data_frame_text[parent].grid(column=0, row=row, columnspan=3)
        row += 1
        LabelEntry("pagos.importe_pendiente", "Importe Sin Asociar: ", frame).grid(column=1, row=row)
        self.Combobox("pagos.estado", admin_config.PAYMENTS_STATES, frame).grid(column=2, row=row) #frame is the name of the bunny
        return frame

    def payment_posibles_frame(self, parent, name):
        frame = Frame(parent)
        row = 0
        columnspan = 4
        if "editable" in name:
            editable = ["dni", "nombre", "id_factura", "importe", "periodo_facturado"]
        else:
            editable = list()
        default_config = {"columns": {"width": 100},
                          "column": {"#0": {"width": 30},
                                     "periodo_facturado": {"width": 110},
                                     },
                          "heading": {"#0": {"text": "ID"},
                                      "dni": {"text": "DNI"},
                                      "nombre": {"text": "Nombre"},
                                      "id_factura": {"text": "ID Factura"},
                                      "importe": {"text": "Importe"},
                                      "periodo_facturado": {"text": "Periodo Facturado"}},
                          #"show": {"importe": lambda x: str(x)[:-2] + "," + str(x)[-2:] + " \u20ac",
                          #         },
                          "show": {"importe": lambda x: x+" \u20ac",
                                   },
                          "validate": {"importe": lambda x: str(float(x.replace("\n", "")
                                                                      .replace(" ", "")
                                                                      .replace("\u20ac", "")
                                                                      .replace(",", "."))
                                                                ).replace(".", ","),
                                       },
                          "bind": {},
                          "editable": editable}
        tree = self.TreeView(name, self.posibles_columns, frame, default_config=default_config, yscroll=True)
        if "editable" in name:
            self.set_tree_calculation(name, partial(self.calculate_pending, name))
        tree.grid(column=0, row=row, columnspan=columnspan)
        if "editable" in name:
            row += 1
            delete = partial(self.del_selected_item_in_tree_data, name)
            self.ImageButton(frame, self.images.remove, command=delete).grid(column=2, row=row, sticky=E)
            self.ImageButton(frame, self.images.add,
                             command=self.add_new_row_to_posibles).grid(column=3, row=row, sticky=W)
        return frame

    def add_new_row_to_posibles(self):
        item = "0"
        tree = self.tree["editable_posibles"]["tree"]
        while True:
            try:
                dni = tree.set(item, "dni")
                nombre = tree.set(item, "nombre")
                next = tree.next(item)
                if next == "":
                    item = str(int(item)+1)
                    break
            except TclError:
                dni = str()
                nombre = str()
        data = {"dni":dni, "nombre":nombre}
        self.append_to_tree_data("editable_posibles", item, data)

    def calculate_pending(self, name):
        tree = self.tree[name]["tree"]
        paid = 0
        next = "0"
        while True:
            try:
                paid += int(round(float(tree.set(next, "importe").replace(" \u20ac", "").replace(",", "."))*100, 2))
            except TclError:
                break
            next = tree.next(next)
            if next == "":
                break
        total = int(round(float(self.get_var("pagos.importe").get().replace(" \u20ac", "").replace(",", "."))*100, 2))
        print("Total: ", str(total))
        print("Pagado: ", str(paid))
        self._pending = total - paid
        self._pending_variable.set(str(round(self._pending/100, 2)).replace(".", ",")+" \u20ac")

    def payment_posibles_load(self, name):
        posibles = self.get_var("pagos.posibles").get()
        final = dict()
        order = list()
        for index, item in enumerate(posibles):
            posible = item.get().split(";")
            print(posible)
            final[str(index)] = dict()
            order.append(index)
            for header in self.posibles_headers:
                if header in self.posibles_columns:
                    if header in self.tree[name]["validate"]:
                        val = self.tree[name]["validate"][header]
                    else:
                        val = lambda x: x
                    final[str(index)][header] = posible[self.posibles_headers.index(header)]
        order.sort()
        self.set_tree_data(name, final, order=[str(key) for key in order])
        self.calculate_pending(name)

    def set_payments_tree_frame(self):
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
                          "show": {"importe": lambda x: str(x).replace(" \u20ac", "").replace(",", "")[:-2]+","+
                                                        str(x).replace(" \u20ac", "").replace(",", "")[-2:]+" \u20ac",
                                   "tels": lambda x: ", ".join(x)},
                          "validate": {"importe": lambda x: int(x.replace("\n", "").replace(" ", "")
                                                                .replace("\u20ac", "").replace(".", "").replace(",", "")),
                                       "tels": lambda x: x.split(", ")},

                          "bind": {}}
        self.payments_tree_frame = Frame(self.tabs["payments"])
        self.payments_tree_frame.pack()
        row = 0
        # Payment search
        Label(self.payments_tree_frame, text="Estado: ").grid(column=0, row=row, sticky="e")
        self.Combobox("paysearch.state", admin_config.PAYMENTS_STATES, self.payments_tree_frame).grid(column=1,
                                                                                                      row=row,
                                                                                                      sticky="w")
        self.LabelEntry("paysearch.customer_id", "DNI: ", self.payments_tree_frame).grid(column=2,
                                                                                         row=row) #TODO: Do a phone searching
        Button(self.payments_tree_frame,
               text="Buscar",
               command=self.search_payment,
               ).grid(column=3, row=row)
        row += 1
        #Button(self.payments_tree_frame,
        #       text="CalcularDNI",
        #       command=self.validate_dni,
        #       ).grid(column=4, row=row)
        row += 1
        self.LabelEntry("paysearch.pay_date", "Fecha: ", self.payments_tree_frame).grid(column=0, row=row, columnspan=2)
        self.LabelEntry("paysearch.office", "Oficina: ", self.payments_tree_frame).grid(column=2, row=row)
        self.LabelEntry("paysearch.amount", "Importe: ", self.payments_tree_frame).grid(column=3, row=row)
        row += 1
        self.payments_tree = self.TreeView("pagos",
                                           columns,
                                           self.payments_tree_frame,
                                           default_config=default_config,
                                           yscroll=True)
        self.payments_tree.bind("<Double-1>", self.open_payment_data_frame)
        #treeScroll = Scrollbar(self.payments_tree_frame,
        #                       orient=VERTICAL,
        #                       command=self.payments_tree.yview)
        #self.payments_tree["yscroll"] = treeScroll.set
        self.payments_tree.grid(column=0, row=row, columnspan=5)
        self.payments_tree_first = self.LinkButton(self.payments_tree_frame,
                                                   command=lambda: self.update_pagos_tree("first"),
                                                   text="Primero",
                                                   state="disable")
        row += 1
        self.payments_tree_first.grid(column=0, row=row)
        self.payments_tree_prev = self.LinkButton(self.payments_tree_frame,
                                                  command=lambda: self.update_pagos_tree("prev"),
                                                  text="Anterior",
                                                  state="disable")
        self.payments_tree_prev.grid(column=1, row=row)
        self.payments_tree_label = Label(self.payments_tree_frame,
                                         text="Página 1 de 1")
        self.payments_tree_label.grid(column=2, row=row)
        self.payments_tree_next = self.LinkButton(self.payments_tree_frame,
                                                  command=lambda: self.update_pagos_tree("next"),
                                                  text="Siguiente",
                                                  state="disable")
        self.payments_tree_next.grid(column=3, row=row)
        self.payments_tree_last = self.LinkButton(self.payments_tree_frame,
                                                  command=lambda: self.update_pagos_tree("last"),
                                                  text="Último",
                                                  state="disable")
        self.payments_tree_last.grid(column=4, row=row)
        row += 1

        #Payment Frame
        self.payment_frame = Frame(self.tabs["payments"])
        self.payment_data_frame(self.payment_frame).pack()
        self.payment_posibles_frame(self.payment_frame, "posibles").pack()
        Button(self.payment_frame, text="Cerrar", command=self.show_payments_tree).pack()

        #Pending Payment Frame
        self.pending_payment_frame = Frame(self.tabs["payments"])
        self.payment_data_frame(self.pending_payment_frame).pack()
        self.payment_posibles_frame(self.pending_payment_frame, "editable_posibles").pack()
        Button(self.pending_payment_frame, text="Cerrar", command=self.show_payments_tree).pack()

        self.tabs["payments"].pack()

    def open_payment_data_frame(self, event):
        self.load_payment_from_tree()
        if self.search_payments_estado == "PENDIENTE":
            self.payment_posibles_load("editable_posibles")
            self.show_pending_payment()
        else:
            self.payment_posibles_load("posibles")
            self.show_payment()

    def validate_dni(self):
        dni = self.get_var("paysearch.customer_id").get()
        try:
            dni = calcular_y_formatear_letra_dni(dni)
        except ValueError:
            dni = formatear_letra_dni(dni)
        self.set_var("paysearch.customer_id", dni)

    def load_payment_from_tree(self, *args, **kwargs):
        category = "pagos"
        tree = self.tree[category]["tree"]
        selection = tree.selection()
        if len(selection) > 0:
            item = tree.selection()[0]
            data = API.get_link(self.tree[category]["data"][item]["_links"]["self"]["href"], var="pagos")
            for column in PAYMENTS_FIELDS:
                if column in data:
                    name = "pagos.{}".format(column)
                    if column in self.tree["pagos"]["show"]:
                        data[column] = self.tree["pagos"]["show"][column](data[column])
                    if column == "posibles":
                        if type(data[column]) in (str, bytearray):
                            data[column] = json.loads(data[column])
                    self.set_var(name, data[column],
                                 w=lambda *args, **kwargs: API.pagos["active"].__setitem__(column, data[column]))
            for parent in (self.payment_frame, self.pending_payment_frame):
                self.payment_data_frame_text[parent]["state"] = "normal"
                self.payment_data_frame_text[parent].delete("1.0", END)
                self.payment_data_frame_text[parent].insert("1.0", self.get_var("pagos.observaciones").get())
                self.payment_data_frame_text[parent]["state"] = "disable"

    def search_payment(self, *args, **kwargs):
        estado = self.get_var("paysearch.state").get()
        self.search_payments_estado = estado
        dni = self.get_var("paysearch.customer_id").get()
        oficina = self.get_var("paysearch.office").get()
        fecha = self.get_var("paysearch.pay_date").get()
        importe = self.get_var("paysearch.amount").get().replace(" ",
                                                                   "").replace(".", "").replace(",", "").replace("\u20ac", "")
        kwargs = dict()
        if estado != "" and estado in admin_config.PAYMENTS_STATES:
            kwargs["estado"] = estado
        if dni != "":
            try:
                kwargs["dni"] = calcular_y_formatear_letra_dni(dni)
            except ValueError:
                kwargs["dni"] = formatear_letra_dni(dni)
        if oficina != "":
            try:
                int(oficina)
            except ValueError:
                pass #TODO: Actualizar NADA
            else:
                kwargs["oficina"] = oficina
        if fecha != "":
            kwargs["fecha"] = fecha #TODO: Validate
        if importe != "":
            kwargs["importe"] = importe
        self.update_pagos_tree(**kwargs)

    def update_pagos_tree(self, link=None, **filter):
        if link is None:
            API.filter_pagos(link, **filter)
            pagos = API.get_pagos_list()
        else:
            pagos = API.get_pagos_list(link) #TODO: fix this shit
        pagos_dict = dict()
        if pagos:
            for pago in pagos:
                if "_id" in pago:
                    pagos_dict[str(pago["_id"])] = pago
        order = [int(key) for key in pagos_dict.keys()]
        order.sort()
        self.set_tree_data("pagos", pagos_dict, order=[str(key) for key in order])
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

    def show_payments_tree(self, *args, **kwargs):
        self.pending_payment_frame.pack_forget()
        self.payment_frame.pack_forget()
        self.payments_tree_frame.pack()

    def show_payment(self, *args, **kwargs):
        self.payments_tree_frame.pack_forget()
        self.payment_frame.pack()

    def show_pending_payment(self, *args, **kwargs):
        self.payments_tree_frame.pack_forget()
        self.pending_payment_frame.pack()

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
        Label(servidor, text="Filas por página: ").grid(column=0, row=2, columnspan=2)
        self.Entry("config.ITEMS_PER_PAGE",
                   servidor).grid(column=4, row=2, columnspan=1)

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
        self.set_var("config.ITEMS_PER_PAGE", local_config.ITEMS_PER_PAGE)

    def set_variables(self):
        self.search_payments_estado = str()
        self._pending = 0
        self._pending_variable = self.set_var("pagos.importe_pendiente")
        self.posibles_headers = ["fecha_aplicacion",
                                 "codigo",
                                 "nombre",
                                 "dni",
                                 "id_factura",
                                 "fecha_operacion",
                                 "importe",
                                 "periodo_facturado",
                                 "metodo",
                                 "via"]
        self.posibles_columns = ["dni",
                                 "nombre",
                                 "id_factura",
                                 "importe",
                                 "periodo_facturado"]
        for item in PAYMENTS_FIELDS:
            self.set_var(".".join(("pagos", item)))


if __name__ == "__main__":
    root = Tk()
    app = App(root)
    app.mainloop()
