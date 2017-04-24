from zrest.basedatamodel import RestfulBaseInterface
import gc
import shelve
import os
from definitions import *
import datetime
from zashel.utils import log
from math import ceil
import glob


class Pari(RestfulBaseInterface):
    def __init__(self, filepath):
        super().__init__()
        self._filepath = filepath
        path, filename = os.path.split(self.filepath)
        if not os.path.exists(path):
            os.makedirs(path)
        self.set_shelve("c")
        self.shelf.close()
        self.set_shelve()
        try:
            self._loaded_file = self.shelf["file"]
        except KeyError:
            self._loaded_file = None
        self.name = None
        self.list_data = dict()
        self.page = 1
        self.items_per_page = 50
        try:
            self.all = self.shelf["all"]
        except KeyError:
            self.all = set()
        self.ids_facturas = None
        self.total_query = int()
        self.filter = None

    @log
    def set_shelve(self, flag="r"): # To implement metadata
        self._shelf = shelve.open(self.filepath, flag)

    @property
    def filepath(self):
        return self._filepath

    @property
    def shelf(self):
        return self._shelf

    @property
    def loaded_file(self):
        return self._loaded_file

    def headers(self):
        return PARI_FIELDS

    @log
    def read_pari(self, pari_file):
        assert os.path.exists(pari_file)
        begin = datetime.datetime.now()
        total_bytes = os.stat(pari_file).st_size
        read_bytes = int()
        last = 0.0000
        info = False
        with open(pari_file, "r") as pari:
            headers = pari.readline().strip("\n").split("|")
            for line in pari:
                read_bytes += len(bytearray(line, "utf-8"))+1
                percent = read_bytes/total_bytes
                if percent >= last:
                    last += 0.0001
                    info = True
                row = line.strip("\n").split("|")
                final = dict()
                for key in PARI_FIELDS:
                    if key.upper() in headers:
                        final[key] = row[headers.index(key.upper())]
                #final["ciclo_facturado"] = API.get_billing_period(final["fecha_factura"])
                if info is True:
                    time = datetime.datetime.now() - begin
                    yield {"percent": round(percent, 4),
                           "time": time,
                           "eta": (time/percent)-time,
                           "data": final}
                    info = False
                else:
                    yield {"data": final}

    @log
    def set_pari(self, pari_file):
        API_id_factura = {"_heads": ["fecha_factura",
                                     "importe_adeudado",
                                     "estado_recibo",
                                     "id_cuenta"],
                          "data": dict()}
        API_id_cuenta = {"_heads": ["segmento",
                                    "facturas",
                                    "id_cliente"],
                          "data": dict()}
        API_id_cliente = {"_heads": ["numdoc",
                                     "id_cuenta"],
                          "data": dict()}
        #API_numdoc = {"_heads": ["numdoc",
        #                         "id_cliente"]}
        API_segmentos = list()
        index_segmentos = dict()
        API_estados = list()
        index_estados = dict()
        index_facturas = dict()
        API_numdocs = {"_heads": ["id_cuenta"],
                       "data": dict()}
        limit_date = datetime.datetime.strptime(
            (datetime.datetime.now() - datetime.timedelta(days=92)).strftime("%d%m%Y"),
            "%d%m%Y").date()
        total = int()
        self.all = set()
        for row in self.read_pari(pari_file):
            id_factura = int(row["data"]["id_factura"])
            id_cuenta = int(row["data"]["id_cuenta"])
            id_cliente = int(row["data"]["id_cliente"])
            numdoc = row["data"]["numdoc"]
            final = {"id_cliente": API_id_cliente,
                     "id_cuenta": API_id_cuenta,
                     "id_factura": API_id_factura,
                     "numdoc": API_numdocs,
                     "estados": API_estados,
                     "segmentos": API_segmentos,
                     "index":{"estados": index_estados,
                              "segmentos": index_segmentos,
                              "fecha_factura": index_facturas}}
            if (row["data"]["estado_recibo"] == "IMPAGADO" or
                        datetime.datetime.strptime(row["data"]["fecha_factura"], "%d/%m/%y").date() >= limit_date):
                for name, item, api in (("id_factura", id_factura, API_id_factura),
                                        ("id_cuenta", id_cuenta, API_id_cuenta),
                                        ("id_cliente", id_cliente, API_id_cliente)):
                    heads = api["_heads"]
                    if item not in api:
                        api["data"][item] = [None for item in heads]
                    for index, head in enumerate(heads):
                        if head in ("id_factura",
                                    "id_cliente",
                                    "id_cuenta"):
                            if head == "id_cliente":
                                API_numdocs["data"].update({numdoc: [id_cliente]})
                            api["data"][item][index] = {"id_factura": id_factura,
                                                        "id_cliente": id_cliente,
                                                        "id_cuenta": id_cuenta}[head]
                        elif head == "facturas":
                            if api["data"][item][index] is None:
                                api["data"][item][index] = list()
                                api["data"][item][index].append(id_factura)
                        elif head == "importe_adeudado":
                            api["data"][item][index] = int(row["data"][head].replace(",", ""))
                        elif head == "segmento":
                            if row["data"][head] not in API_segmentos:
                                API_segmentos.append(row["data"][head])
                            if row["data"][head] not in index_segmentos:
                                index_segmentos[row["data"][head]] = set() #id_cliente
                            index_segmentos[row["data"][head]] |= {id_cliente}
                            segmento = API_segmentos.index(row["data"][head])
                            api["data"][item][index] = segmento.to_bytes(ceil(segmento.bit_length() / 8), "big")
                        elif head == "estado_recibo":
                            if row["data"][head] not in API_estados:
                                API_estados.append(row["data"][head])
                            if row["data"][head] not in index_estados:
                                index_estados[row["data"][head]] = set() #id_factura
                                index_estados[row["data"][head]] |= {id_factura}
                            estado = API_estados.index(row["data"][head])
                            api["data"][item][index] = estado.to_bytes(ceil(estado.bit_length() / 8), "big")
                        elif head == "fecha_factura":
                            fecha = datetime.datetime.strptime(row["data"][head], "%d/%m/%y")
                            fecha = int(fecha.strftime("%d%m%y"))
                            fecha = fecha.to_bytes(ceil(fecha.bit_length() / 8), "big")
                            api["data"][id_factura][index] = fecha
                            if fecha not in index_facturas:
                                index_facturas[fecha] = set() #id_factura
                            index_facturas[fecha] |= {id_factura}
                        else:
                            api["data"][item][index] = row["data"][head]
                self.all |= {id_factura}
                total += 1
            if "eta" in row:
                yield row
        self.shelf.close()
        self.set_shelve("c")
        self.shelf.update(final)
        path, name = os.path.split(pari_file)
        self.shelf["file"] = name
        self.shelf["total"] = total
        self.shelf["all"] = self.all
        self._loaded_file = name
        self.shelf.close()
        self.set_shelve()

    @log
    def replace(self, filter, data, **kwargs):
        if "file" in data and os.path.exists(data["file"]):
            self.drop(filter, **kwargs)
            return self.new(data, **kwargs)
        #TODO: Reenviar algo si no hay nada

    @log
    def drop(self, filter, **kwargs):
        if self.loaded_file is not None:
            self._loaded_file = None
            self.shelf.close()
            for file in glob.glob("{}.*".format(self.filepath)):
                os.remove(file)
            self.set_shelve("c")
            self.shelf.close()
            self.set_shelve()
            return {"filepath": self.filepath,
                    "data": {"pari": {"data": [],
                                      "total": 0,
                                      "page": 1,
                                      "items_per_page": self.items_per_page}
                             },
                    "total": 1,
                    "page": 1,
                    "items_per_page": self.items_per_page}
    @log
    def new(self, data, **kwargs):
        if self.loaded_file is None and "file" in data and os.path.exists(data["file"]):
            for item in self.set_pari(data["file"]):
                print("\r{0:{w}}".format(str(item["eta"]), w=79, fill=" "), end="")
            print()
        #return self.fetch({})
        return ""

    @log
    def fetch(self, filter, **kwargs):
        if not self.loaded_file:
            return {"filepath": "",
                    "data": {"pari": {"data": [],
                                      "total": 0,
                                      "page": 1,
                                      "items_per_page": self.items_per_page}
                             },
                    "total": 1,
                    "page": 1,
                    "items_per_page": self.items_per_page }
        else:
            main_indexes = ("id_factura", "id_cuenta", "id_cliente", "numdoc")
            if self.list_data == dict() or self.filter != filter:
                shelf = dict(self.shelf)
                self.list_data = dict()
                self.filter = filter
                if "fecha_factura" in filter:
                    fechas_factura = filter["fecha_factura"].split(",")
                    filters = [filter.copy() for fecha_factura in fechas_factura]
                    [filter.update({"fecha_factura": fecha_factura}) for fecha_factura in fechas_factura]
                else:
                    filters = [filter]
                template = {"numdoc": None,
                            "id_cliente": None,
                            "id_cuenta": None,
                            "segmento": None,
                            "id_factura": None,
                            "fecha_factura": None,
                            "importe_adeudado": None,
                            "estado_recibo": None
                            }
                self.total_query = int()
                self.ids_facturas = None
                gc.collect()
                if any(index in filter for index in main_indexes): #TODO: Redo
                    for index, id in enumerate(main_indexes):
                        if id in filter:
                            data = template.update()
                            try:
                                data.update(dict(zip(shelf[id]["_heads"],
                                                     shelf[id]["data"][filter[id]])))
                            except ValueError:
                                pass
                            else:
                                while any(data[key] is None for key in template):
                                    for subfilter in main_indexes:
                                        if subfilter in data and data[subfilter] is not None:
                                            data.update(dict(zip(shelf[subfilter]["_heads"],
                                                                 shelf[subfilter]["data"][data[subfilter]])))
                                if "facturas" in data and "id_factura" not in filter:
                                    subdata = data.copy()
                                    del(subdata["facturas"])
                                    for id_factura in data["facturas"]:
                                        subdata.update(dict(zip(shelf[subfilter]["_heads"],
                                                                shelf["id_factura"]["data"][id_factura])))
                                        subdata = self.friend_fetch(subdata)
                                        if any([all([filter[field] == data[field] for field in data if field in filter])
                                                for filter in filters]):
                                            del (subdata["facturas"])
                                            self.list_data[self.total_query] = subdata.copy()
                                            self.total_query += 1
                                else:
                                    subdata = self.friend_fetch(data.copy())
                                    if any([all([filter[field] == data[field] for field in data if field in filter])
                                            for filter in filters]):
                                        self.list_data[self.total_query] = subdata
                                        self.total_query += 1
                                break
                elif self.ids_facturas is None:
                    self.ids_facturas = self.all.copy()
                    for filter in filters:
                        ids = self.all.copy()
                        if "estado_recibo" in filter and filter["estado_recibo"] in shelf["estados"]:
                            ids &= shelf["index"]["estados"][filter["estado_recibo"]]
                        elif "fecha_factura" in filter and filter["fecha_factura"] in shelf["fecha_factura"]:
                            ids &= shelf["index"]["fecha_factura"][filter["fecha_factura"]]
                        elif "segmentos" in filter and filter["segmentos"] in shelf["segmentos"]:
                            ids &= shelf["index"]["segmentos"][filter["segmentos"]]
                        else:
                            ids = set()
                        self.ids_facturas |= ids
                    self.ids_facturas = list(self.ids_facturas)
                    self.ids_facturas.reverse() #From newer to older
                    self.total_query = len(self.ids_facturas)
            else:
                pass
            if "page" in filter:
                self.page = filter["page"]
            else:
                self.page = 1
            if "items_per_page" in filter:
                self.items_per_page = filter["items_per_page"]
            else:
                self.items_per_page = 50
            len_data = len(self.list_data)
            ini = (self.page - 1) * self.items_per_page
            end = self.page * self.items_per_page
            if self.ids_facturas is not None and self.total_query > len_data:
                if end >= len(self.ids_facturas):
                    end = len(self.ids_facturas)
                for index, id_factura in enumerate(self.ids_facturas[ini:end]):
                    if ini+index not in self.list_data:
                        data = template.copy()
                        data["id_factura"] = id_factura
                        print(id_factura)
                        while any(data[key] is None for key in template):
                            for subfilter in main_indexes:
                                if subfilter in data and data[subfilter] is not None:
                                    data.update(dict(zip(shelf[subfilter]["_heads"],
                                                             shelf[subfilter]["data"][data[subfilter]])))
                            print(data)
                        self.list_data[ini+index] = self.friend_fetch(data.copy())
            try:
                del(shelf)
            except UnboundLocalError:
                pass
            gc.collect()
            return {"data": [self.list_data[index] for index in range(ini, end)],
                    "total": self.total_query,
                    "page": self.page,
                    "items_per_page": self.items_per_page}

    def friend_fetch(self, data):
        try:
            del(data["facturas"])
        except KeyError:
            pass
        data["fecha_factura"] = str(int.from_bytes(data["fecha_factura"], "big"))
        while len(data["fecha_factura"]) < 6:
            data["fecha_factura"] = "0" + data["fecha_factura"]
        fecha = data["fecha_factura"]
        data["fecha_factura"] = datetime.datetime.strptime(fecha, "%d%m%y").strftime("%d/%m/%y")
        data["segmento"] = self.shelf["segmentos"][int.from_bytes(data["segmento"], "big")]
        data["estado_recibo"] = self.shelf["estados"][int.from_bytes(data["estado_recibo"], "big")]
        return data