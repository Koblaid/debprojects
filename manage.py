import vcs_import
import model

def reset_db():
    model.db.create_all()
    model.insert_initial_data()
    model.db.session.commit()


def import_csv():
    vcs_import.import_csv('debprojects.csv')
    model.db.session.commit()


def clone_repositories():
    vcs_import.clone_git_repositories('gits1')

#import os
#os.unlink('test.db')
#reset_db()
#import_csv()
clone_repositories()
