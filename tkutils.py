from tkinter import *
from tkinter.ttk import *
from tkinter.font import Font, nametofont
from functools import partial
from zashel.utils import copy, paste
import gc

__all__ = ["TkVars",
           "EasyFrame"]

class TkVars:
    reference = dict()

    def __init__(self, name, r=None, w=None, u=None):
        self._vars = dict()
        self._name = name
        self._bindings = dict()
        self.r = r
        self.w = w
        self.u = u

    def __getattr__(self, item):
        if item in self._vars:
            return self._vars[item]
        else:
            raise KeyError()

    def __setattr__(self, item, value):
        if item in ("_vars", "_name", "_bindings", "r", "w", "u"):
            object.__setattr__(self, item, value)
        else:
            if value is None:
                value = str()
            try:
                tk_var_class = self.check_type(value)
            except KeyError:
                print(value)
                print(type(value))
                raise ValueError
            if issubclass(tk_var_class, Variable):
                if (item not in self._vars or
                        (item in self._vars and not isinstance(self._vars[item], tk_var_class))):
                    self._vars[item] = tk_var_class()
                for method in "rwu":
                    try:
                        data = self.__getattr__(method)
                    except KeyError:
                        data = None
                    if data is not None:
                        self._vars[item].trace(method,
                                               partial(self.__getattr__(method),
                                                       var_name=".".join((self._name, item))))
                    if item in self._bindings and method in self._bindings[item]:
                        self._vars[item].trace(method,
                                               partial(self._bindings[item][method],
                                                       var_name=".".join((self._name, item))))
                self._vars[item].set(value)
                print(".".join((self._name, item)) + ": " + str(value))
                gc.collect()
            elif tk_var_class == dict:
                self._vars[item] = TkVars(item)
                for val in value:
                    self._vars[item].set(item, value[val])
            elif tk_var_class in (list, tuple):
                final = list()
                tkvars = TkVars(".".join((self._name, item)))
                for index, val in enumerate(value):
                    final.append(tkvars.set(index, val))
                if tk_var_class == list:
                    final.append = lambda value, name=self._vars[item]: tkvars.set(len(name), value)

    def check_type(self, value):
        return {type(str()): StringVar,
                type(int()): IntVar,
                type(float()): DoubleVar,
                type(bool()): BooleanVar,
                type(dict()): dict,
                type(list()): list,
                type(tuple()): tuple
                }[type(value)]

    def set(self, name, value=None, *, r=None, w=None, u=None):
        if value == None:
            value = str()
        self.__setattr__(name, value)
        for method in "rwu":
            try:
                data = self.__getattr__(method)
            except KeyError:
                data = None
            if data is not None:
                self._vars[name].trace(method, partial(self.__getattr__(method), var_name=".".join((self._name, name))))

    def get(self, name):
        return self.__getattr__(name)


class EasyFrame(Frame):
    def __init__(self, *args, master=None, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.to_save = dict()
        self.clean_to_save()
        self._undo = {"var": None,
                      "last": None}
        self._vars = dict()
        self._tree = dict()
        self._comboboxes = dict()

    @property
    def vars(self):
        return self._vars

    @property
    def tree(self):
        return self._tree

    def set_widgets(self):
        pass

    def set_menu(self):
        pass

    def set_var(self, route, value=None, *, r=None, w=None, u=None):
        cat, name = self.get_category_and_name(route)
        if cat not in self._vars:
            self._vars[cat] = TkVars(cat)
        self._vars[cat].set(name, value, r=r, w=w, u=u)
        return self._vars[cat].get(name)

    def get_var(self, route):
        cat, name = self.get_category_and_name(route)
        if cat not in self._vars:
            raise KeyError()
        return self._vars[cat].get(name)

    def del_category(self, category):
        if category not in self._vars:
            raise KeyError()
        del (self._vars[category])
        gc.collect

    def LinkButton(self, *args, font_size=9, **kwargs):
        font = Font(family = nametofont("TkDefaultFont").cget("family"),
                    size = font_size,
                    underline=True)
        style = Style()
        style.configure("Linked.TLabel",
                        foreground="#0645AD",
                        font=font)
        config = {"style": "Linked-{}.TLabel",
                  "cursor": "hand2"}
        config.update(kwargs)
        button = Button(*args, **config)
        return button

    def Entry(self, route, *args, **kwargs):
        try:
            var = self.get_var(route)
        except KeyError:
            var = self.set_var(route)
        last_entry_validation = (self.register(self.entered_entry), "%P", route)
        return Entry(*args, textvariable=var, validate="all", validatecommand=last_entry_validation, **kwargs)

    def Checkbutton(self, route, *args, **kwargs):
        try:
            var = self.get_var(route)
        except KeyError:
            var = self.set_var(route)
        last_entry_validation = partial(self.entered_entry, not var.get(), route)
        return Checkbutton(*args, variable=var, command=last_entry_validation, **kwargs)

    def Combobox(self, route, values, *args, **kwargs):
        try:
            var = self.get_var(route)
        except KeyError:
            var = self.set_var(route)
        last_entry_validation = partial(self.entered_entry, var.get(), route)
        cb = Combobox(*args, textvariable=var, values=values, **kwargs)
        cb.bind("<<ComboboxSelected>>", last_entry_validation)
        self._comboboxes[route] = cb
        return cb

    def TreeView(self, category, columns, *args, default_config=None, **kwargs):  # Columns -> dictionary
        options = {"columns": tuple(columns)}
        options.update(kwargs)
        tree = Treeview(*args, **options)
        activate_tree_item = partial(self.activate_tree_item, category)
        tree.bind("<<TreeviewSelect>>", activate_tree_item)
        if "show" not in default_config:
            show = dict()
        else:
            show = default_config["show"]
        for item in columns:
            if item not in show:
                show[item] = lambda dato: dato
        assert all([item in show for item in columns])
        if "validate" not in default_config:
            validate = dict()
        else:
            validate = default_config["validate"]
        for item in columns:
            if item not in validate:
                validate[item] = lambda dato: dato
        assert all([item in validate for item in columns])
        self.tree[category] = {"template": list(columns),
                               "data": list(),
                               "tree": tree,
                               "show": show,
                               "validate": validate}
        for column in columns+["#0"]:
            if column != "#0":
                self.set_var(".".join((category, str(column))), None, w=self.changed_active_tree_item)
            if "columns" in default_config:
                column_config = dict(default_config["columns"])
            else:
                column_config = dict()
            if "column" in default_config and column in default_config["column"]:
                column_config.update(default_config["column"][column])
            tree.column(column, **column_config)
            if "heading" in default_config:
                tree.heading(column, **default_config["heading"][column])
        if "bind" in default_config:
            for item in default_config["bind"]:
                tree.bind(item, default_config["bind"][item])
        return tree

    def set_combobox_values(self, route, values):
        assert type(values) in (list, tuple)
        self._comboboxes[route]["values"] = values

    def get_combobox_values(self, route):
        return self._comboboxes[route]["values"]

    def activate_tree_item(self, category, event):
        tree = self.tree[category]["tree"]
        item = tree.selection()[0]
        template = self.tree[category]["template"]
        for field in template:
            self.set_var(".".join((category, str(field))), tree.set(item, field))

    def changed_active_tree_item(self, variable, void, method, *, var_name):
        category, name = self.get_category_and_name(var_name)
        self.tree[category]["data"][name] = self.get_var(var_name).get()
        tree = self.tree[category]["tree"]
        item = tree.selection()[0]
        tree.set(self.tree[category]["validate"][name](item, name, self.get_var(var_name).get()))

    def del_tree_data(self, category):
        all = list()
        for item in self.tree[category]["data"]:
            all.append(item)
        [self.del_item_in_tree_data(category, item) for item in all]

    def del_item_in_tree_data(self, category, item):
        self.tree[category]["tree"].delete(item)
        if item in self.tree[category]["data"]:
            try:
                del (self.tree[category]["data"][item])
            except TclError:
                pass
        if "." in str(item):
            nombre, item = item.split(".")
            if (nombre in self.tree[category]["data"] and
                        "_details" in self.tree[category]["data"][nombre] and
                        item in self.tree[category]["data"][nombre]["_details"]):
                try:
                    del (self.tree[category]["data"][nombre]["_details"][item])
                except TclError:
                    pass

    def set_tree_data(self, category, data, order=None):
        assert category in self.tree
        self.del_tree_data(category)
        if order is None:
            order = list(data.keys())
            order.sort()
        else:
            assert all([item in data for item in order])
        self.tree[category]["data"] = data
        for item in order:
            if item in data:
                self.append_to_tree_data(category, item, data[item])

    def append_to_tree_data(self, category, name, data):  # _details in data creates a shitty subitem
        values = list()
        for field in self.tree[category]["template"]:
            if field not in data:
                data[field] = str()
            values.append(self.tree[category]["show"][field](data[field]))
        self.tree[category]["tree"].insert("", END, name, text=name, values=values)
        if "_details" in data:
            for item in data["_details"]:
                self.append_details_to_tree_item(category, name, item, data["_details"][item])

    def append_details_to_tree_item(self, category, name, item, data):
        values = list()
        for field in self.tree[category]["template"]:
            if field not in data["_details"][item]:
                data["_details"][item][field] = str()
            values.append(data["_details"][item])
        self.tree[category]["tree"].insert(name, END, ".".join(name, item), text=item, values=values)

    def clean_to_save(self, category=None):
        template = {"old": dict(),
                    "var": dict()}
        if category is None:
            for category in self.to_save:
                self.to_save[category] = dict(template)
        else:
            self.to_save[category] = dict(template)

    def save_and_close(self, category, dialog):
        self.save(category)
        dialog.destroy()

    def get_category_and_name(self, route):
        route = route.split(".")
        category, name = ".".join(route[:-1]), route[-1]
        return (category, name)

    def entered_entry(self, value, route, *args, **kwargs):
        cat, item = self.get_category_and_name(route)
        var = self.get_var(route)
        if cat not in self.to_save:
            self.clean_to_save(cat)
        if not item in self.to_save[cat]["old"]:
            self.to_save[cat]["old"][item] = value
        if not item in self.to_save[cat]["var"]:
            self.to_save[cat]["var"][item] = var
        if self._undo["var"] != var:
            self._undo["var"] = var
            self._undo["last"] = value
        return True

    def undo(self):
        self._undo["var"].set(self._undo["last"])

    def copy(self):
        copy(self.master.selection_get())

    def cut(self):
        self.copy()
        self.master.selection_own_get().delete(SEL_FIRST, SEL_LAST)

    def paste(self):
        self.master.focus_get().insert(INSERT, paste())

    def save(self, category):
        try:
            save = self.__getattribute__("save_{}".format(category))
        except AttributeError:
            raise
        save()
        self.clean_to_save(category)

    def category(self, category):
        return list(self.to_save[category]["var"].keys())

    def get_var_in_category(self, category, name):
        return self.get_var(".".join((category, name)))

    def clean_changes(self, category):
        for item in self.to_save[category]["var"]:
            if item in self.to_save[category]["old"]:
                self.to_save[category]["var"][item].set(self.to_save[category]["old"][item])