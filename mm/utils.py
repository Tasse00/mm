import importlib


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
