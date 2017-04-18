import requests
import pprint
from definitions import *
from zashel.utils import log
import datetime

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
    def get_total_lines(cls, file, headers=True):
        assert os.path.exists(file)
        with open(file, "r") as f:
            final = sum([1 for x in f])
        if headers is True:
            final -= 1
        return final

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
        with open(pari_file, "r") as pari:
            headers = pari.readline().strip("\n").split("|")
            for row in pari:
                row = row.strip("\n").split("|")
                final = dict()
                for key in PARI_FIELDS:
                    if key.upper() in headers:
                        final[key] = row[headers.index(key.upper())]
                final["ciclo_facturado"] = API.get_billing_period(final["fecha_factura"])
                yield final

    @classmethod
    @log
    def upload_pari(cls, pari_file):
        for row in API.read_pari(pari_file):
            data = requests.post(API.basepath+"/facturas", json=row)
            if data.status_code == 201:
                yield data.json
            else:
                API.log_error(API.upload_pari, {"uri": API.basepath+"/facturas",
                                                "post": row,
                                                "status": data.status_code,
                                                "response": data.text})

    @classmethod
    @log
    def execute_with_percentile(cls, generator, total):
        for item in generator:
            yield {"response": item,
                   "over_total": round(generator/total, 4)}

