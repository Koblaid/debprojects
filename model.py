from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from sqlalchemy import Table


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


class VcsType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False, unique=True)


tags = db.Table('maintainance',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
    db.Column('maintainer_id', db.Integer, db.ForeignKey('maintainer.id'))
)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(2000))
    documentation = db.Column(db.String(2000))
    documentation_url = db.Column(db.String(500))
    status = db.Column(db.String(20))
    maintainers = db.relationship('Maintainer', secondary='maintainance',
                                  backref=db.backref('projects'))

    vcs_url = db.Column(db.String(500))
    vcs_type = db.Column('vcs_type_id', db.Integer, db.ForeignKey('vcs_type.id'))

    number_of_commits = db.Column(db.Integer)
    number_of_authors = db.Column(db.Integer)
    number_of_files = db.Column(db.Integer)
    size_of_files = db.Column(db.Integer)
    first_commit = db.Column(db.DateTime)
    latest_commit = db.Column(db.DateTime)


class Maintainer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)


class Language(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     name = db.Column(db.Integer, unique=True, nullable=False)


class UsedLanguage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project = db.Column('project_id', db.Integer, db.ForeignKey('project.id'), nullable=False)
    language = db.Column('maintainer_id', db.Integer, db.ForeignKey('maintainer.id'), nullable=False)
    number_of_files = db.Column(db.Integer)
    code_lines = db.Column(db.Integer)
    comment_lines = db.Column(db.Integer)
    blank_lines = db.Column(db.Integer)


def insert_initial_data():
    db.session.add(VcsType(name='git'))
    db.session.add(VcsType(name='bzr'))
    db.session.add(VcsType(name='svn'))
    db.session.add(VcsType(name='hg'))
