"""Charge les runtimes C++ de la seule venv, sans modifier Windows ni son PATH."""
import ctypes
import os
import sys
from pathlib import Path

_handles = []


def prepare_torch_runtime():
    if os.name != 'nt' or _handles:
        return
    directory = Path(sys.prefix) / 'Scripts'
    if (directory / 'vcruntime140_1.dll').is_file():
        _handles.append(os.add_dll_directory(str(directory)))
        for name in ['vcruntime140.dll', 'vcruntime140_1.dll', 'msvcp140.dll']:
            candidate = directory / name
            if candidate.is_file():
                _handles.append(ctypes.WinDLL(str(candidate)))
