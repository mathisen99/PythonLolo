import datetime
import peewee
import config
from shared.logger import setup_logger

# Peewee database and models
db = peewee.SqliteDatabase(config.DB_PATH)

class BaseModel(peewee.Model):
    class Meta:
        database = db

class User(BaseModel):
    hostmask = peewee.CharField(unique=True)
    nick = peewee.CharField()
    level = peewee.CharField()
    added_at = peewee.DateTimeField(default=datetime.datetime.now)

class Log(BaseModel):
    timestamp = peewee.DateTimeField(default=datetime.datetime.now)
    hostmask = peewee.CharField()
    nick = peewee.CharField()
    target = peewee.CharField()
    message = peewee.TextField()

class ChannelSetting(BaseModel):
    channel = peewee.CharField(unique=True)
    prefix = peewee.CharField(default="!")
    disabled_commands = peewee.TextField(default="")  # comma-separated

class SchemaVersion(BaseModel):
    version = peewee.IntegerField()
    applied_at = peewee.DateTimeField(default=datetime.datetime.now)

logger = setup_logger("logic_server.db")

def init_db():
    # connect and create tables if missing
    db.connect(reuse_if_open=True)
    # include ChannelSetting and SchemaVersion for per-channel settings and migrations
    db.create_tables([User, Log, ChannelSetting, SchemaVersion], safe=True)
    # initialize schema version if absent
    if not SchemaVersion.select().exists():
        SchemaVersion.create(version=1)
    # run pending migrations
    run_migrations()

# User-level operations

def add_user(hostmask: str, nick: str, level: str):
    # insert or update user entry
    User.replace(hostmask=hostmask, nick=nick, level=level).execute()

def remove_user(hostmask: str):
    User.delete().where(User.hostmask == hostmask).execute()

def get_user_level(hostmask: str) -> str:
    try:
        u = User.get(User.hostmask == hostmask)
        return u.level
    except User.DoesNotExist:
        return "Normal"

# Logging operations

def log_message(hostmask: str, nick: str, target: str, message: str):
    Log.create(hostmask=hostmask, nick=nick, target=target, message=message)

# Channel-specific configuration

def get_channel_setting(channel: str) -> ChannelSetting:
    cs, _ = ChannelSetting.get_or_create(channel=channel)
    return cs

def get_prefix(channel: str) -> str:
    return get_channel_setting(channel).prefix

def is_command_enabled(channel: str, cmd_name: str) -> bool:
    cs = get_channel_setting(channel)
    disabled = [c.strip() for c in cs.disabled_commands.split(",") if c.strip()]
    return cmd_name not in disabled

def set_prefix(channel: str, prefix: str):
    cs = get_channel_setting(channel)
    cs.prefix = prefix
    cs.save()

def disable_command(channel: str, cmd: str):
    cs = get_channel_setting(channel)
    disabled = set([c.strip() for c in cs.disabled_commands.split(",") if c.strip()])
    disabled.add(cmd)
    cs.disabled_commands = ",".join(sorted(disabled))
    cs.save()

def enable_command(channel: str, cmd: str):
    cs = get_channel_setting(channel)
    disabled = set([c.strip() for c in cs.disabled_commands.split(",") if c.strip()])
    disabled.discard(cmd)
    cs.disabled_commands = ",".join(sorted(disabled))
    cs.save()

# Migration helpers
def get_schema_version() -> int:
    sv = SchemaVersion.select().order_by(SchemaVersion.version.desc()).first()
    return sv.version if sv else 0

def set_schema_version(version: int):
    SchemaVersion.create(version=version)

# Migration framework
MIGRATIONS: dict[int, callable] = {}

def migration(version: int):
    """Decorator to register a migration function for a schema version"""
    def decorator(func: callable):
        MIGRATIONS[version] = func
        return func
    return decorator

def run_migrations():
    """Apply all migrations with version greater than current"""
    current = get_schema_version()
    for version in sorted(MIGRATIONS):
        if version > current:
            logger.info(f"Applying migration {version}")
            MIGRATIONS[version]()
            set_schema_version(version)
