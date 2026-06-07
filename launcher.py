import os
import sys
import webbrowser
import threading
import time

_frozen = getattr(sys, "frozen", False)
if _frozen:
    if hasattr(sys, "_MEIPASS"):
        _meipass = sys._MEIPASS       # onefile 模式
    else:
        _meipass = os.path.join(os.path.dirname(sys.executable), "_internal")  # onedir 模式
else:
    _meipass = os.path.dirname(os.path.abspath(__file__))

os.chdir(_meipass)
sys.path.insert(0, _meipass)

PORT = 3568

os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"


def _open_browser():
    time.sleep(4)
    webbrowser.open(f"http://localhost:{PORT}")


if __name__ == "__main__":
    threading.Thread(target=_open_browser, daemon=True).start()

    sys.argv = [
        "streamlit", "run", os.path.join(_meipass, "app.py"),
        "--server.port", str(PORT),
        "--server.headless", "true",
    ]
    from streamlit.web import cli as stcli
    sys.exit(stcli.main())
