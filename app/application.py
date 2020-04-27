import os

from app.sso.register import register_sso_component

config_location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__), 'config'))


def register_app_components(flask_app):
    return register_sso_component(flask_app, role_based=False)
