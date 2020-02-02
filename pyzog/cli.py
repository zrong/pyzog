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
from pyzog.tpl import create_from_jinja, tpl_files


basedir = Path(resource_filename('pyzog', '__init__.py')).parents[1]
# 找到 logs 文件夹所在地
logsdir = basedir.joinpath('logs')

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


ECHO_CONF_HELP = '输出 supervisord 和 systemd 配置文件内容'

@click.command(help=ECHO_CONF_HELP)
@click.option('-t', '--type', 'type_', required=True, type=click.Choice(['supervisord', 'systemd'], case_sensitive=False), help='生成 supervisord 或者 systemd 配置文件。使用 systemd 来驱动 supervisord。')
def echoconf(type_):
    try:
        conf_content = create_from_jinja(type_)
        click.echo(conf_content)
    except Exception:
        click.echo(click.style('不支持的 type', fg='red'), err=True)


GEN_PROGRAM_CONF_HELP = '生成 supervisord 的 program 配置文件'

@click.command(help=GEN_PROGRAM_CONF_HELP)
@click.option('-n', '--name', required=True, type=str, help='输入 program 名称')
@click.option('-t', '--type', 'type_', required=True, type=click.Choice(['redis', 'zmq'], case_sensitive=False), help=TYPE_HELP)
@click.option('-a', '--addr', required=True, type=str,  callback=validate_addr, help=ADDR_HELP)
@click.option('-c', '--channel', required=False, type=str, multiple=True, help=CHANNEL_HELP)
def genprog(name, type_, addr, channel):
    succ = check_addr(type_, addr)
    if not succ:
        return

    try:
        cwdpath = Path().cwd()
        replaceobj = {
            'name': name,
            'cwd': cwdpath.resolve(),
            'channels': channel,
            'type': type_,
            'addr': addr.string,
        }
        create_from_jinja('program', cwdpath.joinpath(name + '.conf'), replaceobj)
    except Exception:
        click.echo(click.style('不支持的 type %s' % type_, fg='red'), err=True)


main.add_command(start)
main.add_command(echoconf)
main.add_command(genprog)


if __name__ == '__main__':
    main()