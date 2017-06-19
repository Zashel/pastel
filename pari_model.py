from zrest.basedatamodel import RestfulBaseInterface
import gc
import shelve
import os
from definitions import *
import datetime
from zashel.utils import log
from math import ceil
import glob
import re
from utils import *
import json
import pprint

#TODO: Fix imports order


class Pari(RestfulBaseInterface):
    def __init__(self, filepath):
        super().__init__()
        self._filepath = filepath
        path, filename = os.path.split(self.filepath)
        if not os.path.exists(path):
            os.makedirs(path)
        self.set_shelve("c")
        self.shelf.close()
        self.set_shelve()
        try:
            self._loaded_file = self.shelf["file"]
        except KeyError:
            self._loaded_file = None
        self.name = None
        self.list_data = dict()
        self.page = 1
        self.items_per_page = 50
        try:
            self.all = self.shelf["all"]
        except KeyError:
            self.all = set()
        self.ids_facturas = None
        self.total_query = int()
        self.filter = None

    def set_shelve(self, flag="r"): # To implement metadata
        self._shelf = shelve.open(self.filepath, flag)

    @property
    def filepath(self):
        return self._filepath

    @property
    def shelf(self):
        return self._shelf

    @property
    def loaded_file(self):
        return self._loaded_file

    def headers(self):
        return PARI_FIELDS

    def read_pari(self, pari_file):
        assert os.path.exists(pari_file)
        begin = datetime.datetime.now()
        total_bytes = os.stat(pari_file).st_size
        read_bytes = int()
        last = 0.0000
        info = False
        with open(pari_file, "r") as pari:
            headers = pari.readline().strip("\n").split("|")
            for line in pari:
                read_bytes += len(bytearray(line, "utf-8"))+1
                percent = read_bytes/total_bytes
                if percent >= last:
                    last += 0.0001
                    info = True
                row = line.strip("\n").split("|")
                final = dict()
                for index, key in enumerate(headers):
                    final[key.lower()] = row[index]
                if info is True:
                    time = datetime.datetime.now() - begin
                    yield {"percent": round(percent, 4),
                           "time": time,
                           "eta": (time/percent)-time,
                           "data": final}
                    info = False
                else:
                    yield {"data": final}

    def set_pari(self, pari_file, *, do_export=True, do_report=True):
        if pari_file == "":
            files =  glob.glob("{}*.csv".format(os.path.join(admin_config.N43_PATH_INCOMING, "BI_131_FICHERO_PARI_DIARIO")))
            files.sort()
            files.reverse()
            pari_file = files[0]
        API_id_factura = {"_heads": ["fecha_factura",
                                     "importe_adeudado",
                                     "estado_recibo",
                                     "id_cuenta"],
                          "data": dict()}
        API_id_cuenta = {"_heads": ["segmento",
                                    "facturas",
                                    "id_cliente"],
                          "data": dict()}
        API_id_cliente = {"_heads": ["numdoc",
                                     "id_cuenta"],
                          "data": dict()}
        PARI_FIELDS = admin_config.PARI_FILE_FIELDS
        API_segmentos = list()
        index_segmentos = dict()
        API_estados = list()
        index_estados = dict()
        index_facturas = dict()
        API_numdocs = {"_heads": ["id_cuenta"],
                       "data": dict()}
        limit_date = datetime.datetime.strptime(
            (datetime.datetime.now() - datetime.timedelta(days=92)).strftime("%d%m%Y"),
            "%d%m%Y").date()
        total = int()
        self.all = set()
        reports = {"importes por fechas y estados": dict(),
                    "facturas por fechas y estados": dict(),
                    "devoluciones por fechas y estados": dict(),
                    "diario": dict()}
        ife = reports["importes por fechas y estados"]
        ffe = reports["facturas por fechas y estados"]
        dfe = reports["devoluciones por fechas y estados"]
        diario = dict()
        for row in self.read_pari(pari_file):
            id_factura = int(row["data"]["id_factura"])
            id_cuenta = int(row["data"]["id_cuenta"])
            id_cliente = int(row["data"]["id_cliente"])
            numdoc = row["data"]["numdoc"]
            final = {"id_cliente": API_id_cliente,
                     "id_cuenta": API_id_cuenta,
                     "id_factura": API_id_factura,
                     "numdoc": API_numdocs,
                     "estados": API_estados,
                     "segmentos": API_segmentos,
                     "index":{"estados": index_estados,
                              "segmentos": index_segmentos,
                              "fecha_factura": index_facturas},
                     "reports": reports
                     }
            data = row["data"]
            #Exporting daily reports of certain invoices:
            if do_export is True:
                fecha_puesta_cobro = datetime.datetime.strptime(data["fecha_puesta_cobro"], "%d/%m/%y")
                if (fecha_puesta_cobro + datetime.timedelta(days=61) >= datetime.datetime.today().replace(hour=0,
                                                                                                          minute=0,
                                                                                                          second=0,
                                                                                                          microsecond=0) and
                        data["primera_factura"] == "1"):
                    str_fecha_factura = datetime.datetime.strptime(data["fecha_factura"], "%d/%m/%y")
                    if data["fecha_factura"] not in diario:
                        diario[data["fecha_factura"]] = list()
                        diario[data["fecha_factura"]].append(";".join(PARI_FIELDS))
                    final_list = list()
                    for head in PARI_FIELDS:
                        if "fecha" in head:
                            item = datetime.datetime.strptime(data[head], "%d/%m/%y").strftime("%d/%m/%Y")
                        else:
                            item = data[head]
                        final_list.append(item)
                    diario[data["fecha_factura"]].append(";".join(final_list))
            for report in (ife, ffe, dfe):
                if data["segmento"] not in report:
                    report[data["segmento"]] = dict()
                for segmento in report:
                    if data["fecha_factura"] not in report[segmento]:
                        report[segmento][data["fecha_factura"]] = dict()
                    for fecha_factura in report[segmento]:
                        if data["estado_recibo"] not in report[segmento][fecha_factura]:
                            report[segmento][fecha_factura][data["estado_recibo"]] = int()
            ife[data["segmento"]][data["fecha_factura"]][data["estado_recibo"]] += int(
                    data["importe_adeudado"].replace(",", ""))
            dfe[data["segmento"]][data["fecha_factura"]][data["estado_recibo"]] += int(
                    data["importe_devolucion"].replace(",", ""))
            ffe[data["segmento"]][data["fecha_factura"]][data["estado_recibo"]] += 1
            #if (row["data"]["estado_recibo"] == "IMPAGADO" or row["data"]["estado_recibo"] == "PAGO PARCIAL" or
            #            datetime.datetime.strptime(row["data"]["fecha_factura"], "%d/%m/%y").date() >= limit_date):
            if row["data"]["estado_recibo"] == "IMPAGADO": #Let's play mini, then
                for name, item, api in (("id_factura", id_factura, API_id_factura),
                                        ("id_cuenta", id_cuenta, API_id_cuenta),
                                        ("id_cliente", id_cliente, API_id_cliente)):
                    heads = api["_heads"]
                    if item not in api["data"]:
                        api["data"][item] = [None for item in heads]
                    for index, head in enumerate(heads):
                        if head in ("id_factura",
                                    "id_cliente",
                                    "id_cuenta"):
                            if head == "id_cliente":
                                API_numdocs["data"].update({numdoc: [id_cliente]})
                            if name == "id_cliente" and head == "id_cuenta":
                                if api["data"][item][index] is None:
                                    api["data"][item][index] = list()
                                if id_cuenta not in api["data"][item][index]:
                                    api["data"][item][index].append(id_cuenta)
                            else:
                                api["data"][item][index] = {"id_factura": id_factura,
                                                            "id_cliente": id_cliente,
                                                            "id_cuenta": id_cuenta}[head]
                        elif head == "facturas":
                            if api["data"][item][index] is None:
                                api["data"][item][index] = list()
                            api["data"][item][index].append(id_factura)
                        elif head == "importe_adeudado":
                            importe = float(row["data"][head].replace(",", "."))
                            importe = int(importe*100)
                            api["data"][item][index] = importe
                        elif head == "segmento":
                            if row["data"][head] not in API_segmentos:
                                API_segmentos.append(row["data"][head])
                            if row["data"][head] not in index_segmentos:
                                index_segmentos[row["data"][head]] = set() #id_cliente
                            index_segmentos[row["data"][head]] |= {id_cliente}
                            segmento = API_segmentos.index(row["data"][head])
                            api["data"][item][index] = segmento.to_bytes(ceil(segmento.bit_length() / 8), "big")
                        elif head == "estado_recibo":
                            if row["data"][head] not in API_estados:
                                API_estados.append(row["data"][head])
                            if row["data"][head] not in index_estados:
                                index_estados[row["data"][head]] = set() #id_factura
                            index_estados[row["data"][head]] |= {id_factura}
                            estado = API_estados.index(row["data"][head])
                            api["data"][item][index] = estado.to_bytes(ceil(estado.bit_length() / 8), "big")
                        elif head == "fecha_factura":
                            fecha = datetime.datetime.strptime(row["data"][head], "%d/%m/%y")
                            fecha = int(fecha.strftime("%d%m%y"))
                            fecha = fecha.to_bytes(ceil(fecha.bit_length() / 8), "big")
                            api["data"][id_factura][index] = fecha
                            if row["data"][head] not in index_facturas:
                                index_facturas[row["data"][head]] = set() #id_factura
                            index_facturas[row["data"][head]] |= {id_factura}
                        else:
                            api["data"][item][index] = row["data"][head]
                self.all |= {id_factura}
                total += 1
            if "eta" in row:
                yield row
        self.shelf.close()
        self.set_shelve("c")
        self.shelf.update(final)
        path, name = os.path.split(pari_file)
        self.shelf["file"] = name
        self.shelf["total"] = total
        self.shelf["all"] = self.all
        self._loaded_file = name
        self.shelf.close()
        self.set_shelve()
        if do_export is True:
            for fecha_factura in diario:
                str_fecha_factura = datetime.datetime.strptime(fecha_factura, "%d/%m/%y")
                with open(os.path.join(admin_config.DAILY_EXPORT_PATH,
                                       "jazztel_ciclo_" + str_fecha_factura.strftime("%Y-%m-%d") + ".csv"),
                          "w") as f:
                    f.write("\n".join(diario[fecha_factura]))
        ife = data["importes por fechas y estados"]
        ffe = data["facturas por fechas y estados"]
        dfe = data["devoluciones por fechas y estados"]
        segmentos = list(ife.keys())
        segmentos.sort()
        assert len(segmentos) > 0
        fechas = list(ife[segmentos[0]].keys())
        fechas.sort()
        assert len(fechas) > 0
        estados = list(ife[segmentos[0]][fechas[0]].keys())
        estados.sort()
        assert len(estados) > 0
        heads = "segmento;fecha_factura;estado;facturas;importe_devuelto;importe_impagado\n"
        name = os.path.split(pari_file)[1].strip("BI_131_FICHERO_PARI_DIARIO")
        name = "report_pari_{}".format(name)
        if do_report is True:  # Set in server
            with open(os.path.join(admin_config.REPORT_PATH, "Pari", name), "w") as f:
                f.write(heads)
                for segmento in segmentos:
                    for fecha in fechas:
                        for estado in estados:
                            fecha_str = datetime.datetime.strptime(fecha, "%d/%m/%y").strftime("%d/%m/%Y")
                            facturas = str(ffe[segmento][fecha][estado])
                            importe_devuelto = str(dfe[segmento][fecha][estado])
                            importe_devuelto = "{},{}".format(importe_devuelto[:-2], importe_devuelto[-2:])
                            importe_impagado = str(ife[segmento][fecha][estado])
                            importe_impagado = "{},{}".format(importe_impagado[:-2], importe_impagado[-2:])
                            f.write(";".join((segmento,
                                              fecha_str,
                                              estado,
                                              facturas,
                                              importe_devuelto,
                                              importe_impagado
                                              )) + "\n")

    def read_n43(self, filepath):
        if os.path.exists(filepath):
            begin = datetime.datetime.now()
            total_bytes = os.stat(filepath).st_size
            read_bytes = int()
            last = 0.0000
            total = int()
            info = False
            re_nif = re.compile(r"[DNI]?[ ]?([XYZ]?[0-9]{5,8}[TRWAGMYFPDXBNJZSQVHLCKE]{1})")
            re_cif = re.compile(r"[ABCDEFGHJNPQRUVW]{1}[0-9]{8}")
            re_tels = re.compile(r"\+34[6-9]{1}[0-9]{8}|[6-9]{1}[0-9]{8}")
            with open(filepath, "r") as file_:
                f_oper = None
                f_valor = None
                oficina_orig = str()
                importe = str()
                observaciones = str()
                account = str()
                for row in file_:
                    read_bytes += len(bytearray(row, "utf-8")) + 1
                    percent = read_bytes / total_bytes
                    if percent >= last:
                        last += 0.0001
                        info = True
                    row = row.strip("\n")
                    if row.startswith("11"):
                        account = row[2:20]
                    if row.startswith("22") or row.startswith("33"):
                        if not f_oper is None and not observaciones.startswith("TRASP. AGRUPADO") and not observaciones.startswith("TRASPASO A CTA"):
                            total += 1
                            observaciones = observaciones.strip()
                            telefonos = list()
                            nif = None
                            if observaciones.startswith("TRANSFER"):
                                observaciones = observaciones[:-8]
                            elif observaciones.startswith("81856015"):
                                nif = calcular_letra_dni(observaciones[15:23])
                                telefonos.append(observaciones[53:62])
                            nifs = set()
                            tels = set()
                            if nif is None:
                                for ind, restring in enumerate((observaciones,
                                                                observaciones.replace(".", ""),
                                                                observaciones.replace("-", ""),
                                                                observaciones.replace(" ", ""))):
                                    for nif in re_nif.findall(restring.upper()):
                                        nifs.add(nif)
                                    for cif in re_cif.findall(restring.upper()):
                                        if cif[0] in "XYZ":
                                            cif = calcular_letra_dni(cif)
                                        nifs.add(cif)
                                    for tel in re_tels.findall(restring.upper()):
                                        tels.add(tel)
                                    if ind == 0 and len(nifs) > 0:
                                        break
                                telefonos = list(tels)
                                nifs = list(nifs)
                                if len(nifs) > 0:
                                    nif = nifs[0]
                                    for nifid in nifs:
                                        if nif[-1] in "TRWAGMYFPDXBNJZSQVHLCKE":
                                            nif = nifid
                                            break
                                else:
                                    nif = ""
                            nif = formatear_letra_dni(nif)
                            final = {"cuenta": account,
                                     "fecha_operacion": f_oper,
                                     "fecha_valor": f_valor,
                                     "oficina_origen": oficina_orig,
                                     "importe": importe,
                                     "observaciones": observaciones,
                                     "nif": nif,
                                     "telefonos": telefonos}
                            f_oper = None
                            f_valor = None
                            oficina_orig = str()
                            importe = str()
                            observaciones = str()
                            if info is True:
                                time = datetime.datetime.now() - begin
                                yield {"percent": round(percent, 4),
                                       "time": time,
                                       "eta": (time / percent) - time,
                                       "data": final}
                                info = False
                            else:
                                yield {"data": final}
                        if row.startswith("22"):
                            row = row.strip()
                            f_oper = datetime.datetime.strptime(row[10:16], "%y%m%d")
                            f_valor = datetime.datetime.strptime(row[16:22], "%y%m%d")
                            importe = int(row[28:42])
                            observaciones = row[52:].strip()
                            oficina_orig = row[6:10]
                    elif row.startswith("23"):
                        observaciones += row[4:].strip()

    def get_codes(self):
        fechas_facturas = list(self.shelf["reports"]["importes por fechas y estados"]["RESIDENCIAL"].keys())
        fechas_facturas = [datetime.datetime.strptime(fecha, "%d/%m/%y") for fecha in fechas_facturas]
        fechas_facturas.sort()
        final = dict(admin_config.FACTURAS)
        fechas_final = list(admin_config.FACTURAS.keys())
        fechas_final.sort()
        fecha_inicio = fechas_final[-1]
        codigo_inicio = final[fecha_inicio]
        len_facturas = len(final)
        if fecha_inicio in fechas_facturas:
            index_inicio = fechas_facturas.index(fecha_inicio)
            for index, fecha in enumerate(fechas_facturas):
                if fecha not in final:
                    final[fecha] = codigo_inicio+index-index_inicio
        len_final = len(final)
        if len_final > len_facturas+6:
            keys = len(final.keys())
            keys.sort()
            sfinal = [";".join((final[key], key.strftime("%d/%m/%Y"))) for key in keys]
            with open(admin_config.FACTURAS_FILE, "w") as f:
                f.write("\n".join(sfinal))
        admin_config.FACTURAS = final
        return final

    def set_n43(self, filepath):
        if os.path.exists(filepath):
            apply_date = datetime.datetime.today().strftime("%d/%m/%Y") #TODO: To config
            print("Loading Codes")
            codes = self.get_codes()
            print("Loading PARI")
            shelf = dict(self.shelf)
            print("Cleaning")
            gc.collect()
            account_number = ["018239990014690035"] #TODO: set in shitty config
            account_ventanillas = ["018239990202055004"]
            if not "aplicados" in self.shelf:
                self.shelf["aplicados"] = dict()
            applied = dict(self.shelf["aplicados"])
            print("LEN_APPLIED {}".format(len(applied)))
            print("LEN_NUMDOC {}".format(len(shelf["numdoc"]["data"])))
            print("LEN_CODES {}".format(len(codes)))
            final = list()
            manuals = list()
            anulaciones = dict()
            informe = {"total": {"operaciones": int(),
                                 "importe": int()},
                       "aplicado": {"operaciones": int(),
                                    "importe": int()},
                       "pendiente": {"operaciones": int(),
                                     "importe": int()},
                       "anulaciones": {"operaciones": int(),
                                       "importe": int()},
                       "ventanillas": {"operaciones": int(),
                                       "importe": int()}
                       }
            for row in self.read_n43(filepath):
                data = row["data"]
                if data["cuenta"] in account_number:
                    if data["observaciones"].startswith("ANULACIONES"):
                        if data["cuenta"] not in anulaciones:
                            anulaciones[data["cuenta"]] = dict()
                        anulaciones[data["cuenta"]][data["importe"]] = data["oficina_origen"]
                        informe["anulaciones"]["operaciones"] += 1
                        informe["anulaciones"]["importe"] += data["importe"]
                    informe["total"]["operaciones"] += 1
                    informe["total"]["importe"] += data["importe"]
                elif data["cuenta"] in account_ventanillas:
                    informe["ventanillas"]["operaciones"] += 1
                    informe["ventanillas"]["importe"] += data["importe"]
            for row in self.read_n43(filepath):
                data = row["data"]
                total = int()
                possibles = dict()
                go_on = True
                payments_list = list()
                if data["cuenta"] in account_number and not data["observaciones"].startswith("ANULACIONES"):
                    if (data["importe"] in anulaciones[data["cuenta"]] and
                            anulaciones[data["cuenta"]][data["importe"]] == data["oficina_origen"]):
                        del(anulaciones[data["cuenta"]][data["importe"]])
                        continue
                    id_cliente = str()
                    id_cuentas = list()
                    if data["nif"] in shelf["numdoc"]["data"]:
                        #print("{} en numdoc".format(data["nif"]))
                        id_cliente = shelf["numdoc"]["data"][data["nif"]][0] #TODO: Get index of field by header position
                        id_cuentas = shelf["id_cliente"]["data"][id_cliente][1]
                        for id_cuenta in id_cuentas:
                            #print("id_cuenta {}".format(id_cuentas))
                            if shelf["id_cuenta"]["data"][id_cuenta][0] != "GRAN CUENTA":
                                facturas = shelf["id_cuenta"]["data"][id_cuenta][1]
                                facturas.sort()
                                for id_factura in facturas:
                                    total += 1
                                    estado = (shelf["estados"][int.from_bytes(
                                            shelf["id_factura"]["data"][id_factura][2], "big")])
                                    fecha_factura = int.from_bytes(shelf["id_factura"]["data"][id_factura][0],
                                                                   "big")
                                    fecha_factura = str(fecha_factura)
                                    fecha_factura = "0"*(6-len(fecha_factura))+fecha_factura
                                    fecha_factura = datetime.datetime.strptime(fecha_factura, "%d%m%y")
                                    possibles[id_factura] = {"importe": shelf["id_factura"]["data"][id_factura][1],
                                                             "id_cuenta": id_cuenta,
                                                             "fecha_factura": fecha_factura,
                                                             "estado": estado}
                        election = None
                        if total >= 1:
                            ids_factura = list(possibles.keys())
                            ids_factura.sort()
                            pdte = data["importe"]
                            applied_flag = False
                            for id_factura in ids_factura:
                                #print("Posibles :{}".format(pprint.pprint(possibles[id_factura])))
                                #input("id_factura in applied {}".format(id_factura in applied))
                                if (possibles[id_factura]["estado"] in ("IMPAGADO", "PAGO PARCIAL") and
                                            possibles[id_factura]["importe"] > 0):
                                    if (not id_factura in applied or
                                            (id_factura in applied and
                                            applied[id_factura]["importe_aplicado"] < applied[id_factura]["importe"]) and
                                            pdte > 0):
                                        if not id_factura in applied:
                                            applied[id_factura] = {"importe_aplicado": 0,
                                                                   "importe": possibles[id_factura]["importe"]}
                                        unpaid = applied[id_factura]["importe"] - applied[id_factura]["importe_aplicado"]
                                        to_apply = pdte < unpaid and pdte or unpaid
                                        pdte -= to_apply
                                        if pdte < 0:
                                            pdte = 0
                                        try:
                                            code = codes[possibles[id_factura]["fecha_factura"]]
                                        except KeyError:
                                            #print(possibles)
                                            #print("Orig: {}".format(int.from_bytes(
                                            #                   shelf["id_factura"]["data"][id_factura][0],
                                            #                   "big")))
                                            code = 1
                                        subdata = [str(apply_date),
                                                   str(code),
                                                   str(admin_config.PM_CUSTOMER),
                                                   str(data["nif"]),
                                                   str(id_factura),
                                                   str(data["fecha_operacion"].strftime("%d/%m/%y")),
                                                   str(round(to_apply/100, 2)).replace(".", ","),
                                                   str(id_cuenta),
                                                   str(get_billing_period(possibles[id_factura]["fecha_factura"])),
                                                   str(admin_config.PM_PAYMENT_METHOD),
                                                   str(admin_config.PM_PAYMENT_WAY)
                                                   ]
                                        payments_list.append(";".join(subdata))
                                        applied[id_factura]["importe_aplicado"] += to_apply
                                        applied_flag = True
                                if pdte == 0:
                                    informe["aplicado"]["operaciones"] += 1
                                    informe["aplicado"]["importe"] += data["importe"]
                                    final.extend(payments_list)
                                    go_on = False
                                    break
                            if pdte > 0 and applied_flag is True:
                                go_on = True
                        if pdte > 0 and applied_flag is False:
                            go_on = True
                    else:
                        go_on = True
                    if go_on is True:
                        go_on_final = row["data"].copy()
                        poss = payments_list.copy()
                        #for id in poss:
                        #    for field in poss[id]:
                        #        if isinstance(poss[id][field], datetime.datetime):
                        #            poss[id][field] = poss[id][field].strftime("%d/%m/%Y")
                        for item in go_on_final:
                            if isinstance(go_on_final[item], datetime.datetime):
                                go_on_final[item] = go_on_final[item].strftime("%d/%m/%Y")
                        go_on_final.update({"id_cliente": id_cliente,
                                            "posibles": poss})
                        manuals.append(go_on_final)
                self.shelf["aplicados"].update(applied)
                if "eta" in row:
                    yield row
            with open(os.path.join(local_config.EXPORT_PATH,
                                   "localizacion_automatica_{}.csv".format(apply_date.replace("/", "-"))),
                      "w") as f:
                f.write("\n".join(final))
            os.makedirs(os.path.join(admin_config.REPORT_PATH, "ISM"), exist_ok=True)
            informe["pendiente"]["operaciones"] = informe["total"]["operaciones"] - informe["aplicado"]["operaciones"]
            informe["pendiente"]["importe"] = informe["total"]["importe"] - informe["aplicado"]["importe"]
            final_informe = "estado;operaciones;importe\n"
            final_informe += "\n".join([";".join((estado,
                                                  str(informe[estado]["operaciones"]),
                                                  str(informe[estado]["importe"]/100).replace(".", ",")))
                                        for estado in informe])
            with open(os.path.join(admin_config.REPORT_PATH, "ISM",
                                   "informe_ism_{}.csv".format(apply_date.replace("/", "-"))),
                      "w") as f:
                f.write(final_informe)
            yield {"manuals": manuals, "anulaciones": anulaciones}

    def replace(self, filter, data, **kwargs):
        if "file" in data and os.path.exists(data["file"]):
            path, name = os.path.split(data["file"])
            if ("file" in self.shelf and name > self.shelf["file"]) or "file" not in self.shelf:
                self.drop(filter, **kwargs)
                return self.insert(data, filter=filter)
            else:
                return self.fetch({}, reportes=True)
        #TODO: Reenviar algo si no hay nada

    def drop(self, filter, **kwargs):
        if self.loaded_file is not None:
            self._loaded_file = None
            self.shelf.close()
            for file in glob.glob("{}.*".format(self.filepath)):
                os.remove(file)
            self.set_shelve("c")
            self.shelf.close()
            self.set_shelve()
            return {"data": {"pari": {"data": [],
                                      "total": 0,
                                      "page": 1,
                                      "items_per_page": self.items_per_page}
                             },
                    "total": 1,
                    "page": 1,
                    "items_per_page": self.items_per_page}

    def load_n43(self, data, **kwargs): #TODO: Move to Server
        if isinstance(data, str): #Direct call, transform to json
            data = json.loads(data)
        try:
            if self.loaded_file is not None and "file" in data and os.path.exists(data["file"]):
                final = None
                for item in self.set_n43(data["file"]):
                    if "eta" in item:
                        print("\r{0:{w}}".format(str(item["eta"]), w=79, fill=" "), end="")
                    else:
                        final = item
                print()
                return json.dumps({"data": final,
                                   "headers": {"Content-Type": "text/csv"}})
            else:
                print(data)
        except:
            print("Final: {}".format(final))
            raise

    def insert(self, data, **kwargs): #TODO: Move to Server
        do_export = False
        do_report = False
        if "filter" in kwargs:
            filter = kwargs["filter"]
            if "do_export" in filter:
                do_export = filter["do_export"] == "1"
            if "do_report" in kwargs["filter"]:
                do_report = filter["do_report"] == "1"
        if self.loaded_file is None and "file" in data:
            for item in self.set_pari(data["file"], do_export=do_export, do_report=do_report):
                print("\r{0:{w}}".format(str(item["eta"]), w=79, fill=" "), end="")
            print()
        return self.fetch({}, reportes=True)

    def fetch(self, filter, **kwargs):
        if not self.loaded_file:
            return {"filepath": "",
                    "data": {"pari": {"data": [],
                                      "total": 0,
                                      "page": 1,
                                      "items_per_page": self.items_per_page}
                             },
                    "total": 1,
                    "page": 1,
                    "items_per_page": self.items_per_page }
        else:
            if not kwargs:
                main_indexes = ("id_factura", "id_cuenta", "id_cliente", "numdoc")
                if self.list_data == dict() or self.filter != filter:
                    shelf = dict(self.shelf)
                    self.list_data = dict()
                    self.filter = filter
                    if "fecha_factura" in filter:
                        fechas_factura = filter["fecha_factura"].split(",")
                        filters = [filter.copy() for fecha_factura in fechas_factura]
                        [filters[index].update({"fecha_factura": fechas_factura[index]}) for index in range(len(filters))]
                    else:
                        filters = [filter]
                    template = {"numdoc": None,
                                "id_cliente": None,
                                "id_cuenta": None,
                                "segmento": None,
                                "id_factura": None,
                                "fecha_factura": None,
                                "importe_adeudado": None,
                                "estado_recibo": None
                                }
                    self.total_query = int()
                    self.ids_facturas = None
                    gc.collect()
                    if any(index in filter for index in main_indexes): #TODO: Redo
                        for index, id in enumerate(main_indexes):
                            if id in filter:
                                data = template.update()
                                try:
                                    data.update(dict(zip(shelf[id]["_heads"],
                                                         shelf[id]["data"][filter[id]])))
                                except ValueError:
                                    pass
                                else:
                                    while any(data[key] is None for key in template):
                                        for subfilter in main_indexes:
                                            if subfilter in data and data[subfilter] is not None:
                                                data.update(dict(zip(shelf[subfilter]["_heads"],
                                                                     shelf[subfilter]["data"][data[subfilter]])))
                                    if "facturas" in data and "id_factura" not in filter:
                                        subdata = data.copy()
                                        del(subdata["facturas"])
                                        for id_factura in data["facturas"]:
                                            subdata.update(dict(zip(shelf[subfilter]["_heads"],
                                                                    shelf["id_factura"]["data"][id_factura])))
                                            subdata = self.friend_fetch(subdata)
                                            if any([all([filter[field] == data[field] for field in data if field in filter])
                                                    for filter in filters]):
                                                del (subdata["facturas"])
                                                self.list_data[self.total_query] = subdata.copy()
                                                self.total_query += 1
                                    else:
                                        subdata = self.friend_fetch(data.copy())
                                        if any([all([filter[field] == data[field] for field in data if field in filter])
                                                for filter in filters]):
                                            self.list_data[self.total_query] = subdata
                                            self.total_query += 1
                                    break
                    elif self.ids_facturas is None:
                        self.ids_facturas = set()
                        for filter in filters:
                            ids = self.all.copy()
                            if any(field in filter for field in ("estado_recibo", "fecha_factura", "segmentos")):
                                if "estado_recibo" in filter and filter["estado_recibo"] in shelf["estados"]:
                                    ids &= shelf["index"]["estados"][filter["estado_recibo"]]
                                elif "estado_recibo" in filter:
                                    ids = set()
                                if "fecha_factura" in filter and filter["fecha_factura"] in shelf["index"]["fecha_factura"]:
                                    ids &= shelf["index"]["fecha_factura"][filter["fecha_factura"]]
                                elif "fecha_factura" in filter:
                                    ids = set()
                                #if "segmento" in filter and filter["segmento"] in shelf["segmentos"]:
                                #    ids &= shelf["index"]["segmentos"][filter["segmentos"]]
                            else:
                                ids = set()
                            self.ids_facturas |= ids
                        self.ids_facturas = list(self.ids_facturas)
                        self.ids_facturas.reverse() #From newer to older
                        self.total_query = len(self.ids_facturas)
                else:
                    pass
                if "page" in filter:
                    self.page = int(filter["page"])
                else:
                    self.page = 1
                if "items_per_page" in filter:
                    self.items_per_page = int(filter["items_per_page"])
                else:
                    self.items_per_page = 50
                len_data = len(self.list_data)
                ini = (self.page - 1) * self.items_per_page
                end = self.page * self.items_per_page
                if self.ids_facturas is not None and self.total_query > len_data:
                    if end > len(self.ids_facturas):
                        end = len(self.ids_facturas)
                    for index, id_factura in enumerate(self.ids_facturas[ini:end]):
                        if ini+index not in self.list_data:
                            data = template.copy()
                            data["id_factura"] = id_factura
                            while any(data[key] is None for key in template):
                                for subfilter in main_indexes:
                                    if subfilter in data and data[subfilter] is not None:
                                        data.update(dict(zip(shelf[subfilter]["_heads"],
                                                                 shelf[subfilter]["data"][data[subfilter]])))
                            self.list_data[ini+index] = self.friend_fetch(data.copy())
                try:
                    del(shelf)
                except UnboundLocalError:
                    pass
                gc.collect()
                if len(self.list_data) == 0:
                    data = []
                else:
                    data = [self.list_data[index] for index in range(ini, end)]
                return {"data": data,
                        "total": self.total_query,
                        "page": self.page,
                        "items_per_page": self.items_per_page}
            elif "reportes" in kwargs and kwargs["reportes"] is True:
                return {"data": self.shelf["reports"]}

    def friend_fetch(self, data):
        try:
            del(data["facturas"])
        except KeyError:
            pass
        data["fecha_factura"] = str(int.from_bytes(data["fecha_factura"], "big"))
        while len(data["fecha_factura"]) < 6:
            data["fecha_factura"] = "0" + data["fecha_factura"]
        fecha = data["fecha_factura"]
        data["fecha_factura"] = datetime.datetime.strptime(fecha, "%d%m%y").strftime("%d/%m/%y")
        data["segmento"] = self.shelf["segmentos"][int.from_bytes(data["segmento"], "big")]
        data["estado_recibo"] = self.shelf["estados"][int.from_bytes(data["estado_recibo"], "big")]
        return data
