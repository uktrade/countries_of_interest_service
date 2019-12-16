import os

from authbroker_client import authbroker_blueprint

from celery import Celery

from flask import Flask, json

import redis

from sqlalchemy.engine.url import make_url

from app import config


def make_celery(flask_app):
    cache_backend = _get_redis_url(flask_app)
    flask_app.config['broker_url'] = f"{cache_backend}/0"
    flask_app.config['result_backend'] = f"{cache_backend}/0"
    celery = Celery('application')

    celery.conf.broker_transport_options = {
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    }
    celery.conf.update(flask_app.config)
    return celery


def get_or_create():
    from flask import current_app as flask_app

    if not flask_app:
        flask_app = _create_base_app()
    return flask_app


def make_current_app_test_app(test_db_name):
    flask_app = get_or_create()
    postgres_db_config = (
        os.environ.get('DATABASE_URL')
        if 'DATABASE_URL' in os.environ
        else config.get_config()['app']['database_url']
    )
    flask_app.config.update(
        {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': _create_sql_alchemy_connection_str(
                postgres_db_config, test_db_name
            ),
        }
    )
    return flask_app


def _create_base_app():
    flask_app = Flask(__name__)
    flask_app.config.update(config.get_config())

    postgres_db_config = (
        os.environ.get('DATABASE_URL')
        if 'DATABASE_URL' in os.environ
        else config.get_config()['app']['database_url']
    )
    flask_app.config.update(
        {
            'TESTING': False,
            'SQLALCHEMY_DATABASE_URI': _create_sql_alchemy_connection_str(
                postgres_db_config
            ),
            # set SQLALCHEMY_TRACK_MODIFICATIONS to False because
            # default of None produces warnings, and track modifications
            # are not required
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        }
    )

    flask_app.config['ABC_BASE_URL'] = flask_app.config['sso']['host']
    flask_app.config['ABC_CLIENT_ID'] = flask_app.config['sso']['abc_client_id']
    flask_app.config['ABC_CLIENT_SECRET'] = flask_app.config['sso']['abc_client_secret']
    flask_app.secret_key = flask_app.config['app']['secret_key']
    from app.api.settings import CustomJSONEncoder

    flask_app.json_encoder = CustomJSONEncoder
    celery = make_celery(flask_app)
    flask_app.celery = celery
    flask_app = _register_components(flask_app)
    return flask_app


def _register_components(flask_app):
    from app.api.views import api

    # Postgres DB
    from app.db import sql_alchemy

    sql_alchemy.session = sql_alchemy.create_scoped_session()
    sql_alchemy.init_app(flask_app)
    flask_app.db = sql_alchemy

    # API
    flask_app.register_blueprint(api)
    flask_app.register_blueprint(authbroker_blueprint)

    # Cache
    flask_app.cache = redis.from_url(_get_redis_url(flask_app))
    return flask_app


def _get_redis_url(flask_app):
    redis_uri = _load_uri_from_vcap_services('redis')
    if not redis_uri:
        password = flask_app.config['cache'].get('password')
        redis_uri = (
            f"user:{password}"
            if password
            else ""
            f"{flask_app.config['cache']['host']}:"
            f"{flask_app.config['cache']['port']}"
        )
    return redis_uri


def _load_uri_from_vcap_services(service_type):
    if 'VCAP_SERVICES' in os.environ:
        vcap_services = os.environ.get('VCAP_SERVICES')
        services = json.loads(vcap_services)
        if service_type in services:
            services_of_type = services[service_type]
            for service in services_of_type:
                if 'credentials' in service:
                    if 'uri' in service['credentials']:
                        return service['credentials']['uri']
    return None


def _create_sql_alchemy_connection_str(cfg, db_name=None):
    url = make_url(cfg)
    if db_name:
        url.database = db_name
    return url


app = get_or_create()
celery_app = app.celery