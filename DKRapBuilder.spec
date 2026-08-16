from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

for package in ["faster_whisper", "ctranslate2", "g2p_en"]:
    try:
        d, b, h = collect_all(package)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

a = Analysis(["main.py"], pathex=["."], binaries=binaries, datas=datas, hiddenimports=hiddenimports, hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=["whisperx", "pyannote.audio", "torchvision", "pytorch_lightning"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, name="DKRapVocalBuilder", console=False)
coll = COLLECT(exe, a.binaries, a.datas, name="DKRapVocalBuilder")
