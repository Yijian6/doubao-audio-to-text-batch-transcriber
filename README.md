# Doubao Batch Transcribe

Batch transcribe local audio files into `.txt` files with Volcengine/Doubao ASR.

This project now supports two usage modes:

- command line: pass directories and auth directly
- local app-style usage: edit `config.json`, then double-click `run_transcribe.bat`

The current implementation uses Doubao recorded-audio `flash` recognition, which supports direct local file upload and does not require a public audio URL.

Official docs:

- Flash API: https://www.volcengine.com/docs/6561/1631584
- Standard API: https://www.volcengine.com/docs/6561/1354868

## Files

- `doubao_batch_transcribe.py`: main script
- `config.example.json`: tracked config template
- `config.json`: local config file, ignored by git
- `run_transcribe.bat`: Windows double-click launcher

## Recommended usage

1. Copy `config.example.json` to `config.json` if needed
2. Replace `api_key` with your own current key
3. Put audio files into `input`
4. Double-click `run_transcribe.bat`
5. Read results from `output`

## config file fields

```json
{
  "api_key": "your_api_key",
  "input_dir": "input",
  "output_dir": "output",
  "resource_id": "volc.bigasr.auc_turbo",
  "extensions": [".mp3", ".wav", ".m4a"],
  "recursive": true,
  "overwrite": false,
  "retries": 2,
  "retry_wait": 3,
  "request_timeout": 600,
  "language": "",
  "save_json": false
}
```

Recommended:

- keep `config.example.json` as the shared template
- keep your real key only in local `config.json`

Notes:

- `api_key`: new-console auth
- `app_key` + `access_key`: old-console auth, if you use that path
- `recursive`: scan subfolders
- `overwrite`: rewrite existing `.txt`
- `save_json`: save raw API responses beside `.txt`

## Command-line usage

New console auth:

```powershell
python .\doubao_batch_transcribe.py .\input .\output --api-key "your-api-key" --recursive
```

Old console auth:

```powershell
python .\doubao_batch_transcribe.py .\input .\output --app-key "your-app-key" --access-key "your-access-key" --recursive
```

Config-file usage:

```powershell
python .\doubao_batch_transcribe.py
```

Or specify another config file:

```powershell
python .\doubao_batch_transcribe.py --config .\my_config.json
```

Command-line arguments override `config.json`.

## Output

- `input\demo.mp3` -> `output\demo.txt`
- folder structure is preserved
- logs are appended to `output\transcribe_results.jsonl`

## Limits

This project currently targets the flash API path.

- Good fit: local files, fast batch conversion
- If a single file later exceeds `2 hours` or `100MB`, you should switch to the standard API flow
