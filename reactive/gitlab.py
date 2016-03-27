
from charms.reactive import (
    when,
    when_not,
    set_state,
    remove_state,
)

from charmhelpers.core.hookenv import (
    status_set,
    config,
    open_port,
    log,
    resource_get,
)

from charms.layer import Gitlab


gitlab = Gitlab('production')


@when_not('gitlab.installed')
def install():
    pass


@when('gitlab.installed')
@when('database.database.available')
@when_not('gitlab.psql.configured')
def configure_psql(pgsql):
    db_cfg = {
        'adapter': 'postgresql',
        'encoding': 'unicode',
        'database': pgsql.database(),
        'pool': 10
        'username': pgsql.user(),
        'password': pgsql.password(),
        'host': pgsql.host(),
        'port': pgsql.port(),
    }

    gitlab.configure_db(
        database=pgsql.database(),
        username=pgsql.user(),
        password=pgsql.password(),
        host=pgsql.host(),
        port=pgsql.port(),
    )

    set_state('gitlab.psql.configured')


@when('gitlab.installed')
@when('kv.available')
@when_not('gitlab.redis.configured')
def configure_redis(redis)
    gitlab.configure_resque(redis.connection_string())

    set_state('gitlab.redis.configured')











import re
import sys
import shutil
import fileinput

from charms.reactive import (
    when,
    when_not,
    set_state,
    remove_state,
    hook,
)

from subprocess import check_call, CalledProcessError, call

from charmhelpers.core.hookenv import (
    status_set,
    config,
    open_port,
    log,
)

from charms.reactive.helpers import data_changed
from charms.layer import Gitlab



filepath = '/etc/gitlab/gitlab.rb'


@when('website.available')
@when('gitlab.internal_webserver')
def configure_website(website):
    log("starting hook")
    modConfig(filepath, 'gitlab_workhorse[\'listen_network\']', 'tcp')
    modConfig(filepath, 'gitlab_workhorse[\'listen_addr\']', '0.0.0.0')
    modConfig(filepath, 'nginx[\'enable\']', 'false')
    modConfig(filepath, 'web_server[\'external_users\']', 'www-data')
    check_call(['gitlab-ctl', 'reconfigure'])
    check_call(['gitlab-ctl', 'restart'])
    website.configure(port=8181)
    set_state('gitlab.external_webserver')

@when_not('website.available')
@when('gitlab.external_webserver')
def unconfigure_website(website):
    modConfig(filepath, 'gitlab_workhorse[\'listen_network\']', None)
    modConfig(filepath, 'gitlab_workhorse[\'listen_addr\']', None)
    modConfig(filepath, 'nginx[\'enable\']', 'true')
    modConfig(filepath, 'web_server[\'external_users\']', None)
    set_state('gitlab.internal_webserver')


@when_not('gitlab.installed')
def install():
    status_set('maintenance', 'installing GitLab')

    set_state('gitlab.installed')
    status_set('active', 'GitLab is ready!')


@when('gitlab.installed')
def check_running():
    if data_changed('gitlab.config', config()):
        status_set('maintenance', 'Updating Config')
        updateConfig(config())

    if config('http_port'):
        open_port(config('http_port'))
    else:
        open_port(80)

    status_set('active', 'GitLab is ready!')


def updateConfig(config):
    exturl = None

    if config.get('external_url'):
        exturl = config.get('external_url')
        if not exturl.startswith("http"):
            exturl = "http://" + exturl

    if config.get('external_url') and config.get('http_port'):
        if exturl.endswith("/"):
            exturl = exturl[:-1]

        exturl = exturl + ":" + config.get('http_port')

    modConfigNoEquals(filepath, 'external_url', exturl)
    modConfig(filepath, 'gitlab_rails[\'gitlab_ssh_host\']', config.get('ssh_host'))
    modConfig(filepath, 'gitlab_rails[\'time_zone\']', config.get('time_zone'))
    modConfig(filepath, 'gitlab_rails[\'gitlab_email_from\']', config.get('email_from'))
    modConfig(filepath, 'gitlab_rails[\'gitlab_email_display_name\']', config.get('from_email_name'))
    modConfig(filepath, 'gitlab_rails[\'gitlab_email_reply_to\']', config.get('reply_to_email'))
    modConfig(filepath, 'gitlab_rails[\'smtp_enable\']', config.get('smtp_enable'))
    modConfig(filepath, 'gitlab_rails[\'smtp_address\']', config.get('smtp_address'))
    modConfig(filepath, 'gitlab_rails[\'smtp_port\']', config.get('smtp_port'))
    modConfig(filepath, 'gitlab_rails[\'smtp_user_name\']', config.get('smtp_user_name'))
    modConfig(filepath, 'gitlab_rails[\'smtp_password\']', config.get('smtp_password'))
    modConfig(filepath, 'gitlab_rails[\'smtp_domain\']', config.get('smtp_domain'))
    modConfig(filepath, 'gitlab_rails[\'smtp_enable_starttls_auto\']', config.get('smtp_enable_starttls_auto'))
    modConfig(filepath, 'gitlab_rails[\'smtp_tls\']', config.get('smtp_tls'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_enabled\']', config.get('incoming_email_enabled'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_address\']', config.get('incoming_email_address'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_email\']', config.get('incoming_email_email'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_password\']', config.get('incoming_email_password'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_host\']', config.get('incoming_email_host'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_port\']', config.get('incoming_email_port'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_ssl\']', config.get('incoming_email_ssl'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_start_tls\']', config.get('incoming_email_start_tls'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_mailbox_name\']', config.get('incoming_email_mailbox_name'))
    modConfig(filepath, 'gitlab_rails[\'backup_path\']', config.get('backup_path'))
    modConfig(filepath, 'gitlab_rails[\'backup_keep_time\']', config.get('backup_keep_time'))
    modConfig(filepath, 'gitlab_rails[\'backup_upload_remote_directory\']',
              config.get('backup_upload_remote_directory'))
    modConfig(filepath, 'gitlab_rails[\'backup_upload_connection\']', config.get('backup_upload_connection'))

    check_call(["gitlab-ctl", "reconfigure"])

    status_set('active', 'GitLab is ready!')


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def modConfigNoEquals(File, Variable, Setting):
    for line in fileinput.input(File, inplace=1):
        if line.startswith(Variable):
            line = Variable + ' \'' + Setting + '\''
        sys.stdout.write(line)
    fileinput.close()


def modConfig(File, Variable, Setting):
    """
    Modify Config file variable with new setting
    """
    VarFound = False
    AlreadySet = False
    V = str(Variable)
    S = str(Setting)
    if isinstance(Setting, bool):
        if (Setting):
            S = "true"
        else:
            S = "false"
    elif (S.isdigit()):
        S = int(S)
    elif (isfloat(S)):
        S = float(S)
    else:
        S = '\'' + S + '\''

    for line in fileinput.input(File, inplace=1):
        # process lines that look like config settings #
        if '=' in line:
            _infile_var = str(line.split('=')[0].rstrip(' '))
            _infile_set = str(line.split('=')[1].lstrip(' ').rstrip())
            # only change the first matching occurrence #
            if VarFound == False and _infile_var.rstrip(' ') == V:
                VarFound = True
                # don't change it if it is already set #
                if _infile_set.lstrip(' ') == S:
                    AlreadySet = True
                else:
                    line = "%s = %s\n" % (V, S)

        sys.stdout.write(line)

    # Append the variable if it wasn't found #
    if not VarFound:
        print("Variable '%s' not found.  Adding it to %s" % (V, File))
        with open(File, "a") as f:
            l = "%s = %s\n" % (V, S)
            if (Setting is '' or Setting is None) and not l.lstrip(' ').startswith('#'):
                l = '#' + l
                f.write(l)
            elif (Setting is not '' or Setting is not None) and l.lstrip(' ').startswith('#'):
                l = re.sub("#", "", l)
                f.write(l)
            elif (Setting is not '' or Setting is not None):
                f.write(l)

    elif AlreadySet == True:
        print("Variable '%s' unchanged" % (V))
    else:
        print("Variable '%s' modified to '%s'" % (V, S))

    fileinput.close()
    return
