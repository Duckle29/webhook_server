from flask import Flask
from flask_hookserver import Hooks

from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import InternalServerError

import subprocess
from configparser import ConfigParser

config = ConfigParser()
config.read("config.ini")

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

app.config['GITHUB_WEBHOOKS_KEY'] = config['main']['github_secret']
app.config['VALIDATE_IP'] = True
app.config['VALIDATE_SIGNATURE'] = True


for site in config:
    if site in ['DEFAULT', 'main']: 
        continue
    
    print(site)

deploy_hook = Hooks(app, url=config['main']['endpoint'])

@deploy_hook.hook('push')
def deploy(data, guid):
    repo = data['repository']['full_name']
    branch = data['ref'].split('/')[-1]
    master_branch = data['repository']['master_branch']

    if repo not in config:
        return 'Nothing to do for this repo, skipped.'
    if branch != master_branch:
        return 'Not production branch, skipped.'

    try:
        subprocess.run(['/usr/bin/git',  'pull'], cwd=config[repo]['path'], check=True)
    except subprocess.CalledProcessError as err:
        raise InternalServerError(err)

    return 'Deployed website'


if __name__ == '__main__':
    app.run()
