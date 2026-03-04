# central place to register all commands in current libfunc dir
from .connecter import register as _reg_connecter
from .memcpy import register as _reg_memcpy

def register():
    _reg_connecter()
    _reg_memcpy()