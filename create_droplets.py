"""use DO API to create master and n nodes"""

# stdlib
from os import environ
from time import sleep
import logging
import sys

# 3rd party
import digitalocean

# local

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

token_env_var = 'DO_API_TOKEN'
token = environ.get(token_env_var)

if not token:
    print(f'{token_env_var} env var not set!')
    exit(1)

manager = digitalocean.Manager(token=token)
keys = manager.get_all_sshkeys()
key = [k for k in keys if k.name == 'sol']

ansible_data = {}

def create_droplet(name, region='nyc1'):
    ansible_data[name] = f'{name} ansible_host='
    logging.info(f'creating: {name}')
    droplet = digitalocean.Droplet(token=token,
                                   name=name,
                                   region=region,
                                   image=21669205,
                                   ssh_keys=key,
                                   size_slug='s-4vcpu-8gb',
                                   backups=False)
    droplet.create()
    actions = droplet.get_actions()
    is_done = False
    while not is_done:
        for action in actions:
            action.load()
            if action.status != 'in-progress':
                is_done = True
        sleep(5)
    logging.info(f'done creating: {name}')


create_droplet('master')
for i in range(2):
    name = f'do-node{i+1}'
    create_droplet(name)

for droplet in manager.get_all_droplets():
    if not ansible_data.get(droplet.name):
        continue
    ansible_data[droplet.name] += droplet.ip_address

config_file = f"""\
[masters]
{[v for k,v in ansible_data.items() if k == 'master'][0]}

[workers]
"""

for line in [v for k,v in ansible_data.items() if k != 'master']:
    config_file += f'{line}\n'


hosts_file_path = './k8s_ansible/hosts'

print(f'writing {hosts_file_path}')

with open(hosts_file_path, 'w') as fd:
    fd.write(config_file)

print('all done!')