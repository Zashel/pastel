#! Python/pastel.exe

from zrest.server import App, GET, PUT
from zrest.datamodels.shelvemodels import ShelveModel, ShelveRelational
from definitions import *
from pari_model import Pari

import os

if __name__ == "__main__":
    app = App()
    app.set_base_uri(BASE_URI)
    app.set_method("shutdown", "^/shutdown$", GET, app.shutdown)
    app.set_model(ShelveModel(os.path.join(LOCAL_PATH, "config"),
                              1,
                              index_fields=CONFIG_FIELDS),
                  "config",
                  "^/config/<container>$")
    app.set_model(ShelveModel(os.path.join(DATABASE_PATH, "admin"),
                              1,
                              index_fields=CONFIG_FIELDS),
                  "admin",
                  "^/admin/<container>$")
    app.set_model(Pari(os.path.join(DATABASE_PATH, "facturas")),
                  "facturas",
                  "^/facturas/<id_factura>$")
    app.set_method("facturas", "^/n43$", PUT, "new_n43")
    app.set_model(ShelveModel(os.path.join(DATABASE_PATH, "pagos"),
                              index_fields=PAYMENTS_FIELDS,
                              headers=PAYMENTS_FIELDS),
                  "pagos",
                  "^/pagos/<_id>$")
    app.set_model(ShelveRelational(os.path.join(DATABASE_PATH, "aplicados"),
                                   index_fields=APLICATION_FIELDS,
                                   headers=APLICATION_FIELDS,
                                   relations=[app.get_model("facturas"),
                                              app.get_model("pagos")]),
                  "aplicados",
                  "^/pagos/aplicados/<tipo>")
    app.run(HOST, PORT)