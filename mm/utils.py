import importlib
import os
import sys
from glob import glob
from pathlib import Path
from typing import Optional, Iterator


def convert_bytes_unit(byte: int) -> str:
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    for unit in units:
        if byte < 1000:
            return f"{'%.2f' % byte}{unit}"
        byte /= 1024


def dynamic_load(identify: str):
    """
    动态加载目标 如加载 'pkg.module.Foo'
    """

    target = None
    processed = []
    rest = identify.split('.')
    module_end = False
    last_mod = None
    while rest:
        part = rest.pop(0)

        if not module_end:
            try:
                last_mod = importlib.import_module(".".join(processed + [part]))
            except ModuleNotFoundError:
                if last_mod is None:
                    # 尝试__main__寻找
                    last_mod = importlib.import_module("__main__")
                target = getattr(last_mod, part)
                module_end = True
        else:
            target = getattr(target, part)

        processed.append(part)

    return target or last_mod


def find_mods_in(path: str, parent: Optional[str] = None) -> Iterator:
    """发现指定文件路径下的所有mod"""
    py_files = glob(os.path.join(path, "*.py"))
    for py_file in py_files:
        filename = Path(py_file).name
        if filename.startswith("_"):
            continue
        mod_name = filename.split(".")[0]

        yield importlib.import_module(
            "."+mod_name if parent else mod_name,
            parent
        )

def relaunch():
    python = sys.executable
    os.execl(python, python, *sys.argv)
