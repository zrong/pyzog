# -*- coding: utf-8 -*-
#!/usr/bin/env python
###########################################
# 引用了 mjp 的项目需要初始化
# 这个模块定义了初始化需要的方法
###########################################

from pathlib import Path
from pkg_resources import resource_filename

import pyzog
from pyzog.receiver import ZeroMQReceiver, RedisReceiver

import click


basedir = Path(resource_filename('pyzog', '__init__.py')).parents[1]
# 找到 logs 文件夹所在地
logsdir = basedir.joinpath('logs')


@click.group(help='执行 pyzog 命令')
def main():
    pass


START_HELP = """
启动 pyzog receiver。\n
    TYPE: redis/zmq 代表不同的服务器\n
    ADDR: tcp://127.0.0.1:3456 或者 password@127.0.0.1:3456/0\n
    LOGPATH: log 文件存储路径"""

@click.command(help=START_HELP)
@click.argument('type', nargs=1, type=str)
@click.argument('addr', nargs=1, type=str)
@click.argument('logpath', nargs=1, type=click.Path(dir_okay=True, exists=True))
def start(type, addr, logpath):
    if addr <= 1024:
        st = click.style('请使用大于 1024 的端口号！', fg='red')
        click.echo(st, err=True)
        return

    r = None
    if type == 'zmq':
        r = ZeroMQReceiver(addr, logpath)
    elif type == 'redis':
        r = RedisReceiver(addr, logpath)
    else:
        click.echo(click.style('不支持的 type', fg='red'), err=True)
        return

    click.echo(click.style('正在启动 pyzlog %s receiver...' % type, fg='yellow'))
    r.start()

main.add_command(start)


if __name__ == '__main__':
    main()