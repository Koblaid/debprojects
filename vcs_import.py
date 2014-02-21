import csv
import subprocess
import os
import json
import StringIO
from contextlib import contextmanager

from dateutil import parser, tz

import model as m


# http://ralsina.me/weblog/posts/BB963.html
@contextmanager
def cd(path):
     old_dir = os.getcwd()
     os.chdir(path)
     try:
         yield
     finally:
         os.chdir(old_dir)


def _parse_repository(row, line_num):
    repo_urls = row['repository_url'].strip().split('\n') if row['repository_url'] else []
    repo_types = row['repository_type'].strip().split('\n') if row['repository_type'] else []
    repo_webview_urls = row['repository_webview_url'].strip().split('\n') if row['repository_webview_url'] else []

    if len(repo_urls) != len(repo_types):
        raise Exception('Error in line %s: Number of lines in repository_url must match number of entries in repository_type' % line_num+1)
    if repo_webview_urls and len(repo_urls) != len(repo_webview_urls):
        raise Exception('Error in line %s: Number of lines in repository_url must match number of entries in repository_webview_url' % line_num)

    repos = []
    for i in xrange(len(repo_urls)):
        repos.append(dict(
            url=repo_urls[i],
            repository_type=repo_types[i],
            webview_url=repo_webview_urls[i] if repo_webview_urls else None
        ))
    return repos



def import_csv(filepath):
    repo_types = {}
    for repo_type in m.RepositoryType.query.all():
        repo_types[repo_type.name] = repo_type

    with open(filepath) as f:
        r = csv.DictReader(f)
        for i, row in enumerate(r):
            project = m.Project()
            project.name = row['name']
            project.description = row['description'] or None
            project.documentation = row['documentation'] or None
            project.documentation_url = row['documentation_url'] or None
            project.status = row['status'] or None


            for repo_dict in _parse_repository(row, i):
                repo = m.Repository.query.filter_by(url=repo_dict['url']).first()
                if not repo:
                    repo_type_id = repo_types[repo_dict['repository_type']].id
                    repo = m.Repository(url=repo_dict['url'],
                                        repository_type=repo_type_id,
                                        webview_url=repo_dict['webview_url'])

                project.repositories.append(repo)

            for maintainer_name in row['maintainers'].split('\n'):
                maintainer_name = maintainer_name.strip()
                if not maintainer_name:
                    continue

                maintainer = m.Maintainer.query.filter_by(name=maintainer_name).first()
                if not maintainer:
                    maintainer = m.Maintainer()
                    maintainer.name = maintainer_name

                project.maintainers.append(maintainer)

            m.db.session.add(project)
            m.db.session.commit()


def get_git_repository_name(git_url):
    return os.path.splitext(os.path.basename(git_url))[0]


def clone_git_repositories(path):
    for repo in m.get_git_repositories():
        url = repo.url.replace('git://', 'http://')
        outpath = os.path.join(path, get_git_repository_name(url))
        if os.path.exists(outpath):
            print 'Folder %s already present, skipping' % outpath
            continue

        try:
            print subprocess.check_output(['git', 'clone', url, outpath])
        except Exception, e:
            print e


def analyse_git_repositories(path):
    for repo in m.get_git_repositories():
        full_path = os.path.join(path, get_git_repository_name(repo.url))
        if not os.path.isdir(full_path):
            print 'Folder %s not found, skipping' % full_path
            continue

        with cd(full_path):
            utc_zone = tz.tzutc()

            first = subprocess.check_output(["git rev-list --format=format:'%ai' --max-count=1 `git rev-list --max-parents=0 HEAD`"], shell=True)
            repo.first_commit_date_utc = parser.parse(first.splitlines()[1]).astimezone(utc_zone).replace(tzinfo=None)

            latest = subprocess.check_output(["git rev-list --format=format:'%ai' --max-count=1 `git rev-parse HEAD`"], shell=True)
            repo.latest_commit_date = parser.parse(latest.splitlines()[1]).astimezone(utc_zone).replace(tzinfo=None)

            repo.number_of_authors = subprocess.check_output(["git shortlog -sn | wc -l"], shell=True).strip()

            repo.number_of_commits = subprocess.check_output(["git log --oneline | wc -l"], shell=True).strip()

            repo.number_of_files = subprocess.check_output(["git ls-files | wc -l"], shell=True).strip()

            output = subprocess.check_output(["du -s --exclude=.git/*"], shell=True)
            repo.size_of_files = output.split()[0]

        cmd = 'cloc --not-match-f="jquery.*\.js" --ignored=%s-ignored.txt --csv --quiet %s' % (repo_dir, full_path)
        output = subprocess.check_output([cmd], shell=True)
        csv_string = output.split('\n\n')[1]
        rows = csv.DictReader(StringIO.StringIO(csv_string))

        stats['languages'] = {}
        for row in rows:
            stats['languages'][row['language']] = dict(
                files=row['files'],
                comment=row['comment'],
                code=row['code'],
                blank=row['blank'],
            )

        all_stats[repo_dir] = stats


    with open('all.json', 'w') as out_f:
        out_f.write(json.dumps(all_stats))


def json_to_csv():
    with open('all.json') as f:
        all_stats = json.loads(f.read())

    languages = set()
    for k, v in all_stats.iteritems():
        langs = v.pop('languages')
        languages.update(langs.keys())

        bash = langs.pop('Bourne Again Shell', None)
        if 'Bourne Again Shell' in langs:
            sh = langs['Bourne Shell']
            sh['files'] += bash['files']
            sh['comment'] += bash['comment']
            sh['code'] += bash['code']
            sh['blank'] += bash['blank']

        for lang_name, lang_dict in langs.iteritems():
            v[lang_name + ' files'] = lang_dict['files']
            v[lang_name + ' comment'] = lang_dict['comment']
            v[lang_name + ' code'] = lang_dict['code']
            v[lang_name + ' blank'] = lang_dict['blank']

        v['name'] = k

    fields = ['name', 'number_of_commits', 'number_of_authors', 'number_of_files', 'size_of_files', 'first_commit', 'latest_commit_date', 'Python code', 'Perl code', 'Ruby code', 'Bourne Shell code', 'HTML code', 'Javascript code', 'CSS code', ]
    fields += [l+' files' for l in sorted(languages)]
    fields += [l+' code' for l in sorted(languages)]
    fields += [l+' comment' for l in sorted(languages)]
    fields += [l+' blank' for l in sorted(languages)]

    with open('stats.csv', 'w') as f:
        stats_file = csv.DictWriter(f, fields)
        stats_file.writeheader()
        for s in all_stats.values():
            stats_file.writerow(s)



#analyse_gits()
#json_to_csv()
