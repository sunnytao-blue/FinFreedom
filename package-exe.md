# PyInstaller 打包 Streamlit 应用 — 经验总结

## 1. 概述

将 Streamlit 应用打包为 Windows `.exe` 单文件过程中遇到的核心问题：**Streamlit 的 Web 服务器启动正常，但浏览器访问时页面无法加载**（Not Found 或模块缺失错误）。

根本原因：

1. **Streamlit 的静态文件和多层子模块未被 PyInstaller 自动发现**
2. **环境变量与 CLI 参数冲突导致端口配置不生效**

---

## 2. 最终可用方案

### 2.1 目录结构

```
FinFreedom/
├── app.py                  # Streamlit 主入口
├── launcher.py             # PyInstaller 启动脚本
├── FinFreedom.spec         # PyInstaller 规范文件
├── modules/                # 业务模块
├── models/                 # 数据模型
└── utils/                  # 工具函数
```

### 2.2 关键文件

**`launcher.py`**（PyInstaller 入口）：

```python
import os, sys, webbrowser, threading, time

_frozen = getattr(sys, "frozen", False)
if _frozen:
    if hasattr(sys, "_MEIPASS"):
        _meipass = sys._MEIPASS       # onefile 模式
    else:
        _meipass = os.path.join(os.path.dirname(sys.executable), "_internal")  # onedir（备用）
else:
    _meipass = os.path.dirname(os.path.abspath(__file__))

os.chdir(_meipass)
sys.path.insert(0, _meipass)

os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

PORT = 3568

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
```

**`FinFreedom.spec`** 关键配置：

```python
from PyInstaller.utils.hooks import copy_metadata, collect_data_files, collect_submodules
import os, sys

# 1. 必须包含 Streamlit 前端静态文件（否则页面 Not Found）
datas += collect_data_files('streamlit')

# 2. 必须递归收集所有 Streamlit 子模块（否则缺失 magic_funcs 等）
hiddenimports = collect_submodules('streamlit')

# 3. 必须复制包元数据（否则 PackageNotFoundError）
datas += copy_metadata('streamlit')

# 4. 必须显式包含缺失的系统 DLL（conda 环境特有）
#    使用 sys.prefix 自动定位 conda 环境目录（避免硬编码用户名）
conda_bin = os.path.join(sys.prefix, 'Library', 'bin')
binaries = [
    (f'{conda_bin}\\libcrypto-3-x64.dll', '.'),
    (f'{conda_bin}\\libssl-3-x64.dll', '.'),
    (f'{conda_bin}\\sqlite3.dll', '.'),
    (f'{conda_bin}\\ffi.dll', '.'),
    (f'{conda_bin}\\libexpat.dll', '.'),
    (f'{conda_bin}\\liblzma.dll', '.'),
]

# 5. 使用 onefile 模式（EXE 块，无 COLLECT 块）
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
          name='财务自由评估', ...)
```

---

## 3. 踩过的坑及解决方案

| 问题 | 症状 | 根因 | 解决 |
|------|------|------|------|
| **1. 端口不一致** | 浏览器打开 3000 而非指定的 3568 | `global.developmentMode` 自动开启 | `STREAMLIT_GLOBAL_DEVELOPMENT_MODE=false` |
| **2. PackageNotFoundError** | `No package metadata was found for streamlit` | PyInstaller 未打包 streamlit 的 `dist-info` | 添加 `copy_metadata('streamlit')` |
| **3. _ssl DLL 缺失** | `ImportError: DLL load failed while importing _ssl` | conda 环境的 OpenSSL DLL 未包含 | 显式添加 `libcrypto-3-x64.dll` 等到 `binaries` |
| **4. 静态文件缺失** | 页面 Not Found | Streamlit 前端 HTML/JS/CSS 未打包 | `collect_data_files('streamlit')` |
| **5. ModuleNotFoundError** | `No module named 'streamlit.runtime.scriptrunner.magic_funcs'` | Streamlit 内部动态 import 未被 PyInstaller 分析到 | `collect_submodules('streamlit')` |
| **6. 端口冲突** | `RuntimeError: server.port does not work when global.developmentMode is true` | 开发模式锁定端口 | 环境变量 `STREAMLIT_GLOBAL_DEVELOPMENT_MODE=false` |
| **7. 打包后端口被覆盖** | CLI 参数 `--server.port` 被忽略 | 环境变量和 CLI 参数优先级混淆 | 同时使用环境变量 + CLI 参数双重指定端口 |
| **8. 中文路径问题** | PowerShell 显示乱码 | Windows 控制台编码与 UTF-8 不匹配 | `.bat` 文件使用 ANSI(GBK) 编码或纯 ASCII |
| **9. 文件被锁定** | `PermissionError` 打包失败 | 上次运行的程序未关闭 | 确保程序已退出再打包；`重打包.bat` 含 `taskkill` |
| **10. 默认值不生效** | 修改默认值后启动仍显示旧值 | 持久化的 `~\.finfreedom_config.json` 缓存了旧值 | 修改默认值后删除 config.json 或点击「恢复默认值」 |
| **11. 恢复默认值/导入参数不刷新 UI** | 点击后表单数值不变 | Streamlit widget 的浏览器缓存覆盖 Python 端 `st.session_state` | 版本化 widget key（`widget_ver` 递增），强制重新创建小部件 |
| **12. Streamlit API 废弃** | `use_container_width` 将被移除 | Streamlit 1.58 不再支持 | 改为 `width="stretch"` |

---

## 4. 快速重新打包

修改程序源码后，运行 `重打包.bat` 或执行：

```bash
python -m PyInstaller --clean --noconfirm FinFreedom.spec
```

> 确保已关闭正在运行的 `财务自由评估.exe`（`重打包.bat` 会自动处理）。

输出为 `dist/财务自由评估.exe`（单文件约 82 MB）。

---

## 5. 分发注意事项

- 分发给用户的是 `dist/财务自由评估.exe`（单文件）
- 用户双击即可运行，浏览器自动打开 `http://localhost:3568`
- 关闭命令行窗口停止程序
- 参数自动保存在 `%USERPROFILE%\.finfreedom_config.json`
- 端口固定 **3568**，避免与 Streamlit 默认 8501 或其他服务冲突
