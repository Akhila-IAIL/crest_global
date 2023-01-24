from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_app(app):
    db_connection_string = app.config["DB_CONNECTION_STRING"]
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_BINDS'] = {
        'db': db_connection_string
    }
    app.config['SQLALCHEMY_DATABASE_URI'] = db_connection_string
    db.init_app(app)
    app.logger.info('Initialized models')
    with app.app_context():
        from .add_ons_mst import AddOnsMST
        db.create_all()
        db.session.commit()
        app.logger.info("All the tables are created")
