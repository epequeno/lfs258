"""use DO API to destroy master and worker nodes"""

# stdlib
from os import environ
import logging

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

for droplet in manager.get_all_droplets():
    if droplet.name == 'master' or droplet.name.startswith('worker'):
      logging.info(f'destroying {droplet.name}')
      droplet.destroy()

logging.info('all done!')