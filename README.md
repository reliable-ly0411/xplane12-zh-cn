# X-Plane 12 简体中文与双语补丁

为 X-Plane 12 补充中文界面，并在专业操作页面保留英文名称，便于查阅英文手册、搜索命令和配置控制器。补丁从本地汉化成果中独立提取，提供离线安装、文件校验和恢复工具。

**这是社区补丁，不是 Laminar Research 官方发布。仓库不包含游戏 EXE、完整原始语言包、用户配置、账号信息或游戏备份。** 安装时使用你自己已安装的游戏原文件生成结果，不需要联网，也不需要第三方 Python 库。

## 汉化范围

| 页面／内容 | 显示规则 |
| --- | --- |
| 主菜单、普通设置 | 中文 |
| 按键／控制器命令、控制轴名称 | 中文在前，英文在后 |
| 故障项目、主要分类和状态 | 中文在前，英文在后 |
| 数据输出的 173 个项目名称 | **English (中文)**，如 `Frame rate (帧率)` |
| 数据输出列标题与操作按钮 | 中文 |
| 命令标识符、Dataref 路径、输出编号 | 保持原样 |

生成后的词典包含 **12,299** 个词条，其中 **5,298** 个双语词条；覆盖全部 **3,144** 条内置命令描述，并补充原厂飞机脚本命令。仓库只保存 **7,869** 项新增或修改的翻译，不重复分发未改动的原始词条。

第三方飞机／插件自行绘制的界面、图片内文字、语音及个别底层错误消息不在完整覆盖范围内。命令和 Dataref 的 API 名称不翻译。

## 适用版本与准备

- **Steam Windows 版 X-Plane 12.4.3-r2-15ff1e4d**。
- 支持在 Windows 上安装，或为 Linux 上通过 Proton 运行的 **Windows 版**安装；不适用于原生 Linux ELF 或 macOS 主程序。
- Python **3.9 或更高版本**，仅使用标准库。
- 安装、恢复前完全退出 X-Plane。不要同时运行 Steam 更新、文件验证或其他补丁工具。
- 确保游戏目录可写，建议预留至少 **500 MB** 临时空间和备份空间。
- 工具以文件 SHA-256 精确匹配版本。仅版本号相同但哈希不一致也会拒绝覆盖，不提供跳过版本校验选项。

## 下载与部署

在 GitHub 点击 **Code → Download ZIP**，解压到任意工作目录；也可运行：

```bash
git clone https://github.com/reliable-ly0411/xplane12-zh-cn.git
cd xplane12-zh-cn
```

补丁不需要放进 `Resources/plugins`。请在包含 `patch.py` 的目录打开终端，使用实际游戏安装路径替换下列示例。

### Windows（PowerShell）

```powershell
# 检查原文件是否匹配
py -3 patch.py check "D:\SteamLibrary\steamapps\common\X-Plane 12"

# 可选：生成并验证结果，但不写入游戏目录
py -3 patch.py apply "D:\SteamLibrary\steamapps\common\X-Plane 12" --dry-run

# 安装；自动保存原始 EXE 和词典
py -3 patch.py apply "D:\SteamLibrary\steamapps\common\X-Plane 12"

# 验证两个文件均显示 patched
py -3 patch.py check "D:\SteamLibrary\steamapps\common\X-Plane 12"
```

如果系统使用 `python` 命令，将 `py -3` 替换为 `python`。

### Linux（Steam／Proton）

```bash
python3 patch.py check "/path/to/steamapps/common/X-Plane 12"
python3 patch.py apply "/path/to/steamapps/common/X-Plane 12" --dry-run
python3 patch.py apply "/path/to/steamapps/common/X-Plane 12"
python3 patch.py check "/path/to/steamapps/common/X-Plane 12"
```

安装完成后，从 Steam 启动游戏。在通用设置中选择中文；若刚切换语言，重启游戏使其生效。工具不会自动修改语言偏好、Steam 启动参数、显卡设置、按键绑定或控制器配置。

### 恢复原版

退出游戏后执行：

```powershell
py -3 patch.py restore "D:\SteamLibrary\steamapps\common\X-Plane 12"
```

Linux 使用：

```bash
python3 patch.py restore "/path/to/steamapps/common/X-Plane 12"
```

原文件保存在游戏目录的 `.xplane12-zh-cn-backup/` 中。恢复仅替换 `X-Plane.exe` 和 `Resources/text/Chinese.txt`，不会覆盖用户偏好。恢复后备份仍保留，可再次安装。

如果此前已经使用同版本的手工补丁，可以将包含原始 `X-Plane.exe` 和 `Resources/text/Chinese.txt` 的备份目录传给 `apply --original-dir "/path/to/original-backup"`。工具会核对原文件哈希，不能用未知版本或修改过的文件冒充原始备份。

## 更新与故障处理

- **Steam 更新或“验证游戏文件完整性”可能覆盖补丁。** 更新后先运行 `check`；出现 `unsupported` 时停止，不要强行安装旧补丁，也不要把旧 EXE 复制回新版游戏。
- `original` 表示文件匹配支持的原版，`patched` 表示文件匹配本补丁输出，`unsupported` 表示当前版本或文件修改不匹配。
- 部分文件已安装、部分为原版时，只要有效备份存在且所有文件均为已知哈希，可再次 `apply` 或 `restore` 恢复一致状态。
- 检测到未知修改会拒绝覆盖。请保留现有文件和备份，先确认来源，不要删除备份来绕过检查。
- 无 `state.json` 的备份目录可能来自中断的首次安装；工具会保留并拒绝覆盖它。先核实原始文件与清单哈希，再将该目录移到安全位置后重试。
- 若系统突然断电，两个目标文件可能处于一新一旧的状态。确认备份完整后运行 `restore`；工具不承诺跨两个文件的断电原子性。

## 实现方式

`data/translation-overlay.json` 保存词典新增／修改项。安装器读取使用者自己的原版词典，合并后生成 UTF-8、LF 格式的 `Chinese.txt`，并校验最终哈希。

数据输出的 173 个项目名称直接保存在当前版本 EXE 中，没有使用普通语言词典。因此 `pe_labels.py` 在本地为该版本新增只读文字节，调整对应的 173 个文字指针及必要 PE 元数据。算法检查已有 ASLR 重定位、修改字节范围及 `.text` 指令区不变，最后再次校验整个文件哈希。它不修改模拟逻辑、导入表、输出编号或 DRM。

仓库只保存文字、指针位置和处理代码；**不会分发原始或打过补丁的 EXE**。

## 验证情况

已在 Steam Windows 版通过 Linux／Proton 的实际游戏界面检查：

- 数据输出英文在前，可见文本没有遮挡勾选列。
- 键盘命令中英对照，以及英文搜索。
- 发动机故障项目与状态中英对照。
- VR 设置中文显示；个别 OpenXR 底层错误消息仍为英文。
- 游戏日志未发现语言文件错误；占位参数、内嵌命令引用通过静态检查。
- 命令定义、键盘绑定和控制器设置文件与修改前一致。

尚未进行 Windows 原生游戏运行验证，也未在连接实体控制器的情况下检查校准页面；未执行 UDP／磁盘数据输出传输测试。上述限制不应理解为已通过测试。

运行不需要游戏文件的测试：

```bash
python3 -m unittest discover -s tests -v
```

持有受支持的原版文件时，可以额外验证生成、安装与恢复（仅操作临时副本）：

```bash
python3 tests/integration.py "/path/to/original-game-or-backup"
```

## 文件说明

| 文件 | 用途 |
| --- | --- |
| `patch.py` | 检查、生成、安装、备份和恢复 |
| `pe_labels.py` | 指定版本的数据输出文字表处理 |
| `data/translation-overlay.json` | 新增／修改的翻译 |
| `data/data-output-labels.json` | 173 个数据输出名称及其定位信息 |
| `data/manifest.json` | 版本、原文件和生成结果的 SHA-256 |
| `tests/` | 数据一致性、拒绝未知修改、安装恢复验证 |

## 来源与说明

翻译以游戏随附中文词典为基础补充、整理，并在专业页面保留英文对照。原始游戏名称、英文字符串、既有翻译及商标归各自权利人所有；本仓库不声明对这些内容的独占权利，也不代表官方认可。使用者需自行持有游戏文件。

格式依据：[X-Plane 官方本地化说明](https://www.x-plane.com/kb/localization/)、[语言文件错误说明](https://www.x-plane.com/kb/localization-error-messages/)、[Microsoft PE 格式](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format)。
