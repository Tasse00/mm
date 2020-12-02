from setuptools import setup, find_packages

setup(
    name='mini-monitor',
    version="0.3.3",
    description='Mini Monitor, `Configurable` `Expandable` `Draggable` `TopWindow`',
    long_description=open('README.md', encoding='utf8').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(include="mm/*.py"),
    include_package_data=True,
    author='Carl.Zhang',
    author_email='tasse_00@163.com',
    maintainer='Carl.Zhang',
    maintainer_email='tasse_00@163.com',
    install_requires=open("requirements.txt").readlines(),
    entry_points='''
        [console_scripts]
        mm=mm:run
    ''',
    platforms=["all"],
    url='https://github.com/Tasse00/mm.git',
)
