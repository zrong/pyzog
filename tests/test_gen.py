from click.testing import CliRunner
from pathlib import Path
import configparser
import pytest

@pytest.fixture()
def gensupe_conf():
    sconf = Path(__file__).parent.parent.joinpath('supervisord.conf')
    if sconf.exists():
        sconf.unlink()
    yield sconf


@pytest.fixture()
def gensys_conf():
    sconf = Path(__file__).parent.parent.joinpath('supervisord.service')
    if sconf.exists():
        sconf.unlink()
    yield sconf


def test_gensupe(gensupe_conf):
    runner = CliRunner()
    from pyzog.cli import gensupe

    pathstr = '/srv/app/supervisor'
    user = 'app'

    result = runner.invoke(gensupe, ['--path', pathstr, '--supervisord-user', user])
    assert result.exit_code == 0
    conf = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
    conf.read_string(gensupe_conf.read_text())
    assert conf['supervisord']['user'] == user
    assert conf['unix_http_server']['file'].startswith(pathstr)
    gensupe_conf.unlink()


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
    conf = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
    conf.read_string(gensys_conf.read_text())
    assert conf['Service']['ExecStart'].startswith(supervisord_exec)
    assert conf['Service']['ExecReload'].startswith(supervisorctl_exec)
    gensys_conf.unlink()