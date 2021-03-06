from tkinter import *
from tkinter.ttk import *
from tkinter.font import Font, nametofont
from functools import partial
from zashel.utils import copy, paste, log
from collections import OrderedDict
import gc

__all__ = ["TkVars",
           "EasyFrame",
           "Frame"]

class TupleVar(tuple):
    def get(self):
        return self

class ListVar(list):  # TODO: define "append"
    def get(self):
        return self

class TkVars:
    reference = dict()

    def __init__(self, name, *, r=None, w=None, u=None):
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
                #print(".".join((str(self._name), str(item))) + ": " + str(value).replace("\u20ac", "Euro"))
                gc.collect()
            elif tk_var_class == dict:
                self._vars[item] = TkVars(item)
                for val in value:
                    self._vars[item].set(item, value[val])
            elif tk_var_class in (ListVar, TupleVar):
                final = list()
                tkvars = TkVars(".".join((self._name, item)))
                for index, val in enumerate(value):
                    final.append(tkvars.set(str(index), val))
                self._vars[item] = tk_var_class(final)
                #if tk_var_class == list:
                #    final.append = lambda value, name=self._vars[item]: tkvars.set(len(name), value)
                #TODO: Do an ad-hoc list

    def check_type(self, value):
        return {type(str()): StringVar,
                #type(int()): IntVar,
                #type(float()): DoubleVar,
                #type(bool()): BooleanVar,
                type(int()): StringVar, #This is going to be the problem!2
                type(float()): StringVar,
                type(bool()): StringVar,
                type(dict()): dict,
                type(list()): ListVar,
                type(tuple()): TupleVar
                }[type(value)]

    def set(self, name, value=None, *, r=None, w=None, u=None):
        if value == None:
            value = str()
        self.__setattr__(name, value)
        for method_name, method in (("r", r),
                                    ("w", w),
                                    ("u", u)):
            if type(self._vars[name]) in (ListVar, TupleVar):
                for index, item in enumerate(self._vars[name]):
                    if method is not None:
                        item.trace(method_name, partial(method, var_name=".".join((self._name, name, str(index)))))
            else:
                if method is not None:
                    self._vars[name].trace(method_name, partial(method, var_name=".".join((self._name, name))))
        return self.get(name)

    def get(self, name):
        return self.__getattr__(name)

TKFrame = Frame

class Frame(TKFrame):
    def __getattr__(self, item):
        try:
            return self.children[item]
        except KeyError:
            raise AttributeError

    def __getitem__(self, item):
        try:
            return TKFrame.__getitem__(self, item)
        except (KeyError, TclError):
            if "." not in item:
                if item in self.children:
                    return self.children[item]
            else:
                items = item.split(".")

                def get_item(item, names):
                    if len(names) > 0:
                        name = names[0]
                        try:
                            return get_item(item.children[name], names[1:])
                        except KeyError:
                            raise TclError
                    else:
                        return item

                return get_item(self, items)

    def all_children(self):
        _all = dict()
        for item in self.children:
            _all[item] = self.children[item]
            if isinstance(self.children[item], Frame) is True:
                infradata = self.children[item].all_children()
                for key in infradata:
                    _all["{}.{}".format(item, key)] = infradata[key] #Easier than I thought first. Thinking is the key.
        return _all


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
        self._popUp_data = [None, None, None, None]
        #self._popUp_variable = StringVar()
        self._popUp = None
        self._tree_calculations = dict()

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

    def LinkButton(self, parent=None, *args, font_size=9, **kwargs):
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
        button = Button(parent, *args, **config)
        return button

    def ImageButton(self, parent=None, image=None, *args, **kwargs):
        style = Style()
        style.configure("Image.TLabel")
        config = {"style": "Image-{}.TLabel"}
        config.update(kwargs)
        button = Button(parent, image=image, *args, **config)
        return button

    def Entry(self, route, parent=None, *args, **kwargs):
        try:
            var = self.get_var(route)
        except KeyError:
            var = self.set_var(route)
        last_entry_validation = (self.register(self.entered_entry), "%P", route)
        return Entry(parent, *args, textvariable=var, validate="all", validatecommand=last_entry_validation, **kwargs)

    def LabelEntry(self, route, text, parent=None, *args, labelargs=None, labelkwargs=None, entryargs=None, entrykwargs=None,
                   **kwargs):
        if labelargs is None:
            labelargs = list()
        if labelkwargs is None:
            labelkwargs = dict()
        if entryargs is None:
            entryargs = list()
        if entrykwargs is None:
            entrykwargs = dict()
        if "name" not in kwargs:
            kwargs["name"] = route.lower().replace(".", "_")
        if "name" not in labelkwargs:
            labelkwargs["name"] = "label"
        if "name" not in entrykwargs:
            entrykwargs["name"] = "entry"
        if parent is None:
            parent = self
        last_entry_validation = (self.register(self.entered_entry), "%P", route)
        frame = Frame(parent, *args, borderwidth=0, **kwargs)
        if not "anchor" in labelkwargs:
            labelkwargs["anchor"] = "e"
        labelkwargs.update({"text": text})
        Label(frame, *labelargs, **labelkwargs).grid(column=0, row=0, sticky="w")
        self.Entry(route, frame, *entryargs, **entrykwargs).grid(column=1, row=0, sticky="e")
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=2)
        return frame

    def Checkbutton(self, route, parent=None, *args, **kwargs):
        try:
            var = self.get_var(route)
        except KeyError:
            var = self.set_var(route)
        if "name" not in kwargs:
            kwargs["name"] = route.lower().replace(".", "_")
        last_entry_validation = partial(self.entered_entry, not var.get(), route)
        return Checkbutton(parent, *args, variable=var, command=last_entry_validation, **kwargs)

    def Combobox(self, route, values, parent=None, *args, **kwargs):
        try:
            var = self.get_var(route)
        except KeyError:
            var = self.set_var(route)
        if "name" not in kwargs:
            kwargs["name"] = route.lower().replace(".", "_")
        last_entry_validation = partial(self.entered_entry, var.get(), route)
        cb = Combobox(parent, *args, textvariable=var, values=values, **kwargs)
        cb.bind("<<ComboboxSelected>>", last_entry_validation)
        self._comboboxes[route] = cb
        return cb

    def TreeView(self, category, columns, parent=None, *args, default_config=None,
                 xscroll=False, yscroll=False, **kwargs):  # Columns -> dictionary
        if "name" not in kwargs:
            kwargs["name"] = category.lower().replace(".", "_")
        options = {"columns": tuple(columns)}
        options.update(kwargs)
        frame = Frame(parent)
        tree = Treeview(frame, *args, **options)
        tree.grid(row=0, column=0)
        if xscroll is True:
            xTreeScroll = Scrollbar(frame,
                                    orient=HORIZONTAL,
                                    command=tree.xview)
            tree["xscroll"] = xTreeScroll.set
            xTreeScroll.grid(row=1, column=0, sticky='ew')
        if yscroll is True:
            yTreeScroll = Scrollbar(frame,
                                    orient=VERTICAL,
                                    command=tree.yview)
            tree["yscroll"] = yTreeScroll.set
            yTreeScroll.grid(row=0, column=1, sticky='ns')
        activate_tree_item = partial(self.activate_tree_item, category)
        tree.bind("<<TreeviewSelect>>", activate_tree_item)
        if default_config is None:
            default_config = dict()
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
        if "editable" in default_config:
            if "comboboxes" not in default_config:
                default_config["comboboxes"] = dict()
            print(default_config["editable"])
            tree.bind("<Double-1>", partial(self.editable_tree_pop_entry, category, tree,
                                            default_config["editable"], default_config["comboboxes"]))
            tree.bind("<Button-1>", self.destroy_popUp)
        for item in columns:
            if item not in validate:
                validate[item] = lambda dato: dato
        assert all([item in validate for item in columns])
        self.tree[category] = {"template": list(columns),
                               "data": dict(),
                               "tree": tree,
                               "show": show,
                               "validate": validate,
                               "changed": list()}
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
                if column in default_config["heading"]:
                    tree.heading(column, **default_config["heading"][column])
        if "bind" in default_config:
            for item in default_config["bind"]:
                tree.bind(item, default_config["bind"][item])
        return frame

    def editable_tree_pop_entry(self, category, tree, editable_columns, comboboxes, event): #make a partial
        if self._popUp is not None and hasattr(self._popUp, "destroy"):
            self._popUp.destroy()
        assert isinstance(tree, Treeview)
        column = tree.column(tree.identify_column(event.x))["id"]
        if column in editable_columns:
            row = tree.identify_row(event.y)
            x, y, w, h = tree.bbox(row, column)
            pad = h // 2
            #data = tree.set(row, column)
            #last_entry_validation = (self.register(tree.set), row, column, "%P")
            var = self.get_var(".".join((category, column)))
            if column not in comboboxes:
                self._popUp = Entry(tree, textvariable=var)
            else:
                self._popUp = Combobox(tree, textvariable=var, values=comboboxes[column])
                print("OK?")
            #                    validate="all", validatecommand=last_entry_validation)
            #self._popUp_variable.set(data)
            self._popUp.place(x=x, y=y+pad, anchor=W)
            self._popUp_data = (category, row, column, var)
            self._popUp.bind("<Escape>", self.destroy_popUp)
            self._popUp.bind("<Return>", self.destroy_popUp)
            self._popUp.focus_set()

    def destroy_popUp(self, event=None):
        category, row, column, var = self._popUp_data
        if category is not None:
            tree = self.tree[category]["tree"]
            if hasattr(tree, "set"):
                if column in self.tree[category]["show"]:
                    data = self.tree[category]["show"][column](var.get())
                else:
                    data = var.get()
                try:
                    tree.set(row, column, data)
                except TclError:
                    pass
                self._popUp.destroy()
                if category in self._tree_calculations:
                    for function in self._tree_calculations[category]:
                        function()

    def set_combobox_values(self, route, values):
        assert type(values) in (list, tuple)
        self._comboboxes[route]["values"] = values

    def get_combobox_values(self, route):
        return self._comboboxes[route]["values"]

    def activate_tree_item(self, category, event):
        tree = self.tree[category]["tree"]
        item = tree.selection()[0]
        print(tree.selection())
        #template = self.tree[category]["template"]
        for field in self.tree[category]["data"][item]:
            self.set_var(".".join((category, str(field))), self.tree[category]["data"][item][field])

    def changed_active_tree_item(self, variable, void, method, *, var_name):
        category, name = self.get_category_and_name(var_name)
        tree = self.tree[category]["tree"]
        try:
            item = tree.selection()[0]
            data = self.get_var(var_name).get()
            if item not in self.tree[category]["data"]:
                self.tree[category]["data"][item] = dict()
            self.tree[category]["data"][item][name] = self.tree[category]["validate"][name](data)
            tree.set(item, name, self.tree[category]["show"][name](data))
            if item not in self.tree[category]["changed"]:
                self.tree[category]["changed"].append(item)
        except IndexError:
            pass

    def get_changed_tree_data(self, category):
        return [self.tree[category]["data"][item] for item in self.tree[category]["changed"]]

    def del_changed_tree_data(self, category):
        try:
            self.tree[category]["changed"] = list()
        except IndexError:
            pass

    def del_tree_data(self, category):
        tree = self.tree[category]["tree"]
        items = tree.get_children()
        for item in items:
            self.del_item_in_tree_data(category, item)

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

    def del_selected_item_in_tree_data(self, category):
        tree = self.tree[category]["tree"]
        item = tree.selection()[0]
        self.del_item_in_tree_data(category, item)

    def set_tree_data(self, category, data, order=None):
        assert category in self.tree
        self.del_tree_data(category)
        if type(data) in (list, tuple):
            final = OrderedDict()
            for index, item in enumerate(data):
                final[str(index+1)] = item
            data = final
        if order is None:
            order = list(data.keys())
        else:
            assert all([item in data for item in order])
        print("Order: ", order)
        for item in order:
            if item in data:
                self.append_to_tree_data(category, item, data[item])

    def set_tree_calculation(self, category, function):
        if category not in self._tree_calculations:
            self._tree_calculations[category] = list()
        self._tree_calculations[category].append(function)

    def append_to_tree_data(self, category, name, data={}, *args, **kwargs):  # _details in data creates a shitty subitem
        values = list()
        self.tree[category]["data"][name] = dict()
        for field in self.tree[category]["template"]:
            if field not in data:
                data[field] = str()
            values.append(self.tree[category]["show"][field](data[field]))
        self.tree[category]["data"][name] = data
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
