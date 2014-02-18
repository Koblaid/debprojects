from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from sqlalchemy import Table


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


class RepositoryType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False, unique=True)


class Repository(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    repository_type = db.Column('repository_type_id', db.Integer, db.ForeignKey('repository_type.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False, unique=True)
    webview_url = db.Column(db.String(500))


maintainance = db.Table('maintainance',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
    db.Column('maintainer_id', db.Integer, db.ForeignKey('maintainer.id'))
)


project_repository = db.Table('project_repository',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
    db.Column('repository_id', db.Integer, db.ForeignKey('repository.id'))
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
    repositories = db.relationship('Repository', secondary='project_repository',
                                  backref=db.backref('projects'))

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
    repository = db.Column('repository_id', db.Integer, db.ForeignKey('repository.id'), nullable=False)
    language = db.Column('maintainer_id', db.Integer, db.ForeignKey('maintainer.id'), nullable=False)
    number_of_files = db.Column(db.Integer)
    code_lines = db.Column(db.Integer)
    comment_lines = db.Column(db.Integer)
    blank_lines = db.Column(db.Integer)


def insert_initial_data():
    db.session.add(RepositoryType(name='git'))
    db.session.add(RepositoryType(name='bzr'))
    db.session.add(RepositoryType(name='svn'))
    db.session.add(RepositoryType(name='hg'))
