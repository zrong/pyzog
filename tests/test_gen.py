from click.testing import CliRunner
from pathlib import Path
import configparser
import pytest


def get_conf(sconf):
    conf = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
    conf.read_string(sconf.read_text())
    return conf


@pytest.fixture
def genpyzog_conf():
    sconf = Path(__file__).parent.parent.joinpath('pyzogtest.conf')
    print(' GENPYZOG SETUP create: %s' % sconf)
    if sconf.exists():
        sconf.unlink()
    yield sconf
    print(' GENPYZOG TEARDOWN unlink: %s' % sconf)
    sconf.unlink()


def test_genpyzog(genpyzog_conf):
    runner = CliRunner()
    from pyzog.cli import genpyzog

    pyzog_name = 'pyzogtest'
    pyzog_type = 'redis'
    pyzog_addr = '127.0.0.1:6379'
    pyzog_logpath = '/srv/logs/pyzog'
    pyzog_sleep_time = 0.0005

    result = runner.invoke(genpyzog, [
        '--name', pyzog_name,
        '--logpath', pyzog_logpath,
        '--type', pyzog_type,
        '--addr', pyzog_addr,
        '-s', pyzog_sleep_time,
        '-m', 'thread',
        '-c', 'req.*',
        '-c', 'app.*',
        ])
    assert result.exit_code == 0
    conf = get_conf(genpyzog_conf)
    assert conf['pyzog']['type'] == pyzog_type
    assert conf['pyzog']['addr'] == pyzog_addr
    assert conf['pyzog']['sleep_time'] == str(pyzog_sleep_time)


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
    print(' GENPROG SETUP create: %s' % sconf)
    if sconf.exists():
        sconf.unlink()
    yield sconf
    print(' GENPROG TEARDOWN unlink: %s' % sconf)
    sconf.unlink()


def test_genprog(genprog_conf):
    runner = CliRunner()
    from pyzog.cli import genprog

    prog_user = 'app'
    prog_config_file = 'pyzogtest.conf'
    cwd = str(Path().cwd().resolve())

    result = runner.invoke(genprog, [
        '-n', prog_name,
        '-c', prog_config_file,
        '-u', prog_user,
    ])

    assert result.exit_code == 0
    conf = get_conf(genprog_conf)
    conf_program = conf['program:' + prog_name]
    assert conf_program['user'].startswith(prog_user)
    assert conf_program['directory'].startswith(cwd)
    assert conf_program['stdout_logfile'].startswith(cwd)