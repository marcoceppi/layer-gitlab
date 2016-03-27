import os
import yaml


class Gitlab(object):
    def __init__(self, env='production'):
        super(Gitlab, self).__init__()
        self.ENV = env
        self.install_path = '/home/git/gitlab'

    @property
    def config_path(self):
        return os.path.join(self.install_path, 'config')

    @property
    def installed(self):
        return os.path.exists(self.install_path)

    @property
    def version(self):
        if not self.installed:
            return None
        with open(os.path.join(self.install_path, 'VERSION')) as f:
            return f.read().strip()

    def configure_db(self, cfg):
        with open(os.path.join(self.config_path, 'database.yml'), 'w') as f:
            f.write(yaml.safe_dump({self.ENV: cfg}, default_flow_style=False))

    def configure_resque(self, address):
        cfg = {self.ENV: address}
        with open(os.path.join(self.config_path, 'resque.yml'), 'w') as f:
            f.write(yaml.safe_dump(cfg, default_flow_style=False))
