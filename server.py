#! Python/pastel.exe

from zrest.server import App, GET, PUT, LOAD
from zrest.datamodels.shelvemodels import ShelveModel, ShelveRelational
from definitions import *
from pari_model import Pari

import os

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
    app.set_method("facturas", "^/n43$", LOAD, "new_n43")
    app.set_model(ShelveModel(os.path.join(admin_config.DATABASE_PATH, "pagos"),
                              index_fields=PAYMENTS_INDEX,
                              headers=PAYMENTS_FIELDS),
                  "pagos",
                  "^/pagos/<_id>$")
    app.set_model(ShelveRelational(os.path.join(admin_config.DATABASE_PATH, "aplicados"),
                                   index_fields=APLICATION_FIELDS,
                                   headers=APLICATION_FIELDS,
                                   relations=[app.get_model("facturas"),
                                              app.get_model("pagos")]),
                  "aplicados",
                  "^/pagos/aplicados/<tipo>")
    app.set_model(ShelveModel(os.path.join(admin_config.DATANASE_PATH, "compromisos"),
                              index_fields=COMMITMENTS_FIELDS,
                              headers=COMMITMENTS_FIELDS),
                  "compromisos",
                  "^/compromisos/<_id>$")
    app.run(local_config.HOST, local_config.PORT)
