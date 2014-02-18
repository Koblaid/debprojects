from model import db

def reset_db():
    db.create_all()


reset_db()
