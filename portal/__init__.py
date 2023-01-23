import os
import logging
from functools import wraps
from logging import Formatter
from logging.handlers import RotatingFileHandler
from flask import Flask, session, redirect, url_for
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

APP = None
WORKER_ID = 0
LOG = logging


def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        username = session.get('user')
        if bool(username):
            return test(*args, **kwargs)
        else:
            return redirect(url_for('view.login'))

    return wrap


def uwsgi_friendly_setup(app):
    global WORKER_ID

    try:
        import uwsgi
        WORKER_ID = uwsgi.worker_id()
    except ImportError:
        pass
        # During development on local machine, we may use `flask run` command
        # in this case, uwsgi package won't be available and it will throw error



def get_config_file_path():
    env = os.getenv("BACKEND_ENV", default="development")
    base = os.path.dirname(os.path.abspath(__file__))
    absolute_path = os.path.abspath(os.path.join(base, '..', 'config', env + '.py'))
    return absolute_path


def is_development():
    env = os.getenv("BACKEND_ENV", default="development")
    if env in ["development", "sit"]:
        return True
    return False


def init_logger(app):
    """
    Initializing the logging functionality within the app context
    :param app:
    :return: None
    """
    global LOG
    if not os.path.exists(app.config["LOG_DIR"]):
        os.mkdir(app.config["LOG_DIR"])
    log_file = os.path.join(app.config['LOG_DIR'], 'backend.log')
    log_level = app.config['LOG_LEVEL']
    log_format = Formatter(f"[%(asctime)s][worker-{WORKER_ID}][%(levelname)s] %(message)s")

    TWO_MEGABYTE = 2_000_000
    file_handler = RotatingFileHandler(filename=log_file, maxBytes=TWO_MEGABYTE, backupCount=10)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(log_format)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)
    LOG = app.logger
    # print(app.logger.isEnabledFor(log_level))
    LOG.info('Initialized logger with level %s for worker %s', log_level, WORKER_ID)


def init_routes(app):
    from .views import bp
    app.register_blueprint(bp)


def init_security(app):
    csp = {
        'default-src': [
            '\'self\''
        ],
        'img-src': [
            '\'self\'',
            'data:',
        ],
        'media-src': [
            "'self'",
        ],
        'style-src': ['\'self\'', "'unsafe-inline'", 'https://fonts.googleapis.com/', 'https://cdnjs.cloudflare.com/', 'https://cdn.datatables.net', 'nonce'],
        'script-src': ['\'self\'', "'unsafe-inline'", 'https://fonts.googleapis.com/', 'https://www.google-analytics.com', 'https://cdnjs.cloudflare.com/'],
        'font-src': ['\'self\'', "'unsafe-inline'", 'https://fonts.googleapis.com/', 'https://fonts.gstatic.com', 'https://cdnjs.cloudflare.com/'],
        'frame-ancestors': ["'self'"],
        'frame-src': ["'self'"]
    }
    # t = Talisman(app, content_security_policy=csp)
    # t.force_https = False
    # t.force_https_permanent = False
    # t.session_cookie_secure = False

def init_cors(app):
    CORS(app=app, origins=app.config['CORS_ORIGIN_WHITELIST'], allow_headers=app.config['CORS_HEADERS'])
    LOG.info('Initialized CORS')


def create_app():
    global APP

    if APP is not None:
        return APP

    APP = Flask(__name__, static_url_path='/static')
    APP.debug = True

    uwsgi_friendly_setup(APP)
    APP.wsgi_app = ProxyFix(APP.wsgi_app, x_for=1, x_host=1)

    config_file_path = get_config_file_path()
    if config_file_path is not None:
        if isinstance(config_file_path, dict):
            APP.config.update(config_file_path)
        elif config_file_path.endswith('.py'):
            APP.config.from_pyfile(config_file_path)

    init_logger(APP)
    try:
        init_routes(APP)
        init_cors(APP)
        init_security(APP)
    except Exception as e:
        LOG.error('An error happened during initializing app components: %s', e)
        raise

    APP.logger.info('App Initialization is finished successfully')
    return APP
