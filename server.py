#! Python/pastel.exe

import time
from random import randint

from zrest.server import App, GET, PUT, LOAD, NEXT, ALL
from zrest.datamodels.shelvemodels import ShelveModel, ShelveRelational, ShelveBlocking
for x in range(5):
    try:
        from definitions import *
        time.sleep(x+randint(0, 3))
        break
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        continue
from pari_model import Pari

import os

ALL_NEXT = list(ALL)
ALL_NEXT.append(NEXT)

class PASTELBlocking(ShelveBlocking):
    def __init__(self, *args, **kwargs):
        args = list(args)
        if len(args)==1:
            args.append(None)
        else:
            args = args[:1]+[None]+args[1:]
        ShelveBlocking.__init__(self, *args, **kwargs)
        self.unique_id = local_config.UUID

if __name__ == "__main__":
    app = App()
    app.set_base_uri(BASE_URI)
    app.set_method("shutdown", "^/shutdown$", GET, app.shutdown)
    app.set_model(ShelveModel(os.path.join(admin_config.DATABASE_PATH, "usuarios"),
                              1,
                              index_fields=USERS_FIELDS,
                              headers=USERS_FIELDS,
                              unique="id"),
                  "usuarios",
                  "^/usuarios/<id>$")
    #app.set_model(ShelveModel(os.path.join(LOCAL_PATH, "config"),
    #                          1,
    #                          index_fields=CONFIG_FIELDS),
    #              "config",
    #              "^/config/<container>$")
    #app.set_model(ShelveModel(os.path.join(DATABASE_PATH, "admin"),
    #                          1,
    #                          index_fields=CONFIG_FIELDS),
    #              "admin",
    #              "^/admin/<container>$")
    #TODO: New model of config and admin
    app.set_model(Pari(os.path.join(admin_config.DATABASE_PATH, "facturas")),
                  "facturas",
                  "^/facturas/<id_factura>$")
    app.set_method("facturas", "^/n43$", LOAD, "load_n43")
    app.set_model(PASTELBlocking(os.path.join(admin_config.DATABASE_PATH, "pagos"),
                                 index_fields=PAYMENTS_INDEX,
                                 headers=PAYMENTS_FIELDS),
                  "pagos",
                  "^/pagos/<_id>$",
                  ALL_NEXT)
    app.set_model(ShelveRelational(os.path.join(admin_config.DATABASE_PATH, "aplicados"),
                                   index_fields=APLICATION_FIELDS,
                                   headers=APLICATION_FIELDS,
                                   relations=[app.get_model("facturas"),
                                              app.get_model("pagos")]),
                  "aplicados",
                  "^/pagos/aplicados/<tipo>")
    app.set_model(ShelveModel(os.path.join(admin_config.DATABASE_PATH, "compromisos"),
                              index_fields=COMMITMENTS_FIELDS,
                              headers=COMMITMENTS_FIELDS),
                  "compromisos",
                  "^/compromisos/<_id>$")
    app.run(local_config.HOST, local_config.PORT)
