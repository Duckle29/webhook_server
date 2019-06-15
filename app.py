from flask import Flask, request
from flask_hookserver import Hooks

from os import getenv
import subprocess
from hmac import digest, compare_digest
from binascii import hexlify

app = Flask(__name__)
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
        subprocess.run(['/usr/bin/git pull'], cwd='/srv/mikkel.cc', check=True)
    except subprocess.CalledProcessError as err:
        return err, 500

    return 'Deployed website'


if __name__ == '__main__':
    app.run()
