import logging
import subprocess
import sys
import importlib

log = logging.getLogger(__name__)


def ensure_dependency(module_name, package, flag_name, var_name=None):
        """Ensure a dependency is available."""

        try:
                module = importlib.import_module(module_name)
                if var_name:
                        globals()[var_name] = module
                globals()[flag_name] = True
                return True, f"{package} available"
        except ImportError:
                cmd = [sys.executable, "-m", "pip", "install", package]
                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode != 0:
                        globals()[flag_name] = False
                        log.error("Installation failed: %s", proc.stderr)
                        return False, proc.stderr
                try:
                        importlib.invalidate_caches()
                        module = importlib.import_module(module_name)
                        if var_name:
                                globals()[var_name] = module
                        globals()[flag_name] = True
                        return True, f"{package} installed"
                except Exception as e:
                        globals()[flag_name] = False
                        log.error("Import failed after installation", exc_info=True)
                        return False, str(e)


#GDAL
gdal = None
try:
        from osgeo import gdal as _gdal
        gdal = _gdal
except Exception:
        HAS_GDAL = False
        log.debug('GDAL Python binding unavailable')
else:
        HAS_GDAL = True
        log.debug('GDAL Python binding available')


#PyProj
try:
	import pyproj
except:
	HAS_PYPROJ = False
	log.debug('PyProj unavailable')
else:
	HAS_PYPROJ = True
	log.debug('PyProj available')


#PIL/Pillow
try:
	from PIL import Image
except:
	HAS_PIL = False
	log.debug('Pillow unavailable')
else:
	HAS_PIL = True
	log.debug('Pillow available')


#Imageio freeimage plugin
try:
	from .lib import imageio
	imageio.plugins._freeimage.get_freeimage_lib() #try to download freeimage lib
except Exception as e:
        log.error("Cannot install ImageIO's Freeimage plugin", exc_info=True)
        HAS_IMGIO = False
else:
        HAS_IMGIO = True
        log.debug('ImageIO Freeimage plugin available')


def ensure_dependencies():
        """Install missing Python dependencies."""

        deps = [
                ("osgeo.gdal", "gdal", "HAS_GDAL", "gdal"),
                ("pyproj", "pyproj", "HAS_PYPROJ", None),
                ("PIL", "Pillow", "HAS_PIL", None),
        ]
        results = {}
        for module, package, flag, var in deps:
                ok, msg = ensure_dependency(module, package, flag_name=flag, var_name=var)
                results[package] = (ok, msg)
        return results
