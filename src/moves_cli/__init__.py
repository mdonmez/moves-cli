import os
import sys
from pathlib import Path


def _setup_windows_dlls():
    """
    Fix for Windows DLL conflict where System32/onnxruntime.dll (from WinML)
    takes precedence over the bundled version in Python packages.
    """
    if sys.platform != "win32":
        return

    import importlib.util

    def _add_pkg_dlls(pkg_name):
        spec = importlib.util.find_spec(pkg_name)
        if spec and spec.origin:
            pkg_path = Path(spec.origin).parent
            # Common DLL locations in Python packages
            for sub in ["", "lib", "capi"]:
                dll_dir = pkg_path / sub
                if dll_dir.exists():
                    # official way for Python 3.8+
                    os.add_dll_directory(str(dll_dir.resolve()))
                    # legacy way for some compiled extensions
                    os.environ["PATH"] = (
                        str(dll_dir.resolve()) + os.pathsep + os.environ["PATH"]
                    )

    try:
        _add_pkg_dlls("onnxruntime")
        _add_pkg_dlls("sherpa_onnx")
    except Exception:
        # Don't let DLL setup crash the app
        pass


# Initialize DLLs before any other imports
_setup_windows_dlls()
