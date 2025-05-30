import os

class Config(object):
    USER=os.environ.get('POSTGRES_USER','sasha')
    PASSWORD=os.environ.get('POSTGRES_PASSWORD', 'password')
    HOST=os.environ.get('POSTGRES_HOST', '127.0.0.1') 
    PORT=os.environ.get('POSTGRES_PORT', '5532')
    DB=os.environ.get('POSTGRES_DB', 'db_vkr')

    SQLALCHEMY_DATABASE_URI = f'postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}'
    SECRET_KEY = 'ferf5453rfrqwrs34t46245rf2454tfwrge'
    SQLALCHEMY_TRACK_MODIFICATIONS = True