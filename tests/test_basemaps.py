import base64
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

PNG_DATA = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/axKqdAAAAAASUVORK5CYII="
)


def test_tile_retrieval(tmp_path, monkeypatch):
    from core.basemaps import mapservice, servicesDefs

    root = tmp_path / "tiles"
    tile_path = root / "0" / "0" / "0.png"
    tile_path.parent.mkdir(parents=True)
    tile_path.write_bytes(PNG_DATA)

    source = {
        "name": "Local",
        "description": "local tiles",
        "service": "TMS",
        "grid": "WGS84",
        "quadTree": False,
        "layers": {
            "BASIC": {"urlKey": "", "name": "basic", "description": "", "format": "png", "zmin": 0, "zmax": 0}
        },
        "urlTemplate": root.as_uri() + "/{Z}/{X}/{Y}.png",
        "referer": "",
    }

    monkeypatch.setitem(servicesDefs.SOURCES, "LOCAL", source)

    cache_folder = tmp_path / "cache"
    cache_folder.mkdir()
    ms = mapservice.MapService("LOCAL", cacheFolder=str(cache_folder))

    col, row, z, data = ms.getTile("BASIC", 0, 0, 0, toDstGrid=False)
    assert (col, row, z) == (0, 0, 0)
    assert data == PNG_DATA
