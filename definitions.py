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
         "EXPORT_PATH",
         "ADMIN_DB",
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
            if attr in REMOTE_PATHS:
                return Path(shelf[attr]).path
            else:
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
local_config.set_default("PATH", PATH)
local_config.set_default("EXPORT_PATH", os.path.join(PATH, "Exportaciones"))
local_config.set_default("ADMIN_DB", os.path.join(PATH, "Admin"))

SHARED = ["PM_CUSTOMER",
          "PM_PAYMENT_METHOD",
          "PM_PAYMENT_WAY",
          "DAILY_EXPORT_PATH",
          "PARI_FILE_FIELDS",
          "DATABASE_PATH",
          "N43_PATH",
          "N43_PATH_INCOMING",
          "N43_PATH_OUTGOING",
          "REPORT_PATH"
          ]

class AdminConfig: #To a dynamic access -> change API -> Shit, I've repeated myself!
    def __getattr__(self, attr):
        shelf = shelve.open(os.path.join(local_config.ADMIN_DB, "config"))
        data = None
        try:
            data = shelf[attr]
        finally:
            shelf.close()
            return data
    def __setattr__(self, attr, value):
        shelf = shelve.open(os.path.join(local_config.ADMIN_DB, "config"))
        if attr in SHARED:
            shelf[attr] = value
        shelf.close()
    def __getattr__(self, attr):
        shelf = shelve.open(os.path.join(local_config.ADMIN_DB, "config"))
        if attr in SHARED:
            if attr in REMOTE_PATHS:
                return Path(shelf[attr]).path
            else:
                return shelf[attr]
        shelf.close()
    def set_default(self, attr, default):
        shelf = shelve.open(os.path.join(local_config.ADMIN_DB, "config"))
        if attr in SHARED and attr not in shelf:
            shelf[attr] = default
        return self.__getattr__(attr.lower())

admin_config = AdminConfig()

admin_config.set_default("DATABASE_PATH", os.path.join(PATH, "DB"))
admin_config.set_default("REPORT_PATH",  os.path.join(PATH, "Reportes"))
admin_config.set_default("DAILY_EXPORT_PATH", os.path.join("Exportaciones", "Diarias"))
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


__all__ = list()
__all__.extend(STATIC)
#__all__.extend(LOCAL)
#__all__.extend(SHARED)
__all__.extend(["local_config",
                "admin_config"
                ])

