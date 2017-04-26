def calcular_letra_dni(nif):
    letras = "TRWAGMYFPDXBNJZSQVHLCKE"
    nie = ["XYZ"]
    if isinstance(nif, str):
        if nif[0] in nie:
            nif = str(nie.index(nif[0]))+nif[1:]
    try:
        int_nif = int(nif)
    except ValueError as e:
        raise ValueError("Error con formato de DNI")
    if isinstance(int_nif, int):
        return str(nif)+letras[int_nif%23]


if __name__ == "__main__":
    import unittest

    class Test_Utils(unittest.TestCase):

        def test_calcular_letra_dni(self):
            for number, letter in zip(range(0, 23), "TRWAGMYFPDXBNJZSQVHLCKE"):
                self.assertEqual(str(number) + letter, calcular_letra_dni(number))

    unittest.main()