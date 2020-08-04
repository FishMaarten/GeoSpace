import os
directory = os.path.dirname(os.path.abspath(__file__))

class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "super-duper-secret"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        "sqlite:///" + os.path.join(directory, "dada.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

