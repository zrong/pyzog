from pathlib import Path
import re
from setuptools import setup, find_packages

here = Path(__file__).parent

def read(*parts):
    """ 读取一个文件并返回内容
    """
    return here.joinpath(*parts).read_text(encoding='utf8')

def find_version(*file_paths):
    """ 从 __init__.py 的 __version__ 变量中提取版本号
    """
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

def find_requires(*file_paths):
    """ 将提供的 requirements.txt 按行转换成 list
    """
    require_file = read(*file_paths)
    return require_file.splitlines()

classifiers = [
    'Programming Language :: Python :: 3.6',
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Operating System :: OS Independent',
    'Topic :: Internet :: WWW/TCP :: Logging',
    'Topic :: Utilities',
    'License :: OSI Approved :: MIT License',
]

entry_points = {
    'console_scripts': [
        'pyzog=cli:main',
    ]
}

setup(
    name = "pyzog",
    version=find_version('pyzog', '__init__.py'),
    description = "A Python and ZeroMQ powered logging receiver.",
    author = "zrong",
    author_email = "zrongzrong@gmail.com",
    url = "https://zengrong.net",
    license = "MIT",
    keywords = "development zrong zmq logging",
    python_requires='>=3.6, <4',
    packages = find_packages(exclude=['test*', 'doc*', 'fabric']),
    install_requires=find_requires('requirements.txt'),
    entry_points=entry_points,
    include_package_data = True,
    zip_safe=False,
    classifiers = classifiers
)
