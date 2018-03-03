"""use DO API to create master and n nodes"""

# stdlib
from os import environ
from time import sleep
import logging
import sys
import threading

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
    ansible_data[name] = f'{name} ansible_host='


if __name__ == '__main__':
  # set names
  num_workers = 2
  names = ['master']
  names.extend([f'worker-{n}' for n in range(num_workers)])

  for name in names:
    t = threading.Thread(target=create_droplet, args=[name])
    t.start()

  while len(ansible_data) != len(names):
    sleep(3)

  for droplet in manager.get_all_droplets():
      if not ansible_data.get(droplet.name):
          continue
      ansible_data[droplet.name] += droplet.ip_address

  config_file = f"""\
[masters]
{ansible_data['master']}

[workers]
"""

  for line in [v for k,v in ansible_data.items() if k != 'master']:
      config_file += f'{line}\n'


  hosts_file_path = './k8s_ansible/hosts'

  logging.info(f'writing {hosts_file_path}')

  with open(hosts_file_path, 'w') as fd:
      fd.write(config_file)

  logging.info('all done!')