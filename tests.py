import unittest
from api import API

class Test_API(unittest.TestCase):

    def test_0_get_billing_period(self):
        self.assertEqual("01/12/16-01/01/17", API.get_billing_period("02/01/17"))
        self.assertEqual("15/12/16-15/01/17", API.get_billing_period("16/01/17"))
        self.assertEqual("22/12/16-22/01/17", API.get_billing_period("23/01/17"))