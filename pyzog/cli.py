# -*- coding: utf-8 -*-
#!/usr/bin/env python
###########################################
# 引用了 mjp 的项目需要初始化
# 这个模块定义了初始化需要的方法
###########################################

from pathlib import Path
import re
import configparser

from pkg_resources import resource_filename
import click

from pyzog.receiver import ZeroMQReceiver, RedisReceiver
from pyzog.tpl import create_from_jinja


TYPE_HELP = '指定服务器类型，可选值 redis/zmq'
ADDR_HELP = '服务器地址，形如 tcp://127.0.0.1:5011 或者 password@127.0.0.1:6379/0'
CHANNELS_HELP = '仅当 type 为 redis 的时候提供，允许指定多个 channel 名称'
SLEEP_TIME_HELP = '调用 redis.pubsub.get_message 时提供的 sleep_time 参数'

@click.group(help='执行 pyzog 命令')
def main():
    pass


def validate_addr(ctx, param, value):
    matchobj = re.match(r'^(?P<scheme>\w+:\/\/)?(?P<password>\w+)??@?(?P<host>[\w\d_\.\*]*):(?P<port>\d{4,5})/?(?P<db>\d+)?$', value)
    if matchobj is None:
        raise click.BadParameter('请提供正确的 addr 格式！')
    return matchobj


def check_addr(type_, addr):
    # click.echo(addr.groupdict())
    if type_ == 'zmq' and addr.group('scheme') is None:
        raise ValueError('zmq 类型必须提供 scheme！')
    if int(addr.group('port')) <= 1024:
        raise ValueError('请使用大于 1024 的端口号！')
    return addr


def get_conf(sconf):
    conf = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
    conf.read_string(sconf.read_text())
    return conf


@click.command(help='启动 pyzog。请先使用 pyzog genpyzog 生成配置文件。')
@click.option('-c', '--config_file', required=True, type=click.Path(file_okay=True, readable=True))
def start(config_file):
    try:
        conf = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
        conf.read_string(Path(config_file).read_text())

        type_ = conf['pyzog']['type']
        address = conf['pyzog']['addr']
        logpath = conf['pyzog']['logpath']
        channels = conf['pyzog']['channels'].split(',')

        logp = Path(logpath)
        if not logp.is_dir() or not logp.exists():
            raise ValueError('%s 不存在！' % logpath)

        addr = check_addr(type_, validate_addr(None, None, address))
        r = None
        if type_ == 'zmq':
            r = ZeroMQReceiver(logpath, addr.group('scheme') + addr.group('host'), addr.group('port'))
        elif type_ == 'redis':
            kwargs = {k:v for k, v in addr.groupdict().items() if k in ('host', 'port', 'password', 'db') and v is not None}
            if not channels:
                raise ValueError('必须提供 channels')
            kwargs['channels'] = channels
            kwargs['get_message_type'] = conf['pyzog']['get_message_type']
            kwargs['sleep_time'] = float(conf['pyzog']['sleep_time'])
            click.echo(kwargs)
            r = RedisReceiver(logpath, **kwargs)
        else:
            raise ValueError('不支持的 type: %s' % type_)

        click.echo(click.style('正在启动 pyzlog %s receiver...' % type_, fg='yellow'))
        err = r.start()
        raise ValueError(str(err))
    except Exception as e:
        click.echo(click.style('EXIT：%s' % e, fg='red'), err=True)
        raise click.Abort()


GEN_PYZOG_HELP = '在当前文件夹下生成 pyzog.conf 配置文件'


@click.command(help=GEN_PYZOG_HELP)
@click.option('-n', '--name', required=True, type=str, help='pyzog 实例的名称')
@click.option('-l', '--logpath', required=True, type=click.Path(), help='提供一个路径，pyzog 接收到的日志将放在这里')
@click.option('-t', '--type', required=True, type=click.Choice(['redis', 'zmq'], case_sensitive=False), help=TYPE_HELP)
@click.option('-a', '--addr', required=True, type=str, callback=validate_addr, help=ADDR_HELP)
@click.option('-m', '--get-message-type', required=False, type=click.Choice(['thread', 'block', 'listen'], case_sensitive=False), default='thread')
@click.option('-s', '--sleep-time', required=False, type=float, default=0.001, help=SLEEP_TIME_HELP)
@click.option('-c', '--channel', required=False, type=str, multiple=True, help=CHANNELS_HELP)
def genpyzog(**kwargs):
    try:
        replaceobj = {}
        for k in ('type', 'logpath'):
            replaceobj[k] = kwargs.get(k)
        replaceobj['addr'] = kwargs.get('addr').string

        if kwargs.get('type') == 'redis':
            if not kwargs.get('channel'):
                raise ValueError('必须提供 channel')
            if not kwargs.get('get_message_type'):
                raise ValueError('必须提供 get-message-type')
            click.echo(kwargs)
        for k in ('get_message_type', 'sleep_time', 'channel'):
            replaceobj[k] = kwargs.get(k)

        cwdpath = Path().cwd().joinpath(kwargs.get('name') + '.conf')
        create_from_jinja('pyzog', cwdpath, replaceobj)
    except Exception as e:
        click.echo(click.style('生成错误：%s' % e, fg='red'), err=True)
        raise click.Abort()


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
    except Exception as e:
        click.echo(click.style('生成错误：%s' % e, fg='red'), err=True)
        raise click.Abort()


GEN_PROGRAM_CONF_HELP = '生成 supervisord 的 program 配置文件'

@click.command(help=GEN_PROGRAM_CONF_HELP)
@click.option('-n', '--name', required=True, type=str, help='Supervisor program 名称')
@click.option('-c', '--config_file', required=True, type=click.Path(file_okay=True, readable=True))
@click.option('-u', '--user', required=False, type=str, help='Supervisor program 的 user')
def genprog(name, config_file, user):
    try:
        cwdpath = Path().cwd()
        replaceobj = {
            'cwd': cwdpath.resolve(),
            'name': name,
            'config_file': config_file,
        }
        if user is not None:
            replaceobj['user'] = user
        create_from_jinja('program', cwdpath.joinpath(name + '.conf'), replaceobj)
    except Exception as e:
        click.echo(click.style('生成错误 %s' % e, fg='red'), err=True)
        raise click.Abort()


main.add_command(start)
main.add_command(genpyzog)
main.add_command(gensupe)
main.add_command(gensys)
main.add_command(genprog)


if __name__ == '__main__':
    main()