import json
import sys
import types
from pathlib import Path
import pytest

# Stub bpy to satisfy addon initialization
bpy_stub = types.SimpleNamespace(
    app=types.SimpleNamespace(version=(2, 83, 0), background=True, tempdir="/tmp"),
    types=types.SimpleNamespace(Operator=object, Menu=object, AddonPreferences=object, Panel=object),
    utils=types.SimpleNamespace(register_class=lambda cls: None, unregister_class=lambda cls: None,
                                previews=types.SimpleNamespace(new=lambda: types.SimpleNamespace(icon_id=0))),
    ops=types.SimpleNamespace(),
    context=types.SimpleNamespace(window_manager=types.SimpleNamespace(), area=types.SimpleNamespace(),
                                  preferences=types.SimpleNamespace(addons={__package__: types.SimpleNamespace(preferences=None)})),
    data=types.SimpleNamespace(texts={}),
)
sys.modules.setdefault("bpy", bpy_stub)

pytest.importorskip("numpy")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import settings as settings_module


def test_preference_persistence(tmp_path, monkeypatch):
    with open(settings_module.cfgFile, 'r') as f:
        original = f.read()
    tmpfile = tmp_path / 'settings.json'
    tmpfile.write_text(original)

    monkeypatch.setattr(settings_module, 'cfgFile', str(tmpfile))

    settings = settings_module.settings
    original_engine = settings.proj_engine
    new_engine = 'BUILTIN' if original_engine != 'BUILTIN' else 'AUTO'
    settings.proj_engine = new_engine
    settings.save()

    data = json.loads(tmpfile.read_text())
    assert data['proj_engine'] == new_engine
