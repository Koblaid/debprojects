import vcs_import
import model
import web



def reset_db():
    model.db.create_all()
    model.insert_initial_data()
    model.db.session.commit()


def import_csv():
    vcs_import.import_csv('debprojects.csv')
    model.db.session.commit()


def clone_repositories():
    vcs_import.clone_git_repositories('gits')


def init_admin(app):
    from flask.ext.admin.contrib.sqla import ModelView
    from flask.ext.admin import Admin
    admin = Admin(app)
    admin.add_view(ModelView(model.Project, model.db.session))
    admin.add_view(ModelView(model.Repository, model.db.session))
    admin.add_view(ModelView(model.Maintainer, model.db.session))
    admin.add_view(ModelView(model.Language, model.db.session))
    admin.add_view(ModelView(model.UsedLanguage, model.db.session))


def run_website():
    init_admin(web.app)
    web.app.run(debug=True)


import os
#os.unlink('test.db')
#reset_db()
#import_csv()
#clone_repositories()
#vcs_import.analyse_git_repositories('gits')
#model.db.session.commit()
run_website()
