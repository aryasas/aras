from run import app
with app.app_context():
    print(app.config['SQLALCHEMY_DATABASE_URI'])
