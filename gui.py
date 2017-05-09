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
        self.widgets()
        self.none_dict = {type(str()): "",
                          type(int()): 0,
                          type(float()): 0.0,
                          type(bool()): False}

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
                    pago["posible"][s_index][head].set(datos[dato])

    def set_pagos_list(self, data):
        self.clean_pagos_list()
        for index, item in enumerate(data):
            self._pagos_list[index]["index"].set(index)
            self.set_pago(self.pagos_list[index], item)

    def widgets(self):
        pass

    @property
    def vars(self):
        return self._vars


if __name__ == "__main__":
    root = Tk()
    app = App(root)
    print(app.vars.string.get())
    app.mainloop()