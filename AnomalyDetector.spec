# AnomalyDetector.spec
# Run using: pyinstaller AnomalyDetector.spec

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('comment_rules.yaml', '.'),
        ('models', 'models'),
        ('inference', 'inference'),
        ('utils', 'utils'),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[]
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='AnomalyDetector',
    debug=False,
    strip=False,
    upx=False,
    console=False
)
