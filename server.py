#! Python/pastel.exe

import time
from random import randint

from zrest.server import App, GET, PUT, LOAD, NEXT, ALL
from zrest.datamodels.shelvemodels import ShelveModel, ShelveRelational, ShelveBlocking, ShelveForeign
from definitions import local_config
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
        print(kwargs)
        super().__init__(*args, **kwargs)
        print(self.index_fields)

    @property
    def unique_id(self):
        return local_config.UUID

    @unique_id.setter
    def unique_id(self, value):
        ShelveBlocking.unique_id = value

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
    #TODO: New model of config and admin
    app.set_model(Pari(os.path.join(admin_config.DATABASE_PATH, "facturas")),
                  "facturas",
                  "^/facturas/<id_factura>$")
    app.set_method("facturas", "^/n43$", LOAD, "load_n43")
    pagos = PASTELBlocking(os.path.join(admin_config.DATABASE_PATH, "pagos"),
                           index_fields=PAYMENTS_INDEX,
                           headers=PAYMENTS_FIELDS,
                           items_per_page=local_config.ITEMS_PER_PAGE)
    app.set_model(pagos,
                  "pagos",
                  "^/pagos/<_id>$",
                  ALL_NEXT)
    manual = ShelveModel(os.path.join(admin_config.DATABASE_PATH, "manual"),
                         index_fields=MANUAL_FIELDS,
                         headers=MANUAL_FIELDS,
                         items_per_page=local_config.ITEMS_PER_PAGE,
                         unique="pagos_id")
    app.set_model(manual,
                  "manual",
                  "^/manual/<_id>")
    app.set_model(ShelveForeign(pagos,
                                manual,
                                "pagos_id",
                                items_per_page=local_config.ITEMS_PER_PAGE),
                  "pagos_manual",
                  "^/pagos/<pagos_pagos_id>/manual<manual__id>$")
    app.set_model(ShelveModel(os.path.join(admin_config.DATABASE_PATH, "compromisos"),
                              index_fields=COMMITMENTS_FIELDS,
                              headers=COMMITMENTS_FIELDS),
                  "compromisos",
                  "^/compromisos/<_id>$")
    app.run(local_config.HOST, local_config.PORT)
