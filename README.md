# Doubao Audio to Text Batch Transcriber

把一个文件夹里的本地音频，批量转成 `.txt` 文字稿。

这个项目基于豆包语音识别 API，适合下面这类场景：

- 采访录音转文字
- 会议录音整理
- 播客音频转稿
- 课程录音转写
- 语音备忘录批量处理

它的目标很直接：

1. 你把音频放进 `input/`
2. 你运行一次脚本，或者双击一次 `.bat`
3. 你在 `output/` 里拿到同名 `.txt`

## 先拿 API Key

如果你还没有豆包语音的 API Key，先看官方入口：

- 豆包语音新版控制台快速入门：https://www.volcengine.com/docs/6561/2119699?lang=zh
- 豆包语音 API Key 使用文档：https://www.volcengine.com/docs/6561/1816214?lang=zh
- 火山引擎控制台：https://console.volcengine.com/

说明：

- 这个项目当前走的是豆包语音的录音文件 `极速版` 接口
- 官方接口文档：https://www.volcengine.com/docs/6561/1631584?lang=zh
- 官方标准版文档：https://www.volcengine.com/docs/6561/1354868?lang=zh

根据官方文档，`极速版` 支持直接上传本地音频内容，不要求你先把音频放到公网 URL。

## Demo

### 使用前

```text
input/
|- Episode-01.mp3
|- Meeting-Notes.m4a
`- archive/
   `- Lecture.wav
```

### 使用后

```text
output/
|- Episode-01.txt
|- Meeting-Notes.txt
|- archive/
|  `- Lecture.txt
`- transcribe_results.jsonl
```

### 运行示例

```powershell
PS C:\Users\you\doubao-audio-to-text-batch-transcriber> python .\doubao_batch_transcribe.py .\input .\output --api-key "your-api-key" --recursive
[1/3] TRANSCRIBE C:\Users\you\doubao-audio-to-text-batch-transcriber\input\Episode-01.mp3
[1/3] DONE C:\Users\you\doubao-audio-to-text-batch-transcriber\output\Episode-01.txt
[2/3] TRANSCRIBE C:\Users\you\doubao-audio-to-text-batch-transcriber\input\Meeting-Notes.m4a
[2/3] DONE C:\Users\you\doubao-audio-to-text-batch-transcriber\output\Meeting-Notes.txt
[3/3] TRANSCRIBE C:\Users\you\doubao-audio-to-text-batch-transcriber\input\archive\Lecture.wav
[3/3] DONE C:\Users\you\doubao-audio-to-text-batch-transcriber\output\archive\Lecture.txt
Finished. success=3, skipped=0, failed=0, log=C:\Users\you\doubao-audio-to-text-batch-transcriber\output\transcribe_results.jsonl
```

## 实际流程示意

### 1. 配置 API Key 和目录

![配置示意](assets/step-config.svg)

### 2. 运行批量转写

![运行示意](assets/step-run.svg)

### 3. 查看输出结果

![输出示意](assets/step-output.svg)

### 总体流程

![流程图](assets/workflow.svg)

## 这个工具能做什么

- 批量处理本地音频文件
- 调用豆包语音识别 `极速版` API
- 不需要公网音频 URL
- 自动保留子目录结构
- 支持递归扫描文件夹
- 支持失败重试
- 支持保存原始 JSON 返回
- 支持命令行运行
- 支持 Windows 双击启动

## 3 分钟跑通

### 环境要求

- Windows / macOS / Linux
- Python 3.11+
- 一个可用的豆包语音 API Key

先确认 Python：

```powershell
python --version
```

### Windows 用户最快方式

1. 下载或克隆本仓库
2. 打开 `config.example.json`
3. 复制一份为 `config.json`
4. 把里面的占位 `api_key` 改成你自己的真实 key
5. 把音频文件放进 `input/`
6. 双击 `run_transcribe.bat`
7. 到 `output/` 查看生成的 `.txt`

### 命令行方式

```powershell
python .\doubao_batch_transcribe.py .\input .\output --api-key "your-api-key" --recursive
```

## 项目结构

```text
.
|- doubao_batch_transcribe.py   # 主脚本
|- run_transcribe.bat           # Windows 双击启动器
|- config.example.json          # 配置模板
|- config.json                  # 本地私有配置，不进 git
|- input/                       # 本地音频输入目录
|- output/                      # 本地转写输出目录
`- assets/
   |- workflow.svg
   |- step-config.svg
   |- step-run.svg
   `- step-output.svg
```

## 配置说明

推荐方式是把真实 API Key 放在本地 `config.json` 中。

示例：

```json
{
  "api_key": "your_api_key",
  "input_dir": "input",
  "output_dir": "output",
  "resource_id": "volc.bigasr.auc_turbo",
  "extensions": [".mp3", ".wav", ".m4a", ".ogg", ".opus", ".mp4", ".flac", ".aac", ".wma"],
  "recursive": true,
  "overwrite": false,
  "retries": 2,
  "retry_wait": 3,
  "request_timeout": 600,
  "language": "",
  "save_json": false
}
```

字段解释：

- `api_key`：新版控制台认证方式
- `app_key` + `access_key`：旧版控制台认证方式
- `input_dir`：音频输入目录
- `output_dir`：转写输出目录
- `resource_id`：默认 `volc.bigasr.auc_turbo`
- `extensions`：要扫描的音频扩展名
- `recursive`：是否递归扫描子目录
- `overwrite`：是否覆盖已有 `.txt`
- `retries`：失败重试次数
- `retry_wait`：重试等待秒数
- `request_timeout`：接口请求超时秒数
- `language`：可选语言提示，比如 `zh-CN`
- `save_json`：是否保存接口原始 JSON

## 用法

### 只用配置文件运行

```powershell
python .\doubao_batch_transcribe.py
```

### 指定命令行参数运行

```powershell
python .\doubao_batch_transcribe.py .\input .\output --api-key "your-api-key" --recursive
```

### 指定另一份配置文件

```powershell
python .\doubao_batch_transcribe.py --config .\my_config.json
```

### 旧版认证方式

```powershell
python .\doubao_batch_transcribe.py .\input .\output --app-key "your-app-key" --access-key "your-access-key" --recursive
```

命令行参数会覆盖 `config.json` 中的同名配置。

## 支持的音频格式

默认会扫描这些扩展名：

- `.mp3`
- `.wav`
- `.m4a`
- `.ogg`
- `.opus`
- `.mp4`
- `.flac`
- `.aac`
- `.wma`

## 输出规则

- `input/demo.mp3` 会生成 `output/demo.txt`
- 子目录结构会保留
- 日志会追加写入 `output/transcribe_results.jsonl`
- 开启 `save_json` 后，会额外保存原始接口返回

## 常见问题

### 1. `unrecognized arguments`

通常是命令行参数拼错了。

先看帮助：

```powershell
python .\doubao_batch_transcribe.py --help
```

### 2. `Missing auth`

说明你没有提供有效的认证信息。

检查：

- `config.json` 里是否有 `api_key`
- 或者命令里是否传了 `--api-key`
- 或者你是否同时传了 `--app-key` 和 `--access-key`

### 3. `No matching audio files found`

说明输入目录为空，或者扩展名不在当前配置的 `extensions` 里。

### 4. 请求失败

优先排查：

- API Key 是否可用
- 账号是否有豆包语音识别权限
- 音频格式是否支持
- 文件是否过大

## 安全说明

- `config.json` 已加入 `.gitignore`
- 真实 API Key 只应该保存在你本地的 `config.json`
- 不要把 `input/`、`output/`、日志文件提交到公开仓库
- 如果你把真实 API Key 发到聊天、截图、Issue 或公开页面里，应该立刻去控制台重建

## 为什么现在先做 README，而不是先做 GUI

因为当前这个项目已经能稳定完成核心工作，先把公开页面做清楚，用户更容易：

- 看懂它做什么
- 直接拿去跑通
- 判断它是否适合自己
- 在 GitHub 搜索里找到它

这一步做完，后面再做 GUI，传播效率会更高。

## 后续计划

- 补更多真实操作截图
- 增加拖拽式桌面 GUI
- 增加进度条和任务状态
- 增加 `.srt` 等导出格式
- 为长音频增加标准版流程
- 做成更适合普通用户的桌面应用

## 开发说明

这个仓库目前保持得比较克制：

- 不依赖第三方 Python 包
- 先保证核心链路稳定
- 后续 GUI 可以在现有转写核心上继续封装

## License

当前仓库还没有添加正式 License 文件。
