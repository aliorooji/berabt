from pymongo import MongoClient

mongo_client = MongoClient()


class DB:
    @property
    def db(self):
        try:
            return mongo_client[self.db_name]
        except AttributeError:
            raise AttributeError("Please prepare db_name.")


class Icana(DB):
    db_name = "icana"

    @property
    def archive_raw(self):
        return self.db.archive_raw
