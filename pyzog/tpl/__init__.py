# -*- coding: utf-8 -*-
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

basedir = Path(__file__).parent

# 所有的模版文件名
tpl_files = {
    'supervisord': 'supervisord.jinja2',
    'systemd': 'supervisord.service.jinja2',
    'program': 'supervisor_program.jinja2',
}


def create_from_jinja(tplname, tpltarget=None, replaceobj={}):
    """ 调用 jinja2 渲染
    :param tplname: 模版文件的名称
    :param tpltarget: 如果不提供则返回渲染后的文本，若提供则必须是一个 Path 对象
    """
    tplfile = tpl_files.get(tplname)
    if tplfile is None:
        raise ValueError('没有找到名为 %s 的模版文件！' % tplname)
    tplenv = Environment(loader=FileSystemLoader(basedir.resolve()))
    tpl = tplenv.get_template(tplfile)
    text = tpl.render(replaceobj)
    if isinstance(tpltarget, Path):
        tpltarget.write_text(text)
    return text

