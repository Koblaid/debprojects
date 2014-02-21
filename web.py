from flask import Flask, render_template

import model as m


app = Flask(__name__)


@app.route('/')
def index():
    projects = m.Project.query.all()
    return render_template('index.html', projects=projects)
