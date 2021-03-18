import subprocess
from configparser import ConfigParser
from pathlib import Path

from flask import Flask
from flask_hookserver import Hooks

from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import InternalServerError

config = ConfigParser(interpolation=None)
config.read('config.ini')

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

app.config['GITHUB_WEBHOOKS_KEY'] = config['main']['github_secret']
app.config['VALIDATE_IP'] = True
app.config['VALIDATE_SIGNATURE'] = True

deploy_hook = Hooks(app, url=config['main']['endpoint'])

@deploy_hook.hook('push')
def deploy(data, guid):
    """Pulls the new site, triggered by a github webhook

    Args:
        data (dict): The webhook payload
        guid ([type]): No clue. read the flask_hookserver docs ;)

    Raises:
        InternalServerError: If it fails to pull

    Returns:
        string: A string to log that it deployed a website
    """

    repo = data['repository']['full_name']
    branch = data['ref'].split('/')[-1]
    main_branch = data['repository']['master_branch']

    if repo not in config:
        return 'Nothing to do for this repo, skipped.'

    if 'production_branch' in config[repo]:
        production_branch = config[repo][production_branch]
    else:
        production_branch = main_branch
    
    if branch != production_branch:
        return 'Not production branch, skipped.'

    try:
        subprocess.run(['/usr/bin/git',  'pull'], cwd=config[repo]['path'], text=True, check=True)
    except subprocess.CalledProcessError as err:
        raise InternalServerError(err)

    if 'command' in config[repo]:
        command = config[repo]['command']
        try:
            subprocess.run(command, cwd=config[repo]['path'], shell=True, text=True, check=True)
        except subprocess.CalledProcessError as err:
            raise InternalServerError(err)

    return 'Deployed website from {}'.format(repo)


def init():
    """Clone all sites specified in the config

    Raises:
        InternalServerError: on a failure to clone
    """
    for site in config:
        if site in ['DEFAULT', 'main']:
            continue
        
        deploy_path = Path(config[site]['path'])

        if not deploy_path.is_dir():
            raise FileNotFoundError('webroots have to be created and have appropriate permissions. {} is not a directory'.format(deploy_path))

        if not (deploy_path / '.git').is_dir():
            command = [ '/usr/bin/git',  'clone', config[site]['clone_uri'], '.' ]

            try:
                subprocess.run(command, cwd=deploy_path, check=True)
            except subprocess.CalledProcessError as err:
                raise InternalServerError(err)

init()

if __name__ == '__main__':
    app.run()
