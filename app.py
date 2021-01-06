import subprocess
from configparser import ConfigParser
from argparse import ArgumentParser
from pathlib import Path

from flask import Flask
from flask_hookserver import Hooks

from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import InternalServerError

parser = ArgumentParser()

parser.add_argument('-c', '--config', default='config.ini', 
    help='The path to the config')
parser.add_argument('--gitpath', default='/usr/bin/git', 
    help='Path of the git executable')

args = parser.parse_args()

config = ConfigParser(interpolation=None)
config.read(args['config'])

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
    master_branch = data['repository']['master_branch']

    if repo not in config:
        return 'Nothing to do for this repo, skipped.'
    if branch != master_branch:
        return 'Not production branch, skipped.'

    try:
        subprocess.run([args['gitpath'],  'pull'], cwd=config[repo]['path'], check=True)
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
        
        deploy_path = Path(config[repo]['path'])

        if not deploy_path.is_dir():
            deploy_path.mkdir(parents=True)
            command = [ args['gitpath'],  'clone', config[site]['clone_uri'] ]

            try:
                subprocess.run(command, cwd=deploy_path, check=True)
            except subprocess.CalledProcessError as err:
                raise InternalServerError(err)

if __name__ == '__main__':
    init()
    app.run()
