import requests
import pprint
import time
from random import randint
from zashel.utils import threadize

for x in range(5):
    try:
        from definitions import *
        time.sleep(x+randint(5, 10))
        break
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        continue

from zashel.utils import daemonize

import datetime
import sys
import shelve
import glob
import os
import re
import json

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
    server = False

    pagos = {"active": None,
             "cache": None,
             "self": None,
             "next": None,
             "last": None,
             "prev": None,
             "first": None,
             "page": None,
             "total_pages": None
             }

    @classmethod
    def get_pago(cls, _id):
        if API.pagos["active"]["_id"] != _id:
            request = requests.get("http://{}:{}{}/pagos?_id={}".format(local_config.HOST,
                                                                        str(local_config.PORT),
                                                                        BASE_URI[1:-1],
                                                                        str(_id)))
            if request.status_code == 200:
                data = json.loads(request.text)
                if data["total"] == 1:
                    API.pagos["active"] = data["data"]
            elif request.request == 404:
                API.pagos["active"] = None
        return API.pagos["active"]

    @classmethod
    def get_link(self, link, *, var=None):
        request = requests.get("http://{}:{}{}".format(local_config.HOST,
                                                       str(local_config.PORT),
                                                       link))
        if request.status_code == 200:
            data = json.loads(request.text)
            if var is not None:
                if var == "pagos":
                    API.pagos["active"] = data
            return data

    @classmethod
    def filter_pagos(cls, link=None, **kwargs):
        filter = list()
        if "items_per_page" not in kwargs:
            kwargs["items_per_page"] = local_config.ITEMS_PER_PAGE
        for item in kwargs:
            if item in PAYMENTS_INDEX:
                filter.append("=".join((item, str(kwargs[item]))))
        filter = "&".join(filter)
        if link is None:
            request = requests.get("http://{}:{}{}/pagos{}{}".format(local_config.HOST,
                                                                     str(local_config.PORT),
                                                                     BASE_URI[1:-1],
                                                                     filter != list() and "?" or str(),
                                                                     filter
                                                                     ))
        else:
            request = requests.get("http://{}:{}{}".format(local_config.HOST,
                                                              str(local_config.PORT),
                                                              link
                                                              ))
        if request.status_code == 200:
            data = json.loads(request.text)
            if "_embedded" in data:
                API.pagos["cache"] = data["_embedded"]["pagos"]
            else:
                API.pagos["cache"] = [data]
            if "_links" in data:
                for link in ("self", "next", "prev", "first", "last"):
                    if link in data["_links"]:
                        API.pagos[link] = data["_links"][link]["href"]
                        page = re.findall(r"(?<!_)page=([0-9]{1,20})", data["_links"][link]["href"]) #TODO: Review this!
                        if len(page) > 0:
                            page = int(page[0])
                            if link == "self":
                                API.pagos["page"] = page
                            if link == "last":
                                API.pagos["total_pages"] = page
                    else:
                        API.pagos[link] = None
        else:
            print(request.status_code)
            API.pagos = {"active": None,
                         "cache": dict(),
                         "self": None,
                         "next": None,
                         "last": None,
                         "prev": None,
                         "first": None,
                         "page": None,
                         "total_pages": None
                         }

    @classmethod
    def get_this_pagos_page(cls):
        page = API.pagos["page"]
        if page is None:
            page = 1
        return page

    @classmethod
    def get_total_pagos_page(cls):
        if API.pagos["total_pages"] is None:
            return 1
        return API.pagos["total_pages"]

    @classmethod
    def next_pagos(cls, **kwargs):
        filter = list()
        for item in kwargs:
            if item in PAYMENTS_INDEX+["_item"]:
                filter.append("=".join((item, str(kwargs[item]))))
        filter = "&".join(filter)
        request = requests.request("NEXT",
                                   "http://{}:{}{}/pagos?{}".format(local_config.HOST,
                                                                    str(local_config.PORT),
                                                                    BASE_URI[1:-1],
                                                                    filter))
        if request.status_code == 200:
            data = json.loads(request.text)
            if request.status_code == 404:
                API.pagos["active"] = None
            else:
                API.pagos["active"] = data
        return API.pagos["active"]

    @classmethod
    def unblock_pago(cls, link):
        request = requests.get("http://{}:{}{}?unblock=True".format(local_config.HOST,
                                                                             str(local_config.PORT),
                                                                             link.split("?")[0]))

    @classmethod
    def get_pagos_list(cls, link=None):
        if link not in API.pagos:
            return API.pagos["cache"]
        else:
            API.filter_pagos(API.pagos[link])
            return API.get_pagos_list()

    @classmethod
    def modify_pago(cls, data):
        if "link" in data:
            post_data = data.copy()
            del(post_data["link"])
            request = requests.patch("http://{}:{}{}".format(local_config.HOST,
                                                             str(local_config.PORT),
                                                             data["link"]),
                                     json=post_data)
            if request.status_code in (200, 201):
                data = json.loads(request.text)
                if not "total" in data:
                    API.pagos["active"] = data
                elif request.status_code == 404:
                    API.pagos["active"] = None
            return API.pagos["active"]

    @classmethod
    def insert_manual(cls, link, usuario=None, fecha=None):
        if usuario is None:
            usuario = local_config.USER
        if fecha is None:
            fecha = datetime.datetime.now().strftime("%d/%m/%Y")
        request = requests.post("http://{}:{}{}/manual".format(local_config.HOST,
                                                        str(local_config.PORT),
                                                        link.split("?")[0]),
                                json={"usuario": usuario, "fecha":fecha})
        if request.status_code == 201:
            return True
        else:
            return False

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
        data = requests.request("LOAD", 
                                "http://{}:{}{}/n43".format(local_config.HOST,
                                                            str(local_config.PORT),
                                                            BASE_URI[1:-1]),
                                json={"file": filename})
        data = json.loads(data.text)
        if "data" in data and "manuals" in data["data"]:
            payments = list()
            for payment in data["data"]["manuals"]:
                payments.append({"fecha": payment["fecha_operacion"],
                                 "importe": payment["importe"],
                                 "observaciones": payment["observaciones"],
                                 "dni": payment["nif"],
                                 "id_cliente": payment["id_cliente"],
                                 "tels": payment["telefonos"],
                                 "oficina": payment["oficina_origen"],
                                 "posibles": payment["posibles"],
                                 "estado": "PENDIENTE"
                                 })
            requests.request("LOAD",
                             "http://{}:{}{}/pagos".format(local_config.HOST,
                                                           str(local_config.PORT),
                                                           BASE_URI[1:-1]),
                             json=payments)
        return data

    @classmethod
    def get_pagos_count(cls, **filter):
        if filter == dict():
            request = requests.request("COUNT",
                                       "http://{}:{}{}/pagos".format(local_config.HOST,
                                                                     str(local_config.PORT),
                                                                     BASE_URI[1:-1]))
        else:
            request = requests.request("COUNT",
                                       "http://{}:{}{}/pagos?{}".format(local_config.HOST,
                                                                        str(local_config.PORT),
                                                                        BASE_URI[1:-1],
                                                                        "&".join(["=".join((key, filter[key])) for key in filter])))
        data = json.loads(request.text)
        if "count" in data:
            return int(data["count"])

    @classmethod
    def set_pari(cls, filename=None, *, do_report=True, do_export=True):
        if filename is None:
            files =  glob.glob("{}*.csv".format(os.path.join(admin_config.N43_PATH_INCOMING, "BI_131_FICHERO_PARI_DIARIO")))
            files.sort()
            files.reverse()
        else:
            files = [filename]
        if len(files) > 0:
            data = requests.put("http://{}:{}{}/facturas?do_report={}&do_export={}".format(local_config.HOST,
                                                                                           str(local_config.PORT),
                                                                                           BASE_URI[1:-1],
                                                                                           do_report and 1 or 0,
                                                                                           do_export and 1 or 0),
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
            if do_report is True:
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

    @classmethod
    def shutdown_server(cls):
        request = requests.get("http://{}:{}{}/shutdown".format(local_config.HOST,
                                                                str(local_config.PORT),
                                                                BASE_URI[1:-1]
                                                                ))

    @classmethod
    @threadize
    def init_server(cls):
        API.server = True
        os.system("server.cmd")
        API.server = False

    @classmethod
    def is_server_on(cls):
        return API.server

    @classmethod
    def get_billing_period(cls, fecha):
        return get_billing_period(fecha)

    @classmethod
    def get_fecha_factura_from_periodo(cls, periodo):
        print(periodo)
        initial, final = periodo.split("-")
        ffact = datetime.datetime.strptime(final, "%d/%m/%y")
        if ffact.day != 8:
            ffact = ffact.replace(day=ffact.day + 1)
        return ffact




