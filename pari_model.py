from zrest.basedatamodel import RestfulBaseInterface
import gc
import shelve
import os
from definitions import *


class Pari(RestfulBaseInterface):
    def __init_(self, filepath):
        super().__init__()
        self._filepath = filepath
        path, filename = os.path.split(self.filepath)
        if not os.path.exists(path)
            os.makedirs(path)
        self._shelf = shelve.open(self.filepath)
        try:
            self._loaded_file = self.shelf["file"]
        except KeyError:
            self._file = None
        self._name = None

    @property
    def filepath(self):
        return self._filepath

    @property
    def shelf(self):
        return self._shelf

    @property
    def name(self):
        return self._name

    @property
    def loaded_file(self):
        return self._loaded_file