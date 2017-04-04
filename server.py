#! Python/pastel.exe

from zrest.zrest.server import App, GET
from zrest.zrest.datamodels.shelvemodels import ShelveModel, ShelveRelational
from definitions import *

import os

PATH = "definitions"

if __name__ == "__main__":
    app = App()
    app.set_method("shutdown", "^/shutdown$", GET, app.shutdown)
    app.set_model(ShelveModel(os.path.join(PATH, "clientes"),
                              index_fields=PARI_FIELDS,
                              headers=PARI_FIELDS,
                              unique=PARI_UNIQUE),
                  "clientes",
                  "^/clientes/<id_factura>$")
    app.set_model(ShelveModel(os.path.join(PATH, "pagos"),
                              index_fields=PAYMENTS_FIELDS,
                              headers=PAYMENTS_FIELDS),
                  "pagos",
                  "^/pagos/<_id>$")
    app.set_model(ShelveRelational(os.path.join(PATH, "aplicados"),
                                   index_fields=APLICATION_FIELDS,
                                   headers=APLICATION_FIELDS,
                                   relations=[app.get_model("clientes"),
                                              app.get_model("pagos")]),
                  "aplicados",
                  "^/pagos/aplicados/<tipo>")
    app.run()