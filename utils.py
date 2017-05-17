def calcular_letra_dni(nif):
    letras = "TRWAGMYFPDXBNJZSQVHLCKE"
    nie = "XYZ"
    snif = nif
    if isinstance(nif, str):
        if nif[0] in nie:
            snif = str(nie.index(nif[0]))+nif[1:]
    try:
        int_nif = int(snif)
    except ValueError as e:
        raise ValueError("Error con formato de DNI "+dni)
    if isinstance(int_nif, int):
        return str(nif)+letras[int_nif%23]

def formatear_letra_dni(nif):
    nif = nif.replace(" ", "")
    nif = nif.replace("-", "")
    if len(nif) > 0:
        if nif[0] in "ABCDEFGHJNPQRUVW":
            nif = "{}-{}".format(nif[0], nif[1:])
        elif nif[-1] in "TRWAGMYFPDXBNJZSQVHLCKE":
            nif = "{}-{}".format(nif[:-1], nif[-1])
    return nif

def calcular_y_formatear_letra_dni(nif):
    print(calcular_letra_dni(nif))
    print(formatear_letra_dni(calcular_letra_dni(nif)))
    return formatear_letra_dni(calcular_letra_dni(nif))

if __name__ == "__main__":
    import unittest

    class Test_Utils(unittest.TestCase):

        def test_calcular_letra_dni(self):
            for number, letter in zip(range(0, 23), "TRWAGMYFPDXBNJZSQVHLCKE"):
                self.assertEqual(str(number) + letter, calcular_letra_dni(number))

    unittest.main()