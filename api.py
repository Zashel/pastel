import requests
import pprint
from definitions import *
from zashel.utils import log
from zrest.datamodels.shelvemodels import ShelveModel
import datetime
import sys
import shelve
import glob
if sys.version_info.minor == 3:
    from contextlib import closing
    shelve_open = lambda file, flag="c", protocol=None, writeback=False: closing(shelve.open(file, flag))
else:
    shelve_open = shelve.open

class API:
    basepath = "http://{}:{}/{}".format(HOST, str(PORT), BASE_URI[1:-1].strip("/"))

    @classmethod
    @log
    def get_billing_period(cls, invoice_date):
        if isinstance(invoice_date, str):
            invoice_date = datetime.datetime.strptime(invoice_date, "%d/%m/%y").date()
        if isinstance(invoice_date, datetime.datetime):
            invoice_date = invoice_date.date()
        assert isinstance(invoice_date, datetime.date)
        prev_day = datetime.date.fromordinal((invoice_date - datetime.date(1, 1, 1)).days)
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

    @classmethod
    @log
    def upload_pari(cls, pari_file):
        try:
            pari = ShelveModel(os.path.join(PATH, "facturas"),
                               30,
                               index_fields=PARI_FIELDS,
                               headers=PARI_FIELDS,
                               to_block = False)
            limit_date = datetime.datetime.strptime(
                    (datetime.datetime.now()-datetime.timedelta(days=92)).strftime("%d%m%Y"),
                     "%d%m%Y").date()
            data = dict()
            for index in range(pari.groups):
                data[index] = dict()
            for index, row in enumerate(API.read_pari(pari_file)):
                if (row["data"]["estado_recibo"] == "IMPAGADO" or
                        datetime.datetime.strptime(row["data"]["fecha_factura"], "%d/%m/%y").date() >= limit_date):
                    data[index%pari.groups][str(index)] = row["data"]
                if "eta" in row:
                    yield row
            for group in data:
                filepath = pari._data_path(group)
                [os.remove(filepath) for filepath in glob.glob("{}.*".format(filepath))]
                with shelve_open(filepath) as shelf:
                    shelf["filepath"] = filepath
                    shelf.update(data[group])
            for field in PARI_FIELDS:
                indexed = dict()
                for group in data:
                    for index in data[group]:
                        if data[group][index][field] not in indexed:
                            indexed[data[group][index][field]] = set()
                            indexed[data[group][index][field]] |= {index}
                filepath = pari._index_path(field)
                [os.remove(filepath) for filepath in glob.glob("{}.*".format(filepath))]
                with shelve_open(filepath) as shelf:
                    shelf["filepath"] = filepath
                    shelf.update(indexed)
        finally:
            pari.close()

