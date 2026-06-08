# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import copy_metadata, collect_data_files, collect_submodules

datas = [
    ('app.py', '.'),
    ('modules', 'modules'),
    ('models', 'models'),
    ('utils', 'utils'),
]
datas += collect_data_files('streamlit')

hiddenimports = collect_submodules('streamlit')
hiddenimports += collect_submodules('altair')
hiddenimports += [
    'pandas',
    'plotly',
    'plotly.express',
    'plotly.graph_objects',
    'openpyxl',
    'dataclasses',
    'models.datamodels',
    'utils.helpers',
    'modules.input_module',
    'modules.calculator',
    'modules.display_module',
    'modules.io_module',
]
datas += copy_metadata('streamlit')
datas += copy_metadata('pandas')
datas += copy_metadata('plotly')
datas += copy_metadata('openpyxl')
datas += copy_metadata('altair')
datas += copy_metadata('numpy')
datas += copy_metadata('pyarrow')
datas += copy_metadata('jinja2')
datas += copy_metadata('pillow')
datas += copy_metadata('gitpython')
datas += copy_metadata('pydeck')
datas += copy_metadata('tenacity')
datas += copy_metadata('toml')
datas += copy_metadata('watchdog')
datas += copy_metadata('protobuf')

import os as _os, sys as _sys
_conda_bin = _os.path.join(_sys.prefix, 'Library', 'bin')
binaries = [
    (f'{_conda_bin}\\libcrypto-3-x64.dll', '.'),
    (f'{_conda_bin}\\libssl-3-x64.dll', '.'),
    (f'{_conda_bin}\\sqlite3.dll', '.'),
    (f'{_conda_bin}\\ffi.dll', '.'),
    (f'{_conda_bin}\\libexpat.dll', '.'),
    (f'{_conda_bin}\\liblzma.dll', '.'),
]

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='财务自由评估',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)


