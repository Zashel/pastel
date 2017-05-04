import os
import uuid
import shelve
from zrest.datamodels.shelvemodels import ShelveModel
from zashel.utils import search_win_drive


#STATIC Variables, not configurable

STATIC = ["UUID",
          "USERS_FIELDS",
          "USERS_UNIQUE",
          "USERS_PERMISSIONS",
          "PARI_FIELDS",
          "PARI_UNIQUE",
          "PAYMENTS_FIELDS",
          "APLICATION_FIELDS",
          "BASE_URI",
          "LOG_ERROR",
          "LOG_ERROR_PARI",
          "LOCAL_PATH",
          "METODOS_FIELDS"]

UUID = uuid.uuid4() #Identifier of session

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
                   "id_cuenta",
                   "tel1",
                   "tel2",
                   "oficina"]

APLICATION_FIELDS = ["tipo", # Automático o Manual
                     "pagos__id",
                     "clientes_id_factura",
                     "importe_aplicado",
                     "nombre_cliente", # Manual
                     "numdoc",
                     "id_cuenta",
                     "periodo_facturado",
                     "metodos__id",
                     "via_de_pago"] #Crear Objeto Relacional con esto

METODOS_FIELDS = "nombre"

BASE_URI = "^/pastel/api/v1$"

LOG_ERROR = os.path.join(LOCAL_PATH, "log_error_{}".format(UUID))

LOG_ERROR_PARI = os.path.join(LOCAL_PATH, "log_error_pari_{}".format(UUID))

class Path:
    def __init__(self, path):
        self._path = path
    @property
    def path(self):
        return search_win_drive(self._path)
    @path.setter
    def path(self, value):
        self._path = value

#LOCAL defined variables
LOCAL = ["HOST", "PORT",
         "PATH",
         "EXPORT_PATH"]

class LocalConfig: #To a dynamic access -> change API
    def __getattr__(self, attr):
        shelf = shelve.open(os.path.join(LOCAL_CONFIG, "config"))
        data = None
        try:
            data = shelf[attr]
        finally:
            shelf.close()
            return data
    def __setattr__(self, attr, value):
        shelf = shelve.open(os.path.join(LOCAL_CONFIG, "config"))
        if attr in LOCAL:
            shelf[attr] = value
        shelf.close()
    def __getattr__(self, attr):
        shelf = shelve.open(os.path.join(LOCAL_CONFIG, "config"))
        if attr in LOCAL:
            return shelf[attr]
        shelf.close()
    def set_default(self, attr, default):
        shelf = shelve.open(os.path.join(LOCAL_CONFIG, "config"))
        if attr in LOCAL and attr not in shelf:
            shelf[attr] = default
        return self.__getattr__(attr.lower())

local_config = LocalConfig()

local_config.set_default("HOST", "localhost")
local_config.set_default("PORT", 44752)
local_config.set_default("PATH", "PASTEL")
local_config.set_default("EXPORT_PATH",os.path.join(local_config.PATH, "Exportaciones"))

#PATH Variables
PATHS = ["DATABASE_PATH",
         "REMOTE_PATH",
         "N43_PATH",
         "N43_PATH_INCOMING",
         "N43_PATH_OUTGOING",
         "REPORT_PATH"]

SHARED = ["PM_CUSTOMER",
          "PM_PAYMENT_METHOD",
          "PM_PAYMENT_WAY",
          "DAILY_EXPORT_PATH",
          "PARI_FILE_FIELDS"]

__all__ = list()
__all__.extend(STATIC)
__all__.extend(PATHS)
#__all__.extend(LOCAL)
__all__.extend(SHARED)
__all__.extend(["local_config",
                ])

PARI_FILE_FIELDS = ["id_cliente",
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
                    "primera_factura"]


#Path Definitions

REMOTE_PATH = r"//pnaspom2/campanas$/a-c/cobros/financiacion"
DATABASE_PATH = os.path.join(local_config.PATH, "DB")
REPORT_PATH = os.path.join(local_config.PATH, "Reportes")
DAILY_EXPORT_PATH = os.path.join(local_config.EXPORT_PATH, "Diarias")
N43_PATH = search_win_drive(r"INFORMES GESTIÓN DIARIA\0.REPORTES BBOO\001 CARPETA DE PAGOS\040 NORMA43_JAZZTEL")
N43_PATH_INCOMING = os.path.join(N43_PATH, "041 ENTRADAS")
N43_PATH_OUTGOING = os.path.join(N43_PATH, "042 SALIDAS")

#Payment matching definitions

PM_CUSTOMER = "DEPARTAMENTO DE COBROS"
PM_PAYMENT_METHOD = "TRANSFERENCIA"
PM_PAYMENT_WAY = "INTERNA"

