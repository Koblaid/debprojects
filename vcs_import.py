import csv
import subprocess
import os
import json
import StringIO

import model as m



def import_csv(filepath):
    vcs_types = {}
    for vcs in m.VcsType.query.all():
        vcs_types[vcs.name] = vcs

    with open(filepath) as f:
        r = csv.DictReader(f)
        for row in r:
            project = m.Project()
            project.name = row['name']
            project.description = row['description'] or None
            project.documentation = row['documentation'] or None
            project.documentation_url = row['documentation_url'] or None
            project.status = row['status'] or None
            project.vcs_url = row['vcs_url'] or None
            if row['vcs_type']:
                project.vcs_type_id = vcs_types[row['vcs_type']].id

            maintainers = []
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


def clone_gits():
    r = csv.reader(open('/home/ben/projects/debcensus/debprojects.csv'))

    gits = {}
    for row in r:
        url = row[1]
        if url.startswith('git'):
            gits[row[0]] = row[1].split('\n')


    os.chdir('gits')
    for project_name, git in gits.iteritems():
        for g in git:
            g = g.replace('git://', 'http://')
            try:
                print subprocess.check_output(['git', 'clone', g])
            except Exception, e:
                print e

def analyse_gits():
    original_dir = os.getcwd()
    all_stats = {}

    for repo_dir in sorted(os.listdir('gits')):
        full_path = os.path.join('gits', repo_dir)
        if not os.path.isdir(full_path):
            continue

        stats = {}

        os.chdir(full_path)
        print os.getcwd()

        output = subprocess.check_output(["git rev-list --format=format:'%ai' --max-count=1 `git rev-parse HEAD`"], shell=True)
        stats['latest_commit_date'] = output.splitlines()[1]

        stats['number_of_authors'] = subprocess.check_output(["git shortlog -sn | wc -l"], shell=True).strip()

        stats['number_of_commits'] = subprocess.check_output(["git log --oneline | wc -l"], shell=True).strip()

        stats['number_of_files'] = subprocess.check_output(["git ls-files | wc -l"], shell=True).strip()

        output = subprocess.check_output(["du -s --exclude=.git/*"], shell=True)
        stats['size_of_files'] = output.split()[0]


        os.chdir(original_dir)

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
