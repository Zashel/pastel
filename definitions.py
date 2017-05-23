import os
import uuid
import shelve
import datetime
import getpass
from zashel.utils import search_win_drive


#STATIC Variables, not configurable

STATIC = ["USERS_FIELDS",
          "USERS_UNIQUE",
          "USERS_PERMISSIONS",
          "PARI_FIELDS",
          "PARI_UNIQUE",
          "PAYMENTS_FIELDS",
          "PAYMENTS_INDEX",
          "MANUAL_FIELDS",
          "BASE_URI",
          "LOG_ERROR",
          "LOG_ERROR_PARI",
          "LOCAL_PATH",
          "METODOS_FIELDS",
          "COMMITMENTS_FIELDS",
          "COMMITMENTS_INDEX"]

PATH = "PASTEL"

LOCAL_PATH = os.path.join(os.environ["LOCALAPPDATA"], "pastel")
if not os.path.exists(LOCAL_PATH):
    os.makedirs(LOCAL_PATH)

LOCAL_CONFIG = os.path.join(LOCAL_PATH, "config")
if not os.path.exists(LOCAL_CONFIG):
    os.makedirs(LOCAL_CONFIG)

USERS_FIELDS = ["id",
                "fullname",
                "role"]

USERS_UNIQUE = "id"

USERS_PERMISSIONS = ["type",
                     "model",
                     "verb",
                     "allowed"]

PARI_FIELDS = ["id_cliente",
               "id_cuenta",
               "numdoc",
               "fecha_factura",
               "id_factura",
               "segmento",
               "importe_adeudado",
               "estado_recibo"]

PARI_UNIQUE = "id_factura"

PAYMENTS_FIELDS = ["fecha",
                   "importe",
                   "observaciones",
                   "dni",
                   "id_cliente",
                   "tels",
                   "oficina",
                   "posibles",
                   "estado"]

PAYMENTS_INDEX = ["fecha",
                  "importe",
                  "dni",
                  "id_cliente",
                  "oficina",
                  "estado"]

MANUAL_FIELDS = ["pagos_id",
                 "usuario",
                 "fecha",
                 "reportado"]

METODOS_FIELDS = "nombre"

COMMITMENTS_FIELDS = ["usuario",
                      "id_cliente",
                      "id_cuenta",
                      "id_factura",
                      "fecha_factura",
                      "importe",
                      "fecha",
                      "hora",
                      "canal",
                      "observaciones",
                      "estado"]

COMMITMENTS_INDEX = ["usuario",
                     "id_cliente",
                     "id_cuenta",
                     "id_factura",
                     "fecha_factura",
                     "importe",
                     "fecha",
                     "canal",
                     "estado"]
                      
BASE_URI = "^/pastel/api/v1$"

class Path:
    def __init__(self, path):
        self._path = path
    @property
    def path(self):
        if os.path.splitdrive(self._path)[0] == "":
            def recursive_search(path, sub=None):
                if sub is None:
                    sub = list()
                paths = os.path.split(path)
                sub.append(paths[1])
                if paths[0] == "":
                    raise FileNotFoundError
                try:
                    spath = os.path.join(search_win_drive(paths[0]),
                                         *sub)
                    return spath
                except FileNotFoundError:
                    recursive_search(paths[0], sub)
            try:
                return search_win_drive(self._path)
            except FileNotFoundError:
                return recursive_search(self._path)
        else:
            return self._path
    @path.setter
    def path(self, value):
        self._path = value

#LOCAL defined variables
LOCAL = ["HOST", "PORT",
         "PATH",
         "EXPORT_PATH",
         "ADMIN_DB",
         "UUID",
         "INIT_SERVER_STARTUP",
         "ITEMS_PER_PAGE",
         "USER"
         ]

REMOTE_PATHS = ["PATH",
                "ADMIN_DB",
                "EXPORT_PATH",
                "DAILY_EXPORT_PATH",
                "DATABASE_PATH",
                "N43_PATH",
                "N43_PATH_INCOMING",
                "N43_PATH_OUTGOING",
                "REPORT_PATH"
                ]

class LocalConfig: #To a dynamic access -> change API
    cache = dict()
    def __setattr__(self, attr, value):
        shelf = shelve.open(os.path.join(LOCAL_CONFIG, "config"))
        if attr in LOCAL:
            LocalConfig.cache[attr] = value
            if attr == "UUID":
                shelf["UUID-timeout"] = datetime.datetime.now() + datetime.timedelta(hours=8)
            else:
                shelf[attr] = value
        shelf.close()

    def __getattr__(self, attr):
        shelf = shelve.open(os.path.join(LOCAL_CONFIG, "config"))
        if attr in LOCAL:
            try:
                data = shelf[attr]
            except KeyError:
                if attr in LocalConfig.cache:
                    data = LocalConfig.cache[attr]
                else:
                    raise
            if attr in REMOTE_PATHS:
                return Path(data).path
            else:
                if attr == "UUID":
                    try:
                        timeout = shelf["UUID-timeout"]
                    except KeyError:
                        if "UUID-timeout" in LocalConfig.cache:
                            timeout = LocalConfig.cache["UUID-timeout"]
                        else:
                            timeout = None
                    if timeout is not None and timeout < datetime.datetime.now():
                        data = uuid.uuid4()
                        shelf[attr] = data
                return data
        shelf.close()

    def set(self, attr, value):
        self.__setattr__(attr, value)

    def set_default(self, attr, default):
        shelf = shelve.open(os.path.join(LOCAL_CONFIG, "config"))
        if attr in LOCAL and attr not in shelf:
            shelf[attr] = default
        shelf.close()
        return self.__getattr__(attr.lower())

local_config = LocalConfig()

local_config.set_default("HOST", "localhost")
local_config.set_default("PORT", 44752)
local_config.set_default("INIT_SERVER_STARTUP", True)
local_config.set_default("PATH", PATH)
local_config.set_default("EXPORT_PATH", os.path.join(PATH, "Exportaciones"))
local_config.set_default("ADMIN_DB", os.path.join(PATH, "DB", "Admin"))
local_config.set_default("ITEMS_PER_PAGE", 50)
local_config.set_default("USER", getpass.getuser())
if not os.path.exists(local_config.ADMIN_DB):
    os.makedirs(local_config.ADMIN_DB)

local_config.set_default("UUID", uuid.uuid4())

LOG_ERROR = os.path.join(LOCAL_PATH, "log_error_{}".format(local_config.UUID))
LOG_ERROR_PARI = os.path.join(LOCAL_PATH, "log_error_pari_{}".format(local_config.UUID))

SHARED = ["PM_CUSTOMER",
          "PM_PAYMENT_METHOD",
          "PM_PAYMENT_WAY",
          "DAILY_EXPORT_PATH",
          "PARI_FILE_FIELDS",
          "DATABASE_PATH",
          "N43_PATH",
          "N43_PATH_INCOMING",
          "N43_PATH_OUTGOING",
          "REPORT_PATH",
          "PAYMENTS_STATES",
          "FACTURAS",
          "FACTURAS_FILE"
          ]

class AdminConfig: #To a dynamic access -> change API -> Shit, I've repeated myself!
    cache = dict()
    def __setattr__(self, attr, value):
        shelf = shelve.open(os.path.join(local_config.ADMIN_DB, "config"))
        if attr in SHARED:
            AdminConfig.cache[attr] = value
            shelf[attr] = value
        shelf.close()

    def __getattr__(self, attr):
        shelf = shelve.open(os.path.join(local_config.ADMIN_DB, "config"))
        if attr in SHARED:
            try:
                data = shelf[attr]
            except KeyError:
                if attr in AdminConfig.cache:
                    data = AdminConfig.cache[attr]
                else:
                    raise
            if attr in REMOTE_PATHS:
                return Path(data).path
            else:
                return data
        shelf.close()

    def set(self, attr, value):
        self.__setattr__(attr, value)

    def set_default(self, attr, default):
        shelf = shelve.open(os.path.join(local_config.ADMIN_DB, "config"))
        if attr in SHARED and attr not in shelf:
            self.set(attr, default)
        shelf.close()
        return self.__getattr__(attr.lower())

admin_config = AdminConfig()

admin_config.set_default("DATABASE_PATH", os.path.join(PATH, "DB"))
admin_config.set_default("REPORT_PATH",  os.path.join(PATH, "Reportes"))
admin_config.set_default("DAILY_EXPORT_PATH", os.path.join(PATH, "Exportaciones", "Diarias"))
admin_config.set_default("N43_PATH", os.path.join("INFORMES GESTIÓN DIARIA",
                                                  "0.REPORTES BBOO",
                                                  "001 CARPETA DE PAGOS",
                                                  "040 NORMA43_JAZZTEL"))
admin_config.set_default("N43_PATH_INCOMING", os.path.join("INFORMES GESTIÓN DIARIA",
                                                           "0.REPORTES BBOO",
                                                           "001 CARPETA DE PAGOS",
                                                           "040 NORMA43_JAZZTEL",
                                                           "041 ENTRADAS"))
admin_config.set_default("N43_PATH_OUTGOING", os.path.join("INFORMES GESTIÓN DIARIA",
                                                           "0.REPORTES BBOO",
                                                           "001 CARPETA DE PAGOS",
                                                           "040 NORMA43_JAZZTEL",
                                                           "042 SALIDAS"))
admin_config.set_default("PARI_FILE_FIELDS", ["id_cliente",
                                              "id_cuenta",
                                              "numdoc",
                                              "tipodoc",
                                              "fecha_factura",
                                              "fecha_puesta_cobro",
                                              "id_factura",
                                              "segmento",
                                              "importe_adeudado",
                                              "metodo_pago",
                                              "fecha_devolucion",
                                              "importe_devolucion",
                                              "fecha_pago",
                                              "importe_aplicado",
                                              "metodo_recobro",
                                              "fecha_entrada_fichero",
                                              "fecha_salida_fichero",
                                              "estado_recibo",
                                              "primera_factura"])

admin_config.set_default("PM_CUSTOMER", "DEPARTAMENTO DE COBROS")

admin_config.set_default("PM_PAYMENT_METHOD", "TRANSFERENCIA")

admin_config.set_default("PM_PAYMENT_WAY", "INTERNA")

admin_config.set_default("PAYMENTS_STATES",
                         ["", "PENDIENTE", "APLICADO", "ILOCALIZABLE", "GRAN CUENTA", "DEUDA VENDIDA", "PAGO ORANGE"])

admin_config.set_default("FACTURAS_FILE", "codes.txt")
facturas = dict()
with open(admin_config.FACTURAS_FILE, "r") as f:
    for row in f:
        code, date = row.split(";")
        date = date.strip("\n")
        facturas[datetime.datetime.strptime(date, "%d/%m/%Y")] = code
admin_config.set_default("FACTURAS", facturas)


__all__ = list()
__all__.extend(STATIC)
#__all__.extend(LOCAL)
#__all__.extend(SHARED)
__all__.extend(["local_config",
                "admin_config",
                "LOCAL",
                "SHARED",
                "get_billing_period"
                ])

def get_billing_period(invoice_date):  # TODO: Get this Out of here
    if isinstance(invoice_date, str):
        invoice_date = datetime.datetime.strptime(invoice_date, "%d/%m/%y").date()
    if isinstance(invoice_date, datetime.datetime):
        invoice_date = invoice_date.date()
    assert isinstance(invoice_date, datetime.date)
    prev_day = datetime.date.fromordinal((invoice_date - datetime.date(1, 1, 1)).days)
    # prev_day = invoice_date
    if prev_day.day == 7:
        prev_day = prev_day.replace(day=8)
    prev_month_day = prev_day.day
    prev_month_month = prev_day.month - 1
    if prev_month_month == 0:
        prev_month_month = 12
        prev_month_year = prev_day.year - 1
    else:
        prev_month_year = prev_day.year
    prev_month = datetime.date(prev_month_year, prev_month_month, prev_month_day)
    return "{}-{}".format(prev_month.strftime("%d/%m/%y"), prev_day.strftime("%d/%m/%y"))
