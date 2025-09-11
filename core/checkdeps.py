import logging
import subprocess
import sys
import importlib

log = logging.getLogger(__name__)

#GDAL
gdal = None
try:
        from osgeo import gdal as _gdal
        gdal = _gdal
except ImportError:
        HAS_GDAL = False
        log.debug('GDAL Python binding unavailable')
except Exception:
        HAS_GDAL = False
        log.error('Unexpected error importing GDAL', exc_info=True)
else:
        HAS_GDAL = True
        log.debug('GDAL Python binding available')


def _gdal_install_hint():
        if sys.platform.startswith("win"):
                return "Download GDAL wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal and install it manually."
        if sys.platform == "darwin":
                return "Install GDAL via Homebrew: brew install gdal"
        return "Refer to https://gdal.org/download.html#binaries for platform specific instructions"


def ensure_gdal():
        """Ensure GDAL Python bindings are installed."""
        global HAS_GDAL, gdal

        try:
                from osgeo import gdal as _gdal
                gdal = _gdal
                HAS_GDAL = True
                return True, "GDAL available"
        except ImportError:
                HAS_GDAL = False
        except Exception:
                HAS_GDAL = False
                log.error('Unexpected error importing GDAL', exc_info=True)

        try:
                import pip  # noqa: F401
        except Exception:
                try:
                        import ensurepip
                        ensurepip.bootstrap()
                except Exception as e:
                        log.error("pip not available", exc_info=True)
                        return False, f"pip not available: {e}"

        cmd = [sys.executable, "-m", "pip", "install", "gdal"]
        log.info("Installing GDAL via pip")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
                log.error("GDAL installation failed: %s", proc.stderr)
                return False, _gdal_install_hint()

        try:
                gdal = importlib.import_module("osgeo.gdal")
                HAS_GDAL = True
                log.info("GDAL installed successfully")
                return True, "GDAL installed"
        except ImportError as e:
                HAS_GDAL = False
                log.error("GDAL import failed after installation", exc_info=True)
                return False, str(e)
        except Exception as e:
                HAS_GDAL = False
                log.error("Unexpected error importing GDAL after installation", exc_info=True)
                return False, str(e)


#PyProj
try:
        import pyproj
except ImportError:
        HAS_PYPROJ = False
        log.debug('PyProj unavailable')
except Exception:
        HAS_PYPROJ = False
        log.error('Unexpected error importing PyProj', exc_info=True)
else:
        HAS_PYPROJ = True
        log.debug('PyProj available')


#PIL/Pillow
try:
        from PIL import Image
except ImportError:
        HAS_PIL = False
        log.debug('Pillow unavailable')
except Exception:
        HAS_PIL = False
        log.error('Unexpected error importing Pillow', exc_info=True)
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
