from flask import Flask
from flask_hookserver import Hooks

from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import InternalServerError

from os import getenv
import subprocess

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

app.config['GITHUB_WEBHOOKS_KEY'] = getenv('WEBHOOKS_GH_SECRET')
app.config['VALIDATE_IP'] = True
app.config['VALIDATE_SIGNATURE'] = True

hooks_deploy_mikkel_cc = Hooks(app, url='/deploy/mikkelcc')


@hooks_deploy_mikkel_cc.hook('push')
def website_deploy(data, guid):
    repo = data['repository']['full_name']
    branch = data['ref'].split('/')[-1]
    master_branch = data['repository']['master_branch']

    if repo != 'Duckle29/startbootstrap-resume':
        return 'Nothing to do for this repo, skipped.'
    if branch != master_branch:
        return 'Not production branch, skipped.'

    try:
        subprocess.run(['/usr/bin/git',  'pull'], cwd='/srv/mikkel.cc', check=True)
    except subprocess.CalledProcessError as err:
        raise InternalServerError(err)

    return 'Deployed website'


if __name__ == '__main__':
    app.run()
