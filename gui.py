from tkinter import *
from tkinter.ttk import *
from api import API
from functools import partial
from definitions import local_config, admin_config, LOCAL, SHARED, PAYMENTS_FIELDS
from tkutils import *
from utils import *
from zashel.utils import threadize, daemonize
import getpass
import json
import os
import datetime

VERSION = "Beta"

class Images:
    def __init__(self):
        self.add = PhotoImage(file=os.path.join("icons", "add.gif"))
        self.remove = PhotoImage(file=os.path.join("icons", "remove.gif"))
        self.check = PhotoImage(file=os.path.join("icons", "check.gif"))


class StarredList(list):
    def __contains__(self, item):
        value = list.__contains__(self, item)
        if value is False and isinstance(item, str) is True and item.endswith("*"):
            key = item[:-1]
            for l_item in self:
                if isinstance(l_item, str) is True and l_item.startswith(key):
                    value = True
                    break
        return value


class App(EasyFrame):
    def __init__(self, master=None):
        super().__init__(master=master, padding=(3, 3, 3, 3), name="pastel")
        self.pack()
        self.set_var("config.nombre_usuario", "")
        self.permissions = {"Operador": StarredList(["pagos_busqueda.*",
                                                     "pagos.botones.cerrar",
                                                     "pagos_pendientes.botones.cerrar"])}
        self.permissions["BO"] = self.permissions["Operador"] + StarredList(["pagos.datos.estado",
                                                                             "pagos_pendientes.datos.estado",
                                                                             "pagos_pendientes.posibles.*",
                                                                             "pagos_pendientes.botones.guardar",
                                                                             "pagos_pendientes.botones.siguiente"])
        self.permissions["Admin"] = self.permissions["BO"] + StarredList()
        #Widgets
        self.images = Images()
        self.set_variables()
        self.set_menu()
        self.set_widgets()
        #Show Home
        self.show_home()
        #Login
        self.load_user()

    def set_widgets(self):
        self.payment_data_frame_text = dict()
        self.set_payments_tree_frame()
        self.set_manual_review_frame()
        #TABS

    def set_variables(self):
        self.search_payments_estado = str()
        self._pending = 0
        self._pending_variable = self.set_var("pagos.importe_pendiente")
        self._pagos_filter = str()
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
        self.set_var("pagos._id", -1)

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
        self.menu_export = Menu(self.menubar)

        self.menubar.add_cascade(menu=self.menu_file, label="Archivo")
        self.menubar.add_cascade(menu=self.menu_edit, label="Edición")

        self.menu_file.add_cascade(menu=self.menu_new, label="Nuevo")
        self.menu_file.add_cascade(menu=self.menu_open, label="Abrir")
        self.menu_file.add_cascade(menu=self.menu_load, label="Cargar")
        self.menu_file.add_cascade(menu=self.menu_export, label="Exportar")
        self.menu_file.add_separator()
        self.menu_file.add_command(label="Cambiar Usuario")

        self.menu_new.add_command(label="Localización")
        self.menu_new.add_command(label="Pago Pasarela")
        self.menu_new.add_command(label="Usuario")

        self.menu_open.add_command(label="Pagos", command=self.show_payments_tree)
        self.menu_open.add_command(label="Pagos Pendientes",
                                   command=partial(self.go_to_payment_by_state, "PENDIENTE"))
        self.menu_open.add_command(label="Pagos Ilocalizables",
                                   command=partial(self.go_to_payment_by_state, "ILOCALIZABLE"))
        self.menu_open.add_command(label="Revisión Pagos Manuales", command=self.go_to_manual_review)
        self.menu_open.add_command(label="Usuarios")

        self.menu_load.add_command(label="Pagos ISM")
        self.menu_load.add_command(label="PARI...")
        self.menu_load.add_command(label="Último PARI")

        self.menu_export.add_command(label="Manuales de hoy")

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

        # Usuario
        usuario.grid(sticky=(N, S, E, W))
        Label(usuario, text="Login: ").grid(column=0, row=1, sticky=(N, W))
        Label(usuario, text=self.usuario).grid(column=1, row=1, sticky=(N, W))
        Label(usuario, text="Rol: ").grid(column=5, row=1, sticky=(N, E))
        Label(usuario, textvariable=self.get_var("usuario.role")).grid(column=6, row=1, sticky=(N, E,))
        Label(usuario, text="Nombre: ").grid(column=0, row=2, sticky=(N, W))
        self.Entry("config.nombre_usuario",
                   usuario).grid(column=1, row=2, columnspan=5, sticky=(N, E))

        # Servidor
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

        # Rutas
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
        # Datos

        notebook.add(usuario, text="Usuario")
        notebook.add(servidor, text="Servidor")
        notebook.add(rutas, text="Rutas")
        # notebook.add(datos, text="Datos")

        # Botones
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

    #Frames
    def payment_data_frame(self, parent):
        row = 0
        # Frame
        frame = Frame(parent, name="datos")
        #Objects:
        LabelEntry = partial(self.LabelEntry, entrykwargs={"state": "readonly"})
        LabelEntry("pagos.fecha", "Fecha Pago: ", frame, name="fecha").grid(column=0, row=row)
        LabelEntry("pagos.oficina", "Oficina: ", frame, name="oficina").grid(column=1, row=row)
        LabelEntry("pagos.importe", "Importe: ", frame, name="importe").grid(column=2, row=row)
        row += 1
        LabelEntry("pagos.dni", "DNI: ", frame, name="dni").grid(column=0, row=row)
        LabelEntry("pagos.id_cliente", "Id_Cliente: ", frame, name="id_cliente").grid(column=1, row=row)
        LabelEntry("pagos.tels", "Teléfonos", frame, name="tels").grid(column=2, row=row)
        row += 1
        Text(frame, width=80, height=5, state="disable", name="observaciones").grid(column=0, row=row, columnspan=3)
        row += 1
        LabelEntry("pagos.importe_pendiente", "Importe Sin Asociar: ",
                   frame, name="importe_pendiente").grid(column=1, row=row)
        self.Combobox("pagos.estado", admin_config.PAYMENTS_STATES, frame, name="estado").grid(column=2, row=row) #frame is the name of the bunny
        return frame

    def payment_posibles_frame(self, parent, name):
        frame = Frame(parent, name="posibles")
        row = 0
        columnspan = 4
        if "editable" in name:
            editable = ["dni", "nombre", "id_factura", "importe", "periodo_facturado"]
            comboboxes = {"periodo_facturado": self.set_list_codes()}
        else:
            editable = list()
            comboboxes = dict()
        default_config = {"columns": {"width": 100},
                          "column": {"#0": {"width": 30},
                                     "periodo_facturado": {"width": 150},
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
                          "editable": editable,
                          "comboboxes": comboboxes
                          }
        tree = self.TreeView(name, self.posibles_columns, frame, default_config=default_config,
                             yscroll=True, name="vista")
        if "editable" in name:
            self.set_tree_calculation(name, partial(self.calculate_pending, name))
        tree.grid(column=0, row=row, columnspan=columnspan)
        if "editable" in name:
            row += 1
            button_frame = Frame(frame, name="botones")
            button_frame.grid(column=3, row=row, sticky=E)
            self.ImageButton(button_frame, self.images.remove, name="remove",
                             command=self.del_selected_item_in_posibles).grid(column=0, row=0, sticky=E)
            self.ImageButton(button_frame, self.images.check, name="check",
                             command=self.add_pending_to_selected).grid(column=1, row=0, sticky=E)
            self.ImageButton(button_frame, self.images.add, name="add",
                             command=self.add_new_row_to_posibles).grid(column=2, row=0, sticky=E)
        return frame

    #Setting Frames
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
        payments_tree_frame = Frame(self, name="pagos_busqueda")
        payments_tree_frame.pack()
        row = 0
        # Payment search
        Label(payments_tree_frame, text="Estado: ").grid(column=0, row=row, sticky="e")
        self.Combobox("paysearch.state", admin_config.PAYMENTS_STATES,
                      payments_tree_frame, name="estado").grid(column=1, row=row, sticky="w")
        self.LabelEntry("paysearch.customer_id", "DNI: ", payments_tree_frame, name="dni").grid(column=2,
                                                                                                row=row) #TODO: Do a phone searching
        Button(payments_tree_frame,
               text="Buscar",
               command=self.search_payment,
               name="buscar"
               ).grid(column=3, row=row)
        row += 1
        #Button(self.payments_tree_frame,
        #       text="CalcularDNI",
        #       command=self.validate_dni,
        #       ).grid(column=4, row=row)
        row += 1
        self.LabelEntry("paysearch.pay_date", "Fecha: ",
                        payments_tree_frame, name="fecha").grid(column=0, row=row, columnspan=2)
        self.LabelEntry("paysearch.office", "Oficina: ",
                        payments_tree_frame, name="oficina").grid(column=2, row=row)
        self.LabelEntry("paysearch.amount", "Importe: ",
                        payments_tree_frame, name="importe").grid(column=3, row=row)
        row += 1
        payments_tree = self.TreeView("pagos",
                                      columns,
                                      payments_tree_frame,
                                      default_config=default_config,
                                      yscroll=True,
                                      name="vista")
        self.tree["pagos"]["tree"].bind("<Double-1>", self.open_payment_data_frame)
        payments_tree.grid(column=0, row=row, columnspan=5)
        payments_tree_first = self.LinkButton(payments_tree_frame,
                                              command=lambda: self.update_pagos_tree("first"),
                                              text="Primero",
                                              state="disable",
                                              name="first")
        row += 1
        payments_tree_first.grid(column=0, row=row)
        payments_tree_prev = self.LinkButton(payments_tree_frame,
                                             command=lambda: self.update_pagos_tree("prev"),
                                             text="Anterior",
                                             state="disable",
                                             name="prev")
        payments_tree_prev.grid(column=1, row=row)
        Label(payments_tree_frame, text="Página 1 de 1.\t0 Registros", name="informacion").grid(column=2, row=row)
        payments_tree_next = self.LinkButton(payments_tree_frame,
                                             command=lambda: self.update_pagos_tree("next"),
                                             text="Siguiente",
                                             state="disable",
                                             name="next")
        payments_tree_next.grid(column=3, row=row)
        payments_tree_last = self.LinkButton(payments_tree_frame,
                                             command=lambda: self.update_pagos_tree("last"),
                                             text="Último",
                                             state="disable",
                                             name="last")
        payments_tree_last.grid(column=4, row=row)
        row += 1

        #Payment Frame
        payment_frame = Frame(self, name="pagos")
        self.payment_data_frame(payment_frame).pack()
        self.payment_posibles_frame(payment_frame, "posibles").pack()
        button_frame_payment = Frame(payment_frame, name="botones")
        button_frame_payment.pack()
        Button(button_frame_payment, text="Cerrar", command=self.show_payments_tree, name="cerrar").pack()

        #Pending Payment Frame
        pending_payment_frame = Frame(self, name="pagos_pendientes")
        self.payment_data_frame(pending_payment_frame).pack()
        self.payment_posibles_frame(pending_payment_frame, "editable_posibles").pack()
        button_frame_payment_pending = Frame(pending_payment_frame)
        button_frame_payment_pending.pack()
        Label(button_frame_payment_pending, textvariable=self.set_var("gui.pagos_pendientes"),
              name="informacion").grid(column=0, row=0, sticky=W)
        Button(button_frame_payment_pending, text="Cerrar",
               command=self.show_payments_tree, name="cerrar").grid(column=1, row=0, sticky=E)
        Button(button_frame_payment_pending, text="Guardar",
               command=self.save_pagos_pendiente, name="guardar").grid(column=2, row=0, sticky=E)
        Button(button_frame_payment_pending, text="Siguiente",
               command=self.save_and_next_payment, name="siguiente").grid(column=3, row=0, sticky=E)

    def set_manual_review_frame(self):
        Frame(self, name="pagos_manuales")
        row = 0
        #Label(self.pagos_manuales, text="Estado: ").grid(column=0, row=row, sticky=E)
        #self.Combobox("manualsearch.state", admin_config.PAYMENTS_STATES, self.pagos_manuales).grid(column=1,
        #                                                                                                 row=row,
        #                                                                                                 sticky=W)
        self.LabelEntry("manualsearch.date", "Fecha: ", self.pagos_manuales).grid(column=2,
                                                                                  row=row,
                                                                                  sticky=W,
                                                                                  columnspan=2)
        row+=1
        self.LabelEntry("manualsearch.user", "Usuario: ", self.pagos_manuales).grid(column=0,
                                                                                    row=row,
                                                                                    #sticky=E,
                                                                                    columnspan=2)
        Button(self.pagos_manuales, text="Buscar", command=self.load_review_manuals_tree).grid(column=2,
                                                                                               row=row,
                                                                                               sticky=W,
                                                                                               columnspan=2)
        #self.Checkbutton("manualsearch.reported",
        #                 self.pagos_manuales,
        #                 text="Reportado: ").grid(column=2, row=row, sticky=W, columnspan=2)
        row += 1
        default_config = {"columns": {"width": 75},
                          "heading": {"#0": {"text": "ID"},
                                      "fecha_aplicacion": {"text": "Fecha Aplicación"},
                                      "codigo": {"text": "Código"},
                                      "nombre": {"text": "Nombre"},
                                      "nif": {"text": "DNI"},
                                      "id_factura": {"text": "ID Factura"},
                                      "fecha_pago": {"text": "Fecha de Pago"},
                                      "importe": {"text": "Importe"},
                                      "periodo_facturado": {"text": "Periodo Facturado"},
                                      "metodo": {"text": "Método"},
                                      "via": {"text": "Vía"},
                                      "usuario": {"text": "Usuario"}
                                      }}
        self.TreeView("manual_review", admin_config.PAYMENTS_UPLOADING_HEADERS+["usuario"], self.pagos_manuales,
                      default_config=default_config, yscroll=True, name="vista").grid(column=0, row = row, columnspan=4)

    #Manual Review Related
    def load_review_manuals_tree(self):
        filter = dict()
        self.set_var("manualsearch.state", "APLICADO")
        state = self.get_var("manualsearch.state").get()
        date = self.get_var("manualsearch.date").get()
        user = self.get_var("manualsearch.user").get()
        #reported = self.get_var("manualsearch.reported").get()
        if state != str():
            filter["pagos_estado"] = state
        if date != str():
            filter["manual_fecha"] = date
        if user != str():
            filter["manual_usuario"] = user
        data = API.review_manuals(**filter)
        final = dict()
        index = int()
        for user in data:
            for item in data[user]:
                final[index] = dict(zip(admin_config.PAYMENTS_UPLOADING_HEADERS+["usuario"], item+[user]))
                index += 1
        self.set_tree_data("manual_review", final)

    #Payments related
    def add_new_row_to_posibles(self):
        tree = self.tree["editable_posibles"]["tree"]
        items = tree.get_children()
        if self.get_var("pagos.importe_pendiente").get() != "0,0 \u20ac":
            if len(items) > 0:
                dni = tree.set(items[-1], "dni")
                nombre = tree.set(items[-1], "nombre")
                item = str(int(items[-1])+1)
            else:
                dni = self.get_var("pagos.dni").get()
                nombre = str()
                item = "0"
            data = {"dni":dni,
                    "nombre":nombre,
                    "importe": self.get_var("pagos.importe_pendiente").get().replace(" \u20ac", "")}
            self.append_to_tree_data("editable_posibles", item, data)
            self.calculate_pending("editable_posibles")

    def add_pending_to_selected(self):
        tree = self.tree["editable_posibles"]["tree"]
        item = tree.selection()[0]
        if item != "":
            importe = int(round(float(tree.set(item, "importe").replace(" \u20ac", "").replace(",", "."))*100, 2))
            pendiente = int(round(float(self.get_var("pagos.importe_pendiente").get()
                                        .replace(" \u20ac", "").replace(",", "."))*100, 2))
            nuevo = str((importe + pendiente)/100).replace(".", ",")+" \u20ac"
            #tree.set(item, "importe", nuevo)
            self.set_var("editable_posibles.importe", nuevo.replace(" \u20ac", ""))
            self.calculate_pending("editable_posibles")

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
        if self._pending == 0:
            self.set_var("pagos.estado", "APLICADO")

    def del_selected_item_in_posibles(self):
        self.del_selected_item_in_tree_data("editable_posibles")
        self.calculate_pending("editable_posibles")

    def filter_payment(self, *args, **kwargs):
        estado = self.get_var("paysearch.state").get()
        self.search_payments_estado = estado
        dni = self.get_var("paysearch.customer_id").get()
        oficina = self.get_var("paysearch.office").get()
        fecha = self.get_var("paysearch.pay_date").get()
        importe = self.get_var("paysearch.amount").get().replace(" ",
                                                                 "").replace(".", "").replace(",", "").replace(
            "\u20ac",
            "")
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
                pass  # TODO: Actualizar NADA
            else:
                kwargs["oficina"] = oficina
        if fecha != "":
            kwargs["fecha"] = fecha  # TODO: Validate
        if importe != "":
            kwargs["importe"] = importe
        self._pagos_filter = kwargs
        return kwargs

    def load_payment(self, data):
        for column in PAYMENTS_FIELDS:
            if column in data:
                name = "pagos.{}".format(column)
                if column in self.tree["pagos"]["show"]:
                    data[column] = self.tree["pagos"]["show"][column](data[column])
                if column == "posibles":
                    if type(data[column]) in (str, bytearray):
                        data[column] = json.loads(data[column])
                print(str(data[column]).replace("\u20ac", "Euro"))
                self.set_var(name, data[column],
                             w=lambda *args, **kwargs: API.pagos["active"].__setitem__(column, data[column]))
        link = data["_links"]["self"]["href"]
        self.set_var("pagos.link", link)
        self.set_var("pagos._id", data["_id"])
        for parent in (self.pagos, self.pagos_pendientes):
            text = self["{}.datos.observaciones".format(parent._name)]
            text["state"] = "normal"
            text.delete("1.0", END)
            text.insert("1.0", self.get_var("pagos.observaciones").get())
            text["state"] = "disable"
        if self.search_payments_estado == "PENDIENTE":
            self.payment_posibles_load("editable_posibles")
        else:
            self.payment_posibles_load("posibles")

    def load_payment_from_tree(self, *args, **kwargs):
        category = "pagos"
        tree = self.tree[category]["tree"]
        selection = tree.selection()
        if len(selection) > 0:
            item = tree.selection()[0]
            link = self.tree[category]["data"][item]["_links"]["self"]["href"]
            data = API.get_link(link, var="pagos")
            self.load_payment(data)

    def next_payment(self):
        kwargs = dict(self._pagos_filter)
        kwargs.update({"_item": self.get_var("pagos._id").get()})
        self.load_payment(API.next_pagos(**kwargs))
        @daemonize
        def update():
            try:
                self.set_var("gui.pagos_pendientes", "Quedan {} pagos.".format(API.get_pagos_count(**self._pagos_filter)))
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                pass
        update()

    def open_payment_data_frame(self, event):
        self.load_payment_from_tree()
        if self.search_payments_estado == "PENDIENTE":
            self.show_pending_payment()
            self.set_var("gui.pagos_pendientes", "Quedan {} pagos.".format(API.get_pagos_count(**self._pagos_filter)))
        else:
            self.show_payment()

    def payment_posibles_load(self, name):
        self.clean_pagos_vars()
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
                        val = lambda x: x #TODO
                    final[str(index)][header] = posible[self.posibles_headers.index(header)]
        order.sort()
        self.set_tree_data(name, final, order=[str(key) for key in order])
        self.calculate_pending(name)

    def save_and_next_payment(self):
        self.destroy_popUp()
        link = self.get_var("pagos.link").get()
        tree = self.tree["editable_posibles"]["tree"]
        posibles = list()
        items = tree.get_children()
        codes = admin_config.FACTURAS
        for item in items:
            code = codes[API.get_fecha_factura_from_periodo(tree.set(item, "periodo_facturado"))]
            posibles.append(";".join([datetime.datetime.now().strftime("%d/%m/%Y"),
                                      str(code),
                                      str(tree.set(item, "nombre")),
                                      str(tree.set(item, "dni")),
                                      str(tree.set(item, "id_factura")),
                                      str(self.get_var("pagos.fecha").get()),
                                      str(tree.set(item, "importe").replace(".", ",").replace(" \u20ac", "")),
                                      str(tree.set(item, "periodo_facturado")),
                                      str(admin_config.PM_PAYMENT_METHOD),
                                      str(admin_config.PM_PAYMENT_WAY)
                                      ]))
        estado = self.get_var("pagos.estado").get()
        @threadize
        def save(link, estado, posibles):
            print("Saving")
            API.modify_pago({"link": link, "estado": estado, "posibles": posibles})
            print("Modified Payment")
            API.insert_manual(link)
            print("Inserted Manual")
            API.unblock_pago(link)
            print("Unblocked Pago")
        save(link, estado, posibles) #Repeating myself...
        self.next_payment()

    def save_pagos_pendiente(self):
        self.destroy_popUp()
        link = self.get_var("pagos.link").get()
        tree = self.tree["editable_posibles"]["tree"]
        posibles = list()
        items = tree.get_children()
        codes = admin_config.FACTURAS
        for item in items:
            code = codes[API.get_fecha_factura_from_periodo(tree.set(item, "periodo_facturado"))]
            posibles.append(";".join([datetime.datetime.now().strftime("%d/%m/%Y"),
                                      str(code),
                                      str(tree.set(item, "nombre")),
                                      str(tree.set(item, "dni")),
                                      str(tree.set(item, "id_factura")),
                                      str(self.get_var("pagos.fecha").get()),
                                      str(tree.set(item, "importe").replace(".", ",").replace(" \u20ac", "")),
                                      str(tree.set(item, "periodo_facturado")),
                                      str(admin_config.PM_PAYMENT_METHOD),
                                      str(admin_config.PM_PAYMENT_WAY)
                                      ]))
        @threadize
        def save(link, estado, posibles):
            API.modify_pago({"link": link, "estado": estado, "posibles": posibles})
            API.insert_manual(link)
            API.unblock_pago(link)
        save(link, self.get_var("pagos.estado").get(), posibles)

    def search_payment(self, *args, **kwargs):
        #self.filter_payment()
        self.update_pagos_tree(**self.filter_payment())

    def update_pagos_tree(self, link=None, **filter):
        if link is None:
            API.filter_pagos(link, **filter)
            pagos = API.get_pagos_list()
        else:
            pagos = API.get_pagos_list(link)  # TODO: fix this shit
        pagos_dict = dict()
        if pagos:
            for pago in pagos:
                if "_id" in pago:
                    pagos_dict[str(pago["_id"])] = pago
        order = [int(key) for key in pagos_dict.keys()]
        order.sort()
        self.set_tree_data("pagos", pagos_dict, order=[str(key) for key in order])
        for link in ("first", "prev", "next", "last"):
            self["pagos_busqueda."+link]["state"] = "enable"
        page = API.get_this_pagos_page()
        print("Page: ", str(page))
        last = API.get_total_pagos_page()
        total = API.get_pagos_count(**filter)
        if page == 1:
            self.pagos_busqueda.first["state"] = "disable"
            self.pagos_busqueda.prev["state"] = "disable"
        if page == last:
            self.pagos_busqueda.next["state"] = "disable"
            self.pagos_busqueda.last["state"] = "disable"
        self.pagos_busqueda.informacion["text"] = "Página {} de {}.\t{} Registros".format(str(page), str(last), str(total))

    #GUI
    def hide_everything(self, *args, **kwrags):
        self.pagos_busqueda.pack_forget()
        self.pagos_pendientes.pack_forget()
        self.pagos.pack_forget()
        self.pagos_manuales.pack_forget()

    def go_to_manual_review(self, *args, **kwargs):
        self.hide_everything()
        self.pagos_manuales.pack()

    def go_to_payment_by_state(self, estado, *args, **kwargs):
        self.hide_everything()
        self.set_var("paysearch.customer_id", "")
        self.set_var("paysearch.office", "")
        self.set_var("paysearch.pay_date", "")
        self.set_var("paysearch.amount", "")
        self.set_var("paysearch.state", estado)
        self.filter_payment()
        self.next_payment()
        self.show_payment()

    def show_home(self, *args, **kwargs):
        self.hide_everything()

    def show_payment(self, *args, **kwargs):
        self.hide_everything()
        if self.search_payments_estado == "PENDIENTE":
            self.pagos_pendientes.pack()
        else:
            self.pagos.pack()

    def show_payments_tree(self, *args, **kwargs):
        self.hide_everything()
        self.pagos_busqueda.pack()
        if self._pagos_filter != dict():
            self.update_pagos_tree(**self._pagos_filter)

    def show_pending_payment(self, *args, **kwargs):
        self.hide_everything()
        self.show_payment()

    #Others
    def changed_data(self, var, void, action, var_name): #I don't know if I need it...
        pass

    def clean_pagos_vars(self):
        for item in PAYMENTS_FIELDS:
            self.set_var(".".join(("pagos", "")))

    def activate_all(self):
        for item in self.all_children:
            if item in self.permissions[self.get_var("usuario.role").get()]:
                self.children[item]["state"] = "normal" #This is not easy to do

    def disable_all(self):
        for item in self.children:
            try:
                self.children[item]["state"] = "disable"
            except (KeyError, TclError):
                pass #you fools!

    def load_user(self, user=getpass.getuser()):
        datos_usuario = API.get_usuario(user)
        self.set_var("usuario.id", datos_usuario["id"])
        self.set_var("usuario.role", datos_usuario["role"])
        self.set_var("usuario.fullname", datos_usuario["fullname"])

    def set_last_pari(self):
        self.disable_all()
        file = API.set_pari
        self.activate_all()

    def set_list_codes(self):
        keys = list(admin_config.FACTURAS.keys())
        keys.sort()
        keys.reverse()
        return [API.get_billing_period(key) for key in keys]

    def validate_dni(self):
        dni = self.get_var("paysearch.customer_id").get()
        try:
            dni = calcular_y_formatear_letra_dni(dni)
        except ValueError:
            dni = formatear_letra_dni(dni)
        self.set_var("paysearch.customer_id", dni)


if __name__ == "__main__":
    root = Tk()
    root.title("P.A.S.T.E.L. {}".format(VERSION))
    root.iconbitmap("pastel.ico")
    app = App(root)
    app.mainloop()
