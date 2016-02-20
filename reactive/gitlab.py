import re
import sys
import shutil
import fileinput

from charmhelpers.fetch import apt_install, apt_update
from charmhelpers.core.hookenv import status_set, config

from charms.reactive import when, when_not, set_state, remove_state, hook
from charms.reactive.helpers import data_changed

from subprocess import check_call, CalledProcessError, call


@when_not('gitlab.installed')
def install():
    status_set('maintenance', 'Installing GitLab')
    apt_install(["curl", "openssh-server", "ca-certificates", "postfix"])

    check_call(['apt-key', 'add', './data/gitlab_gpg.key'])

    shutil.copy2('data/gitlab_gitlab-ce.list', '/etc/apt/sources.list.d/gitlab-ce.list')
    apt_update()

    version = ''
    if config('gitlab_version'):
        version = '=' + config('gitlab_version')

    apt_install(['gitlab-ce' + version])

    check_call(['gitlab-ctl', 'reconfigure'])
    set_state('gitlab.installed')
    status_set('active', 'GitLab is ready!')


@when('gitlab.installed')
def check_running():
    if data_changed('gitlabconfig', config()):
        status_set('maintenance', 'Updating Config')
        updateConfig(config())

    if config('http_port'):
        open_port(config('http_port'))
    else:
        open_port(80)

    status_set('active', 'GitLab is ready!')


def updateConfig(config):
    filepath = '/etc/gitlab/gitlab.rb'

    exturl = None

    if config('external_url'):
        exturl = config('external_url')
        if not exturl.startswith("http"):
            exturl = "http://" + exturl

    if config('external_url') and config('http_port'):
        if exturl.endswith("/"):
            exturl = exturl[:-1]

        exturl = exturl + ":" + config('http_port')

    modConfigNoEquals(filepath, 'external_url', exturl)
    modConfig(filepath, 'gitlab_rails[\'gitlab_ssh_host\']', config('ssh_host'))
    modConfig(filepath, 'gitlab_rails[\'time_zone\']', config('time_zone'))
    modConfig(filepath, 'gitlab_rails[\'gitlab_email_from\']', config('email_from'))
    modConfig(filepath, 'gitlab_rails[\'gitlab_email_display_name\']', config('from_email_name'))
    modConfig(filepath, 'gitlab_rails[\'gitlab_email_reply_to\']', config('reply_to_email'))
    modConfig(filepath, 'gitlab_rails[\'smtp_enable\']', config('smtp_enable'))
    modConfig(filepath, 'gitlab_rails[\'smtp_address\']', config('smtp_address'))
    modConfig(filepath, 'gitlab_rails[\'smtp_port\']', config('smtp_port'))
    modConfig(filepath, 'gitlab_rails[\'smtp_user_name\']', config('smtp_user_name'))
    modConfig(filepath, 'gitlab_rails[\'smtp_password\']', config('smtp_password'))
    modConfig(filepath, 'gitlab_rails[\'smtp_domain\']', config('smtp_domain'))
    modConfig(filepath, 'gitlab_rails[\'smtp_enable_starttls_auto\']', config('smtp_enable_starttls_auto'))
    modConfig(filepath, 'gitlab_rails[\'smtp_tls\']', config('smtp_tls'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_enabled\']', config('incoming_email_enabled'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_address\']', config('incoming_email_address'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_email\']', config('incoming_email_email'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_password\']', config('incoming_email_password'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_host\']', config('incoming_email_host'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_port\']', config('incoming_email_port'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_ssl\']', config('incoming_email_ssl'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_start_tls\']', config('incoming_email_start_tls'))
    modConfig(filepath, 'gitlab_rails[\'incoming_email_mailbox_name\']', config('incoming_email_mailbox_name'))
    modConfig(filepath, 'gitlab_rails[\'backup_path\']', config('backup_path'))
    modConfig(filepath, 'gitlab_rails[\'backup_keep_time\']', config('backup_keep_time'))
    modConfig(filepath, 'gitlab_rails[\'backup_upload_remote_directory\']',
              config('backup_upload_remote_directory'))
    modConfig(filepath, 'gitlab_rails[\'backup_upload_connection\']', config('backup_upload_connection'))

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
            if not VarFound and _infile_var.rstrip(' ') == V:
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
            if not Setting and not l.lstrip(' ').startswith('#'):
                l = '#' + l
                f.write(l)
            elif Setting and l.lstrip(' ').startswith('#'):
                l = re.sub("#", "", l)
                f.write(l)
            elif Setting is not '' or Setting is not None:
                f.write(l)

    elif AlreadySet:
        print("Variable '%s' unchanged" % (V))
    else:
        print("Variable '%s' modified to '%s'" % (V, S))

    fileinput.close()
    return
