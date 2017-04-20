import unittest
from api import API
from pari_model import Pari
import os
from definitions import *
from zrest.server import App, GET, POST

class Test_API(unittest.TestCase):

    def test_0_get_billing_period(self):
        self.assertEqual("01/12/16-01/01/17", API.get_billing_period("01/01/17"))
        self.assertEqual("08/02/17-08/03/17", API.get_billing_period("8/03/17"))
        self.assertEqual("15/12/16-15/01/17", API.get_billing_period("15/01/17"))
        self.assertEqual("22/12/16-22/01/17", API.get_billing_period("22/01/17"))

    def setUp(self):
        self.app = App()
        self.app.set_model(Pari(os.path.join(PATH, "facturas")),
                           "facturas",
                            "^/facturas/<id_factura>$")
        self.app.

    def test_1_pari_model(self):
        print(self.app.action(GET, "/facturas"))
        print(self.app.action(POST, "/facturas",
                              data={"file": r"c:\users\IURIRIV\Documents\pastel\BI_131_FICHERO_PARI_DIARIO_20170412.csv"}))


if __name__ == "__main__":
    unittest.main()