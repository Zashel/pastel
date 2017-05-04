import requests
import pprint
from definitions import *
from zashel.utils import log, daemonize
from zrest.datamodels.shelvemodels import ShelveModel

import datetime
import sys
import shelve
import glob
import os
import re
import json
import time
if sys.version_info.minor == 3:
    from contextlib import closing
    shelve_open = lambda file, flag="c", protocol=None, writeback=False: closing(shelve.open(file, flag))
else:
    shelve_open = shelve.open

class API:
    basepath = "http://{}:{}/{}".format(local_config.HOST, str(local_config.PORT), BASE_URI[1:-1].strip("/"))
    id_factura = {"_heads": ["fecha_factura",
                            "importe_adeudado",
                            "estado_recibo",
                            "id_cuenta"]}
    id_cuenta = {"_heads": ["id_cliente",
                            "segmento",
                            "facturas"]}
    id_cliente = {"_heads": ["numdoc",
                             "id_cuenta"]}
    segmentos = list()
    estados = list()
    procesos = {}
    procesos_done = list()

    @classmethod
    @daemonize
    def run(cls):
        today = datetime.datetime.now()
        tomorrow = today + datetime.timedelta(days=1)
        next_set_pari = tomorrow
        next_set_pari = next_set_pari.replace(hour=6, minute=50, second=0, microsecond=0)
        API.procesos.update({next_set_pari: {"function": API.set_pari,
                                             "args": [],
                                             "kwargs": {},
                                             "repeat": datetime.timedelta(days = 1)}})
        while True:
            for fecha in API.procesos:
                if fecha <= datetime.datetime.now():
                    proceso = API.procesos[fecha]
                    proceso["function"](*proceso["args"], **proceso["kwargs"])
                    API.procesos_done.append(fecha)
            for fecha in API.procesos_done:
                if API.procesos[fecha]["repeat"] is not None:
                    API.procesos[fecha+API.procesos[fecha]["repeat"]] = API.procesos[fecha].copy()
                    del(API.procesos[fecha])
            API.procesos_done = list()
            time.sleep(60)

    @classmethod
    def log_error(cls, function, aditional_dict, file=LOG_ERROR):
        with open(file, "a") as logger:
            to_log = "{} - API.{}:\n\t{}\n".format(datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S"),
                                                 function.__name__,
                                                 pprint.pformat(aditional_dict))
            logger.write(to_log)

    @classmethod
    def set_n43(cls, filename):
        data = requests.put("http://{}:{}{}/n43".format(local_config.HOST,
                                                             str(local_config.PORT),
                                                             BASE_URI[1:-1]),
                            json={"file": filename})
        data = json.loads(data.text)
        if "data" in data and "manuals" in data["data"]:
            for payment in data["data"]["manuals"]:
                requests.post("http://{}:{}{}/pagos".format(local_config.HOST,
                                                         str(local_config.PORT),
                                                         BASE_URI[1:-1]),
                              json={"fecha": payment["fecha_operacion"],
                                    "importe": payment["importe"],
                                    "observaciones": payment["observaciones"],
                                    "dni": payment["nif"],
                                    "id_cliente": payment["id_cliente"],
                                    "tels": payment["telefonos"],
                                    "oficina": payment["oficina_origen"],
                                    "posibles": payment["posibles"],
                                    "estado": "PENDIENTE"
                                    })
        return data

    @classmethod
    def set_pari(cls):
        files =  glob.glob("{}*.csv".format(os.path.join(admin_config.N43_PATH_INCOMING, "BI_131_FICHERO_PARI_DIARIO")))
        files.sort()
        files.reverse()
        print(files)
        if len(files) > 0:
            data = requests.put("http://{}:{}{}/facturas".format(local_config.HOST,
                                                                 str(local_config.PORT),
                                                                 BASE_URI[1:-1]),
                                json = {"file": files[0]})
            data = json.loads(data.text)["data"]
            ife = data["importes por fechas y estados"]
            ffe = data["facturas por fechas y estados"]
            dfe = data["devoluciones por fechas y estados"]
            segmentos = list(ife.keys())
            segmentos.sort()
            assert len(segmentos) > 0
            fechas = list(ife[segmentos[0]].keys())
            fechas.sort()
            assert len(fechas) > 0
            estados = list(ife[segmentos[0]][fechas[0]].keys())
            estados.sort()
            assert len(estados) > 0
            heads = "segmento;fecha_factura;estado;facturas;importe_devuelto;importe_impagado\n"
            name = os.path.split(files[0])[1].strip("BI_131_FICHERO_PARI_DIARIO")
            name = "report_pari_{}".format(name)
            with open(os.path.join(admin_config.REPORT_PATH, "Pari", name), "w") as f:
                f.write(heads)
                for segmento in segmentos:
                    for fecha in fechas:
                        for estado in estados:
                            fecha_str = datetime.datetime.strptime(fecha, "%d/%m/%y").strftime("%d/%m/%Y")
                            facturas = str(ffe[segmento][fecha][estado])
                            importe_devuelto = str(dfe[segmento][fecha][estado])
                            importe_devuelto = "{},{}".format(importe_devuelto[:-2], importe_devuelto[-2:])
                            importe_impagado = str(ife[segmento][fecha][estado])
                            importe_impagado = "{},{}".format(importe_impagado[:-2], importe_impagado[-2:])
                            f.write(";".join((segmento,
                                              fecha_str,
                                              estado,
                                              facturas,
                                              importe_devuelto,
                                              importe_impagado
                                              ))+"\n")
            return os.path.join(admin_config.REPORT_PATH, "Pari", name)

    @classmethod
    def export_unpaid_by_invoice_date(cls, dates):
        format = "%d/%m/%y"
        finaldates = list()
        if not isinstance(dates, list) and not isinstance(dates, tuple):
            dates = [dates]
        for date in dates:
            if isinstance(date, datetime.datetime) or isinstance(date, datetime.date):
                date = date.strftime(format)
            elif isinstance(dates, str):
                try:
                    date = datetime.datetime.strptime("%d/%m/%y")
                except ValueError:
                    try:
                        date = datetime.datetime.strptime("%d/%m/%Y")
                    except ValueError:
                        raise
                else:
                    date = date.strftime(format)
            try:
                finaldates.append(date)
            except UnboundLocalError:
                raise ValueError
        finaldates = ",".join(finaldates)
        return requests.get(
                "http://{}:{}{}/facturas?fecha_factura={}&estado_recibo=IMPAGADO&items_per_page=1000".format(local_config.HOST,
                                                                                                            str(local_config.PORT),
                                                                                                            BASE_URI[1:-1],
                                                                                                            finaldates),
                            headers = {"Content-Type": "text/csv; charset=utf-8"}).text


