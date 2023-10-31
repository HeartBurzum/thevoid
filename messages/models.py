import atexit
import os
import pathlib

from playhouse.sqliteq import SqliteQueueDatabase
from playhouse.sqlite_ext import CharField, ForeignKeyField, IntegerField, Model

a = os.path.realpath(__file__)
l = str(pathlib.Path(os.path.realpath(__file__)).parents[1].joinpath('databases', 'message_db.db'))
b = os.path.join(a, "..")
path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "/databases/message_db.db"))
db = SqliteQueueDatabase(
    str(pathlib.Path(os.path.realpath(__file__)).parents[1].joinpath('databases', 'message_db.db')),
    use_gevent=False,
    autostart=True,
    queue_max_size=64,
)

@atexit.register
def __stop_worker_threads():
    if not db.is_stopped():
        db.stop()


class Users(Model):
    discord_id = IntegerField()

    class Meta:
        database = db


class Messages(Model):
    uuid = CharField(unique=True)
    discord_message_id = IntegerField(null=True)
    user = ForeignKeyField(Users, backref='messages')

    class Meta:
        database = db
