import math
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

from core.proj.reproj import lonLatToWebMerc, webMercToLonLat


def test_webmerc_roundtrip():
    lon, lat = 2.0, 40.0
    x, y = lonLatToWebMerc(lon, lat)
    lon2, lat2 = webMercToLonLat(x, y)
    assert math.isclose(lon, lon2, abs_tol=1e-6)
    assert math.isclose(lat, lat2, abs_tol=1e-6)
