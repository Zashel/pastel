import os
import uuid
import shelve
from zrest.datamodels.shelvemodels import ShelveModel
from zashel.utils import search_win_drive

STATIC = ["UUID",
          "USERS_FIELDS",
          "USERS_UNIQUE",
          "USERS_PERMISSIONS",
          "PARI_FIELDS",
          "PARI_UNIQUE",
          "PAYMENTS_FIELDS",
          "APLICATION_FIELDS",
          "CONFIG_FIELDS",
          "BASE_URI",
          "LOG_ERROR",
          "LOG_ERROR_PARI",
          "LOCAL_PATH",
          "METODOS_FIELDS"]

PATHS = ["DATABASE_PATH",
         "REMOTE_PATH",
         "N43_PATH",
         "N43_PATH_INCOMING",
         "N43_PATH_OUTGOING",
         "REPORT_PATH"]

LOCAL = ["HOST", "PORT",
         "PATH",
         "EXPORT_PATH",]

SHARED = ["PM_CUSTOMER",
           "PM_PAYMENT_METHOD",
           "PM_PAYMENT_WAY",
           "DAILY_EXPORT_PATH",
           "PARI_FILE_FIELDS"]

__all__ = list()
__all__.extend(STATIC)
__all__.extend(PATHS)
__all__.extend(LOCAL)
__all__.extend(SHARED)

LOCAL_PATH = os.path.join(os.environ["LOCALAPPDATA"], "pastel")
CONFIG_FIELDS = ["container",
                 "field",
                 "value"]

class LocalConfigFile:
    def __getattr__(self, attr):
        shelf = shelve.open(os.path.join(LOCAL_PATH, "pastel"))
        data = None
        try:
            data = shelf[attr]
        finally:
            shelf.close()
            return data

    def __setattr__(self, attr, value):
        shelf = shelve.open(os.path.join(LOCAL_PATH, "pastel"))
        if attr in shelf["fields"]:
            shelf[attr] = value
        shelf.close()

    def __getattr__(self, attr):
        shelf = shelve.open(os.path.join(LOCAL_PATH, "pastel"))
        if attr in shelf["fields"]:
            return shelf[attr]["value"]
        shelf.close()


local = LocalConfigFile()
        

#Identifier of session
UUID = uuid.uuid4()

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


#Path Definitions

HOST, PORT = "localhost", 44752
REMOTE_PATH = r"//pnaspom2/campanas$/a-c/cobros/financiacion"
PATH = search_win_drive("PASTEL")
DATABASE_PATH = os.path.join(PATH, "DB")
REPORT_PATH = os.path.join(PATH, "Reportes")
EXPORT_PATH = os.path.join(PATH, "Exportaciones")
DAILY_EXPORT_PATH = os.path.join(EXPORT_PATH, "Diarias")
N43_PATH = search_win_drive(r"INFORMES GESTIÓN DIARIA\0.REPORTES BBOO\001 CARPETA DE PAGOS\040 NORMA43_JAZZTEL")
N43_PATH_INCOMING = os.path.join(N43_PATH, "041 ENTRADAS")
N43_PATH_OUTGOING = os.path.join(N43_PATH, "042 SALIDAS")
BASE_URI = "^/pastel/api/v1$"
LOG_ERROR = os.path.join(LOCAL_PATH, "log_error_{}".format(UUID))
LOG_ERROR_PARI = os.path.join(LOCAL_PATH, "log_error_pari_{}".format(UUID))

#Payment matching definitions

PM_CUSTOMER = "DEPARTAMENTO DE COBROS"
PM_PAYMENT_METHOD = "TRANSFERENCIA"
PM_PAYMENT_WAY = "INTERNA"

