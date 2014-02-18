import vcs_import
import model

def reset_db():
    model.db.create_all()
    model.insert_initial_data()
    model.db.session.commit()


def import_csv():
    vcs_import.import_csv('debprojects.csv')
    model.db.session.commit()


import os
#os.unlink('test.db')
reset_db()
import_csv()
