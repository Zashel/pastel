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

CONFIG_FIELDS = ["container",
                 "field"]