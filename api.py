import requests
import pprint
from definitions import *
from zashel.utils import log
from zrest.datamodels.shelvemodels import ShelveModel
from math import ceil
import datetime
import sys
import shelve
import glob
import os
import gc
import json
if sys.version_info.minor == 3:
    from contextlib import closing
    shelve_open = lambda file, flag="c", protocol=None, writeback=False: closing(shelve.open(file, flag))
else:
    shelve_open = shelve.open

class API:
    basepath = "http://{}:{}/{}".format(HOST, str(PORT), BASE_URI[1:-1].strip("/"))
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

    @classmethod
    @log
    def get_billing_period(cls, invoice_date):
        if isinstance(invoice_date, str):
            invoice_date = datetime.datetime.strptime(invoice_date, "%d/%m/%y").date()
        if isinstance(invoice_date, datetime.datetime):
            invoice_date = invoice_date.date()
        assert isinstance(invoice_date, datetime.date)
        #prev_day = datetime.date.fromordinal((invoice_date - datetime.date(1, 1, 1)).days)
        prev_day = invoice_date
        prev_month_day = prev_day.day
        prev_month_month = prev_day.month - 1
        if prev_month_month == 0:
            prev_month_month = 12
            prev_month_year = prev_day.year - 1
        else:
            prev_month_year = prev_day.year
        prev_month = datetime.date(prev_month_year, prev_month_month, prev_month_day)
        return "{}-{}".format(prev_month.strftime("%d/%m/%y"), prev_day.strftime("%d/%m/%y"))

    @classmethod
    @log
    def log_error(cls, function, aditional_dict, file=LOG_ERROR):
        with open(file, "a") as logger:
            to_log = "{} - API.{}:\n\t{}\n".format(datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S"),
                                                 function.__name__,
                                                 pprint.pformat(aditional_dict))
            logger.write(to_log)

    @classmethod
    @log
    def set_pari(cls):
        files =  glob.glob("{}*.csv".format(os.path.join(N43_PATH, "BI_131_FICHERO_PARI_DIARIO")))
        files.reverse()
        print(files)
        if len(files) > 0:
            data = requests.put("http://{}:{}{}/facturas".format(HOST,
                                                                 str(PORT),
                                                                 BASE_URI[1:-1]),
                                json = {"file": files[0]})
            data = json.loads(data)["data"]
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
            name = "report_pari{}".format(name)
            with open(os.path.join(REPORT_PATH, "Pari", name)) as f:
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
                            f.write(";".join(segmento, fecha_str, estado, importe_devuelto, importe_impagado)+"\n")
            return os.path.join(REPORT_PATH, "Pari", name)

    @classmethod
    @log
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
                "http://{}:{}{}/facturas?fecha_factura={}&estado_recibo=IMPAGADO&items_per_page=200".format(HOST,
                                                                                                            str(PORT),
                                                                                                            BASE_URI[1:-1],
                                                                                                            finaldates),
                            headers = {"Content-Type": "text/csv; charset=utf-8"}).text


