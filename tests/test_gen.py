from click.testing import CliRunner
from pathlib import Path
import configparser
import pytest


def get_conf(sconf):
    conf = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
    conf.read_string(sconf.read_text())
    return conf


@pytest.fixture
def gensupe_conf():
    sconf = Path(__file__).parent.parent.joinpath('supervisord.conf')
    print(' SETUP create: %s' % sconf)
    if sconf.exists():
        sconf.unlink()
    yield sconf
    print(' TEARDOWN unlink: %s' % sconf)
    sconf.unlink()


def test_gensupe(gensupe_conf):
    runner = CliRunner()
    from pyzog.cli import gensupe

    pathstr = '/srv/app/supervisor'
    user = 'app'

    result = runner.invoke(gensupe, ['--path', pathstr, '--supervisord-user', user])
    assert result.exit_code == 0
    conf = get_conf(gensupe_conf)
    assert conf['supervisord']['user'] == user
    assert conf['unix_http_server']['file'].startswith(pathstr)


@pytest.fixture
def gensys_conf():
    sconf = Path(__file__).parent.parent.joinpath('supervisord.service')
    print(' SETUP create: %s' % sconf)
    if sconf.exists():
        sconf.unlink()
    yield sconf
    print(' TEARDOWN unlink: %s' % sconf)
    sconf.unlink()


def test_gensys(gensys_conf):
    runner = CliRunner()
    from pyzog.cli import gensys

    supervisord_exec = '/srv/app/supervisor/venv/bin/supervisord'
    supervisorctl_exec = '/srv/app/supervisor/venv/bin/supervisorctl'
    supervisord_conf = '/srv/app/supervisor/supervisord.conf'

    result = runner.invoke(gensys, [
        '--supervisord-exec', supervisord_exec,
        '--supervisorctl-exec', supervisorctl_exec,
        '--supervisord-conf', supervisord_conf])

    assert result.exit_code == 0
    conf = get_conf(gensys_conf)
    assert conf['Service']['ExecStart'].startswith(supervisord_exec)
    assert conf['Service']['ExecReload'].startswith(supervisorctl_exec)


prog_name = 'test1'

@pytest.fixture
def genprog_conf():
    sconf = Path(__file__).parent.parent.joinpath(prog_name + '.conf')
    print(' SETUP create: %s' % sconf)
    if sconf.exists():
        sconf.unlink()
    yield sconf
    print(' TEARDOWN unlink: %s' % sconf)
    # sconf.unlink()


def test_genprog(genprog_conf):
    runner = CliRunner()
    from pyzog.cli import genprog

    prog_type = 'redis'
    prog_addr = '127.0.0.1:6379'
    prog_channel = 'req.*'
    prog_logpath = '/srv/logs/pyzog'
    prog_user = 'app'
    cwd = str(Path().cwd().resolve())

    result = runner.invoke(genprog, [
        '-n', prog_name,
        '-t', prog_type,
        '-a', prog_addr,
        '-c', prog_channel,
        '-u', prog_user,
        '-p', prog_logpath])

    assert result.exit_code == 0
    conf = get_conf(genprog_conf)
    conf_program = conf['program:' + prog_name]
    assert conf_program['user'].startswith(prog_user)
    assert conf_program['directory'].startswith(cwd)
    assert conf_program['stdout_logfile'].startswith(cwd)