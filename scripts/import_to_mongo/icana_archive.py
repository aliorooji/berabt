import os
from lib.mongo.databases import Icana
import ijson


class Importer:
    def __init__(self, filepath):
        if not os.path.isfile(filepath):
            raise ValueError("File path is not valid.")

        self.filepath = filepath

    def import_to_db(self):
        file = open(self.filepath)
        items = ijson.items(file, "item")
        db = Icana()
        db.archive_raw.insert_many(items)
