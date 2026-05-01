# Doubao Audio to Text Batch Transcriber

Batch transcribe a folder of local audio files into `.txt` files with the Doubao speech recognition API.

This project is built for a simple job:

- put audio files into one folder
- run one command or double-click one launcher
- get text transcripts in another folder

It is a good fit for:

- interview recordings
- meeting audio
- podcast clips
- lecture recordings
- voice notes

## Demo

### What it does

`input/`

```text
input/
|- Episode-01.mp3
|- Meeting-Notes.m4a
`- archive/
   `- Lecture.wav
```

Run the tool once, then get:

`output/`

```text
output/
|- Episode-01.txt
|- Meeting-Notes.txt
|- archive/
|  `- Lecture.txt
`- transcribe_results.jsonl
```

### Example terminal output

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

### Workflow

![Workflow](assets/workflow.svg)

## Features

- Batch transcribe local audio files into `.txt`
- Uses the Doubao recorded-audio flash API
- No public audio URL required
- Preserves subfolder structure in output
- Supports recursive folder scanning
- Supports retry on failure
- Supports raw JSON response export
- Supports command-line usage and double-click Windows usage

## Why this tool

Many speech-to-text tools focus on live dictation, browser recording, or larger desktop apps.

This project focuses on one narrower workflow:

1. you already have local audio files
2. you want to call Doubao ASR directly
3. you want plain transcript files in bulk

That makes it useful as a simple utility, and also a clean base for a future GUI app.

## Quick Start

### Requirements

- Windows, macOS, or Linux
- Python 3.11+
- A Doubao / Volcengine API key with speech recognition access

Check Python:

```powershell
python --version
```

## 3-Minute Setup

### Option 1: easiest for Windows users

1. Clone or download this repository
2. Open `config.example.json`
3. Copy it to `config.json`
4. Replace the placeholder API key with your own key
5. Put audio files into the `input` folder
6. Double-click `run_transcribe.bat`
7. Read transcripts from the `output` folder

### Option 2: command line

```powershell
python .\doubao_batch_transcribe.py .\input .\output --api-key "your-api-key" --recursive
```

## Repository Structure

```text
.
|- doubao_batch_transcribe.py   # main script
|- run_transcribe.bat           # Windows launcher
|- config.example.json          # shared config template
|- config.json                  # local config, ignored by git
|- input/                       # local input audio folder
|- output/                      # local output transcript folder
`- assets/
   `- workflow.svg
```

## Configuration

### `config.json`

The recommended setup is to keep your real API key in a local `config.json`.

Example:

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

### Field reference

- `api_key`: API key for the newer auth path
- `app_key` + `access_key`: older auth path, if your account uses it
- `input_dir`: folder containing local audio files
- `output_dir`: folder for generated `.txt` files
- `resource_id`: default is `volc.bigasr.auc_turbo`
- `extensions`: file extensions to scan
- `recursive`: scan subfolders
- `overwrite`: rewrite existing transcript files
- `retries`: retry count when requests fail
- `retry_wait`: delay between retries in seconds
- `request_timeout`: request timeout in seconds
- `language`: optional language hint such as `zh-CN` or `en-US`
- `save_json`: save the raw API response next to the `.txt`

## Usage

### Use config file only

```powershell
python .\doubao_batch_transcribe.py
```

### Use command-line arguments

```powershell
python .\doubao_batch_transcribe.py .\input .\output --api-key "your-api-key" --recursive
```

### Use another config file

```powershell
python .\doubao_batch_transcribe.py --config .\my_config.json
```

### Old auth path

```powershell
python .\doubao_batch_transcribe.py .\input .\output --app-key "your-app-key" --access-key "your-access-key" --recursive
```

Command-line arguments override values in `config.json`.

## Supported Audio Formats

By default, the tool scans:

- `.mp3`
- `.wav`
- `.m4a`
- `.ogg`
- `.opus`
- `.mp4`
- `.flac`
- `.aac`
- `.wma`

## Output Rules

- `input/demo.mp3` becomes `output/demo.txt`
- subfolder structure is preserved
- logs are appended to `output/transcribe_results.jsonl`
- when `save_json` is enabled, raw API responses are saved beside the transcript

## Security

- `config.json` is ignored by git
- your real API key should stay only in local `config.json`
- do not commit `input/`, `output/`, or transcript logs to a public repository
- if you ever paste a real API key into chat or a screenshot, rotate it immediately

## API Notes

This project currently targets the Doubao recorded-audio flash API.

That path is a good fit when:

- your audio files are local
- you want a direct upload workflow
- you want a simpler batch pipeline

Official docs:

- Flash API: https://www.volcengine.com/docs/6561/1631584
- Standard API: https://www.volcengine.com/docs/6561/1354868

If you later need to support very long files, the standard API path may be a better fit, but it usually requires a public audio URL workflow.

## Common Issues

### `unrecognized arguments`

One or more command-line options were typed incorrectly.

Check available options:

```powershell
python .\doubao_batch_transcribe.py --help
```

### `Missing auth`

You did not provide valid auth values.

Fix one of these:

- set `api_key` in `config.json`
- or provide `--api-key`
- or provide both `--app-key` and `--access-key`

### `No matching audio files found`

The input folder is empty, or the file extensions are not included in the configured `extensions` list.

### API request failed

Check:

- whether the API key is valid
- whether the key has ASR access
- whether the audio format is supported
- whether the file is too large for the flash path

## Roadmap

- better README screenshots and real demo samples
- drag-and-drop desktop GUI
- progress bar and clearer task states
- transcript export formats such as `.srt`
- long-audio fallback flow
- packaging for non-technical users

## Development Notes

This repository is intentionally small and conservative:

- no third-party Python dependency is required
- the current goal is reliability and clarity
- future UI work can build on the existing core transcription flow

## License

No license file has been added yet.
