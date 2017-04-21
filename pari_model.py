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
        self.set_shelve()
        try:
            self._loaded_file = self.shelf["file"]
        except KeyError:
            self._loaded_file = None
        self.name = None

    @log
    def set_shelve(self): # To implement metadata
        self._shelf = shelve.open(self.filepath)

    @property
    def filepath(self):
        return self._filepath

    @property
    def shelf(self):
        return self._shelf

    @property
    def loaded_file(self):
        return self._loaded_file

    @property
    def items_per_page(self):
        return 50

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
        API_numdocs = {"_heads": ["id_cuenta"]}
        limit_date = datetime.datetime.strptime(
            (datetime.datetime.now() - datetime.timedelta(days=92)).strftime("%d%m%Y"),
            "%d%m%Y").date()
        total = int()
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
                              "segmentos": index_segmentos}}
            if (row["data"]["estado_recibo"] in ("IMPAGADO", "PAGO PARCIAL") or
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
                                API_numdocs.update({numdoc: id_cliente})
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
                            if row["data"][head] not in index_facturas:
                                index_facturas[fecha] = set() #id_factura
                                index_facturas[fecha] |= {id_factura}
                        else:
                            api["data"][item][index] = row["data"][head]
                total += 1
            if "eta" in row:
                yield row
        self.shelf.update(final)
        path, name = os.path.split(pari_file)
        self.shelf["file"] = name
        self.shelf["total"] = total
        self._loaded_file = name

    @log
    def replace(self, filter, data, **kwargs):
        if self.loaded_file is not None and "file" in data and os.path.exists(data["file"]):
            self.drop(filter, **kwargs)
            self.new(data, **kwargs)
        #TODO: Reenviar algo si no hay nada

    @log
    def drop(self, filter, **kwargs):
        if self.loaded_file is not None:
            self._loaded_file = None
            self.shelf.close()
            for file in glob.glob("{}.*".format(self.filepath)):
                os.remove(file)
            self.set_shelve()
            return {"filepath": self.filepath,
                    "data": {"pari": {"data": [],
                                      "total": self.shelf["total"],
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
            filepath = data["file"]
            data = list(self.shelf["id_factura"]["data"].keys())
            data.sort()
            data = [{"id_factura": factura} for factura in data[:self.items_per_page]]
            return {"filepath": filepath,
                    "data": {"pari": {"data": data,
                                      "total": self.shelf["total"],
                                      "page": 1,
                                      "items_per_page": self.items_per_page}
                             },
                    "total": 1,
                    "page": 1,
                    "items_per_page": self.items_per_page}
        # TODO: Reenviar algo si no hay nada

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
