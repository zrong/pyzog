# -*- coding: utf-8 -*-
#!/usr/bin/env python
###########################################
# 引用了 mjp 的项目需要初始化
# 这个模块定义了初始化需要的方法
###########################################

from pathlib import Path
import re

from pkg_resources import resource_filename
import click

from pyzog.receiver import ZeroMQReceiver, RedisReceiver
from pyzog.tpl import create_from_jinja


@click.group(help='执行 pyzog 命令')
def main():
    pass


START_HELP = """
启动 pyzog receiver。\n
    LOGPATH: log 文件存储路径"""
TYPE_HELP = '指定服务器类型'
ADDR_HELP = '形如 tcp://127.0.0.1:5011 或者 password@127.0.0.1:6379/0'
CHANNEL_HELP = '仅当 type 为 redis 的时候提供，允许指定多个 channel 名称'

def validate_addr(ctx, param, value):
    matchobj = re.match(r'^(?P<scheme>\w+:\/\/)?(?P<password>\w+)??@?(?P<host>[\w\d_\.\*]*):(?P<port>\d{4,5})/?(?P<db>\d+)?$', value)
    if matchobj is None:
        raise click.BadParameter('请提供正确的 addr 格式！')
    return matchobj


def check_addr(type_, addr):
    # click.echo(addr.groupdict())
    if type_ == 'zmq' and addr.group('scheme') is None:
        st = click.style('zmq 类型必须提供 scheme！', fg='red')
        click.echo(st, err=True)
        return False
    
    if int(addr.group('port')) <= 1024:
        st = click.style('请使用大于 1024 的端口号！', fg='red')
        click.echo(st, err=True)
        return False
    return True


@click.command(help=START_HELP)
@click.option('-t', '--type', 'type_', required=True, type=click.Choice(['redis', 'zmq'], case_sensitive=False), help=TYPE_HELP)
@click.option('-a', '--addr', required=True, type=str,  callback=validate_addr, help=ADDR_HELP)
@click.option('-c', '--channel', required=False, type=str, multiple=True, help=CHANNEL_HELP)
@click.argument('logpath', nargs=1, type=click.Path(dir_okay=True, exists=True))
def start(type_, addr, channel, logpath):
    # click.echo(addr.groupdict())
    succ = check_addr(type_, addr)
    if not succ:
        return

    r = None
    if type_ == 'zmq':
        r = ZeroMQReceiver(logpath, addr.group('scheme') + addr.group('host'), addr.group('port'))
    elif type_ == 'redis':
        kwargs = {k:v for k, v in addr.groupdict().items() if k in ('host', 'port', 'password', 'db') and v is not None}
        if not channel:
            click.echo(click.style('必须提供 channel', fg='red'), err=True)
            return
        kwargs['channel'] = channel
        click.echo(kwargs)
        r = RedisReceiver(logpath, **kwargs)
    else:
        click.echo(click.style('不支持的 type', fg='red'), err=True)
        return

    click.echo(click.style('正在启动 pyzlog %s receiver...' % type_, fg='yellow'))
    err = r.start()
    click.echo(click.style('EXIT: %s' % err, fg='red'), err=True)


GEN_SUPE_HELP = '在当前文件夹下生成 supervisord.conf 配置文件'

@click.command(help=GEN_SUPE_HELP)
@click.option('-p', '--path', required=False, type=click.Path(), help='提供一个路径，配置中和路径相关的内容都放在这个路径下')
@click.option('--unix-http-server-file', required=False, type=str)
@click.option('--supervisord-logfile', required=False, type=str)
@click.option('--supervisord-pidfile', required=False, type=str)
@click.option('--supervisord-user', required=False, type=str)
@click.option('--supervisord-directory', required=False, type=str)
@click.option('--supervisorctl-serverurl', required=False, type=str)
@click.option('--include-files', required=False, type=str)
def gensupe(**kwargs):
    try:
        replaceobj = {}
        path = kwargs.get('path')
        if path is not None:
            path = Path(path)
            replaceobj['unix_http_server_file'] = str(path.joinpath('run', 'supervisord.sock').resolve())
            replaceobj['supervisorctl_serverurl'] = 'unix://%s' % str(path.joinpath('run', 'supervisord.sock').resolve())
            replaceobj['include_files'] = str(path.joinpath('conf.d').resolve()) + '/*.conf'
            replaceobj['supervisord_logfile'] = str(path.joinpath('log', 'supervisord.log').resolve())
            replaceobj['supervisord_pidfile'] = str(path.joinpath('run', 'supervisord.pid').resolve())
            replaceobj['supervisord_directory'] = str(path.resolve())
            
        for k, v in kwargs.items():
            if v is not None:
                replaceobj[k] = v
        name = 'supervisord'
        cwdpath = Path().cwd()
        create_from_jinja(name, cwdpath, replaceobj)
    except Exception as e:
        click.echo(click.style('生成错误：%s' % e, fg='red'), err=True)
        raise click.Abort()


GEN_SYS_HELP = '在当前文件夹下生成 systemd 需要的 supervisord.service 配置文件'

@click.command(help=GEN_SYS_HELP)
@click.option('--supervisord-exec', required=False, type=str)
@click.option('--supervisorctl-exec', required=False, type=str)
@click.option('--supervisord-conf', required=False, type=str)
def gensys(**kwargs):
    try:
        replaceobj = {}
        for k, v in kwargs.items():
            if v is not None:
                replaceobj[k] = v
        name = 'systemd'
        cwdpath = Path().cwd()
        create_from_jinja(name, cwdpath, replaceobj)
    except Exception:
        click.echo(click.style('生成错误：%s' % e, fg='red'), err=True)
        raise click.Abort()


GEN_PROGRAM_CONF_HELP = '生成 supervisord 的 program 配置文件'

@click.command(help=GEN_PROGRAM_CONF_HELP)
@click.option('-n', '--name', required=True, type=str, help='输入 program 名称')
@click.option('-t', '--type', 'type_', required=True, type=click.Choice(['redis', 'zmq'], case_sensitive=False), help=TYPE_HELP)
@click.option('-a', '--addr', required=True, type=str,  callback=validate_addr, help=ADDR_HELP)
@click.option('-c', '--channel', required=False, type=str, multiple=True, help=CHANNEL_HELP)
@click.option('-u', '--user', required=False, type=str, help='执行 program 的 user')
@click.option('-p', '--logpath', required=False, type=str, help='log 文件的路径。若不提供则使用当前文件夹下的 logs 文件夹')
def genprog(name, type_, addr, channel, user, logpath):
    succ = check_addr(type_, addr)
    if not succ:
        return

    if type_ == 'redis':
        if not channel:
            click.echo(click.style('必须提供 channel', fg='red'), err=True)
            return
    try:
        cwdpath = Path().cwd()
        replaceobj = {
            'cwd': cwdpath.resolve(),
            'name': name,
            'addr': addr.string,
            'type': type_,
            'logpath': logpath or cwdpath.joinpath('logs').resolve(),
        }
        if channel is not None:
            replaceobj['channels'] = channel
        if user is not None:
            replaceobj['user'] = user
        create_from_jinja('program', cwdpath.joinpath(name + '.conf'), replaceobj)
    except Exception as e:
        click.echo(click.style('生成错误 %s' % e, fg='red'), err=True)
        raise click.Abort()


main.add_command(start)
main.add_command(gensupe)
main.add_command(gensys)
main.add_command(genprog)


if __name__ == '__main__':
    main()