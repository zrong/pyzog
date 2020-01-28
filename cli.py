# -*- coding: utf-8 -*-
#!/usr/bin/env python
###########################################
# 引用了 mjp 的项目需要初始化
# 这个模块定义了初始化需要的方法
###########################################

from pathlib import Path
from pkg_resources import resource_filename

import pyzog
from pyzog.receiver import Receiver

import click


basedir = Path(resource_filename('pyzog', '__init__.py')).parents[1]
# 找到 logs 文件夹所在地
logsdir = basedir.joinpath('logs')


@click.group(help='执行 pyzog 命令')
def main():
    pass


@click.command(help='启动 pyzog receiver')
@click.argument('port', nargs=1, type=int)
@click.argument('logpath', nargs=1, type=click.Path(dir_okay=True, exists=True))
def start(port, logpath):
    if port <= 1024:
        st = click.style('请使用大于 1024 的端口号！', fg='red')
        click.echo(st, err=True)
        return

    r = Receiver(port, logpath)
    click.echo(click.style('正在启动 pyzlog receiver...', fg='yellow'))
    r.start()

main.add_command(start)


if __name__ == '__main__':
    main()