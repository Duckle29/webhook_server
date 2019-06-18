## Webhook server

This is a simple webhook server based on Flask and Flask-Hookserver. It eats github webhooks, and for now, deploys
my website if a push is made to the master branch.

It's meant to sit behind an nginx server, and as such has a proxyfix applied.
It expects a secret in the config.json
