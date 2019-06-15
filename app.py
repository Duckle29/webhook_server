from flask import Flask, request
from os import getenv
import subprocess
from hmac import digest, compare_digest
from binascii import hexlify

app = Flask(__name__)

SECRET = getenv('WEBHOOKS_GH_SECRET', 'NO_SECRET')\

if SECRET == 'NO_SECRET':
    print('The secret key hasn\'t been set!', flush=True)
    exit(1)

SECRET = SECRET.encode('utf-8')


def verify_signature():
    gh_signature = request.headers.get('X-Hub-Signature')
    hexdig = hexlify(digest(SECRET, request.get_data(), 'sha1'))
    signature = 'sha1=' + hexdig.decode('utf-8')

    return compare_digest(signature, gh_signature)


def website_deploy():
    subprocess.run(['/usr/bin/git pull'], cwd='/srv/mikkel.cc', check=True)


@app.route('/github', methods=['POST'])
def webhook():
    payload = request.json

    try:
        repo = payload['repository']['full_name']
        branch = payload['ref'].split('/')[-1]
        master_branch = payload['repository']['master_branch']
    except KeyError as err:
        return 'Unexpected payload: {}'.format(err), 500

    if repo != 'Duckle29/startbootstrap-resume':
        return 'Nothing to do for this repo', 200

    if branch != master_branch:
        return 'Not master, skipped', 200

    valid = verify_signature()

    if valid:
        try:
            website_deploy()
        except subprocess.CalledProcessError as err:
            return err, 500

        return 'Deployed website', 200

    if not valid:
        return '', 401

    return '', 500


if __name__ == '__main__':
    app.run()
