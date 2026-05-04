#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from doubao_batch_transcribe import (
    DEFAULT_CONFIG_NAME,
    DEFAULT_RESOURCE_ID,
    SUPPORTED_EXTENSIONS,
    apply_config,
    iter_audio_files,
    load_config,
    namespace_to_config,
    normalized_extensions,
    run_batch_transcription,
    save_config,
)


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("豆包音频转文字批量工具")
        self.root.geometry("1040x820")
        self.root.minsize(960, 720)
        self.root.configure(bg="#f4f2ee")

        self.config_path = Path(DEFAULT_CONFIG_NAME)
        self.queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.worker: threading.Thread | None = None

        self.api_key_var = tk.StringVar()
        self.input_dir_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=True)
        self.overwrite_var = tk.BooleanVar(value=False)
        self.save_json_var = tk.BooleanVar(value=False)
        self.retries_var = tk.IntVar(value=2)
        self.status_var = tk.StringVar(value="就绪")
        self.summary_var = tk.StringVar(value="成功 0 | 跳过 0 | 失败 0")
        self.preview_var = tk.StringVar(value="待扫描")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.preview_limit = 200

        self._build_ui()
        self._load_config_into_form()
        self.root.after(120, self._poll_queue)

    def _configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        # Gallery palette: warm paper, graphite accents, no decoration.
        bg = "#f4f2ee"          # warm off-white canvas
        panel = "#faf9f7"       # lifted surface, barely distinguishable
        border = "#ddd9d2"      # thin graphite divider
        text = "#2c2a26"        # soft-black body text
        muted = "#9b9590"       # gallery-placard secondary text
        accent = "#2c2a26"      # accent = text, no color pop
        field_bg = "#ffffff"
        ui_font = "Microsoft YaHei UI"

        style.configure(".", background=bg, foreground=text)
        style.configure("TFrame", background=bg)
        style.configure("Panel.TFrame", background=panel, borderwidth=1, relief="solid", bordercolor=border)
        style.configure("Surface.TFrame", background=panel)

        # Typography hierarchy: generous sizing, light weight where possible.
        style.configure("TLabel", background=bg, foreground=text, font=(ui_font, 10))
        style.configure("Title.TLabel", background=bg, foreground=text, font=(ui_font, 22))
        style.configure("Subtitle.TLabel", background=bg, foreground=muted, font=(ui_font, 10))
        style.configure("Section.TLabel", background=bg, foreground=muted, font=(ui_font, 9))
        style.configure("InlineTitle.TLabel", background=panel, foreground=muted, font=(ui_font, 9))
        style.configure("InlineValue.TLabel", background=panel, foreground=text, font=(ui_font, 10))

        style.configure("TEntry", fieldbackground=field_bg, bordercolor=border, lightcolor=border, darkcolor=border, font=(ui_font, 10))
        style.configure("TSpinbox", fieldbackground=field_bg, bordercolor=border, lightcolor=border, darkcolor=border)
        style.configure("TCheckbutton", background=bg, foreground=text, font=(ui_font, 10))

        # Buttons: flat, graphite, no visual noise.
        style.configure("TButton", padding=(12, 6), font=(ui_font, 10), bordercolor=border, lightcolor=border, darkcolor=border)
        style.map("TButton", background=[("active", "#eae8e4")])
        style.configure("Primary.TButton", background=accent, foreground="#ffffff", borderwidth=0, padding=(18, 7), font=(ui_font, 10))
        style.map(
            "Primary.TButton",
            background=[("active", "#444240"), ("disabled", "#c8c5c0")],
            foreground=[("disabled", "#e8e6e2")],
        )
        style.configure("Quiet.TButton", background=panel, foreground=text, bordercolor=border, lightcolor=border, darkcolor=border, font=(ui_font, 10))
        style.map("Quiet.TButton", background=[("active", "#eeecea")])

        style.configure("TSeparator", background=border)
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor="#eae8e4",
            background=accent,
            bordercolor="#eae8e4",
            lightcolor=accent,
            darkcolor=accent,
        )

    def _build_ui(self) -> None:
        self._configure_style()
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(6, weight=1)

        PAD_X = 44          # generous gallery margins
        ROW_SPACING = 10    # breathing room between form rows

        # Header
        header = ttk.Frame(self.root, padding=(PAD_X, 36, PAD_X, 0))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="豆包音频转文字", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(header, text="批量音频转写工具", style="Subtitle.TLabel").grid(
            row=1, column=0, sticky="w", pady=(4, 0)
        )

        # thin graphite rule
        ttk.Separator(self.root, orient="horizontal").grid(
            row=1, column=0, sticky="ew", padx=PAD_X, pady=(18, 0)
        )

        # Form
        form = ttk.Frame(self.root, padding=(PAD_X, 22, PAD_X, 0))
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="配置", style="Section.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 14)
        )

        ttk.Label(form, text="API Key").grid(row=1, column=0, sticky="w", pady=(0, ROW_SPACING), padx=(0, 16))
        ttk.Entry(form, textvariable=self.api_key_var, show="*").grid(
            row=1, column=1, columnspan=2, sticky="ew", pady=(0, ROW_SPACING)
        )

        ttk.Label(form, text="输入目录").grid(row=2, column=0, sticky="w", pady=(0, ROW_SPACING), padx=(0, 16))
        ttk.Entry(form, textvariable=self.input_dir_var).grid(
            row=2, column=1, sticky="ew", pady=(0, ROW_SPACING)
        )
        ttk.Button(form, text="选择", command=self._choose_input_dir, style="Quiet.TButton").grid(
            row=2, column=2, padx=(10, 0), pady=(0, ROW_SPACING)
        )

        ttk.Label(form, text="输出目录").grid(row=3, column=0, sticky="w", pady=(0, ROW_SPACING), padx=(0, 16))
        ttk.Entry(form, textvariable=self.output_dir_var).grid(
            row=3, column=1, sticky="ew", pady=(0, ROW_SPACING)
        )
        ttk.Button(form, text="选择", command=self._choose_output_dir, style="Quiet.TButton").grid(
            row=3, column=2, padx=(10, 0), pady=(0, ROW_SPACING)
        )

        # thin graphite rule
        ttk.Separator(self.root, orient="horizontal").grid(
            row=3, column=0, sticky="ew", padx=PAD_X, pady=(6, 0)
        )

        # Options
        options = ttk.Frame(self.root, padding=(PAD_X, 14, PAD_X, 0))
        options.grid(row=4, column=0, sticky="ew")
        options.columnconfigure(0, weight=1)
        options.columnconfigure(1, weight=1)
        options.columnconfigure(2, weight=1)
        options.columnconfigure(3, weight=1)

        ttk.Checkbutton(options, text="递归扫描", variable=self.recursive_var).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Checkbutton(options, text="覆盖已有结果", variable=self.overwrite_var).grid(
            row=0, column=1, sticky="w"
        )
        ttk.Checkbutton(options, text="保存 JSON", variable=self.save_json_var).grid(
            row=0, column=2, sticky="w"
        )
        retries_group = ttk.Frame(options)
        retries_group.grid(row=0, column=3, sticky="e")
        ttk.Label(retries_group, text="重试次数").pack(side="left", padx=(0, 8))
        ttk.Spinbox(
            retries_group,
            from_=0,
            to=10,
            width=5,
            textvariable=self.retries_var,
        ).pack(side="left")

        # Status bar
        status_panel = ttk.Frame(self.root, style="Panel.TFrame", padding=(18, 11))
        status_panel.grid(row=5, column=0, sticky="ew", padx=PAD_X, pady=(16, 0))
        status_panel.columnconfigure(0, weight=1)

        stats = ttk.Frame(status_panel, style="Surface.TFrame")
        stats.grid(row=0, column=0, sticky="w")
        self._build_inline_stat(stats, 0, "状态", self.status_var)
        self._build_inline_stat(stats, 1, "统计", self.summary_var)
        self._build_inline_stat(stats, 2, "待处理", self.preview_var)

        button_bar = ttk.Frame(status_panel, style="Surface.TFrame")
        button_bar.grid(row=0, column=1, sticky="e")
        self.save_button = ttk.Button(button_bar, text="保存", command=self._save_config, style="Quiet.TButton")
        self.save_button.grid(row=0, column=0, padx=(0, 8))
        self.open_button = ttk.Button(
            button_bar, text="打开输出", command=self._open_output_dir, style="Quiet.TButton"
        )
        self.open_button.grid(row=0, column=1, padx=(0, 8))
        self.scan_button = ttk.Button(
            button_bar, text="预扫描", command=self._scan_files, style="Quiet.TButton"
        )
        self.scan_button.grid(row=0, column=2, padx=(0, 8))
        self.start_button = ttk.Button(
            button_bar, text="开始转写", command=self._start_transcription, style="Primary.TButton"
        )
        self.start_button.grid(row=0, column=3)

        # Bottom area: progress and panels
        controls = ttk.Frame(self.root, padding=(PAD_X, 18, PAD_X, 28))
        controls.grid(row=6, column=0, sticky="nsew")
        controls.columnconfigure(0, weight=2)
        controls.columnconfigure(1, weight=3)
        controls.rowconfigure(3, weight=1)

        ttk.Label(controls, text="运行进度", style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10)
        )
        progress_frame = ttk.Frame(controls, style="Panel.TFrame", padding=(12, 10))
        progress_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        progress_frame.columnconfigure(0, weight=1)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode="determinate",
            variable=self.progress_var,
            maximum=100,
            style="Horizontal.TProgressbar",
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew")

        ttk.Label(controls, text="文件预览", style="Section.TLabel").grid(
            row=2, column=0, sticky="w", pady=(16, 8)
        )
        preview_frame = ttk.Frame(controls, style="Panel.TFrame", padding=6)
        preview_frame.grid(row=3, column=0, sticky="nsew", padx=(0, 14))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.preview_list = tk.Listbox(
            preview_frame,
            activestyle="none",
            bd=0,
            relief="flat",
            bg="#fdfcfb",
            fg="#2c2a26",
            selectbackground="#2c2a26",
            selectforeground="#fdfcfb",
            font=("Microsoft YaHei UI", 9),
            highlightthickness=0,
        )
        self.preview_list.grid(row=0, column=0, sticky="nsew")
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_list.yview)
        preview_scrollbar.grid(row=0, column=1, sticky="ns")
        self.preview_list.configure(yscrollcommand=preview_scrollbar.set)
        self.preview_list.insert("end", "点击“预扫描”查看待转写音频")

        ttk.Label(controls, text="运行日志", style="Section.TLabel").grid(
            row=2, column=1, sticky="w", pady=(16, 8)
        )
        log_frame = ttk.Frame(controls, style="Panel.TFrame", padding=6)
        log_frame.grid(row=3, column=1, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_frame,
            wrap="word",
            font=("Consolas", 10),
            height=18,
            bd=0,
            relief="flat",
            bg="#fdfcfb",
            fg="#2c2a26",
            insertbackground="#2c2a26",
            padx=14,
            pady=12,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _build_inline_stat(self, parent: ttk.Frame, column: int, title: str, variable: tk.StringVar) -> None:
        item = ttk.Frame(parent, style="Surface.TFrame")
        item.grid(row=0, column=column, sticky="w", padx=(0, 36))
        ttk.Label(item, text=title, style="InlineTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(item, textvariable=variable, style="InlineValue.TLabel").grid(row=1, column=0, sticky="w", pady=(3, 0))

    def _load_config_into_form(self) -> None:
        defaults = load_config(self.config_path)
        args = argparse.Namespace(
            input_dir=None,
            output_dir=None,
            api_key=None,
            app_key=None,
            access_key=None,
            resource_id=None,
            extensions=None,
            recursive=None,
            overwrite=None,
            retries=None,
            retry_wait=None,
            request_timeout=None,
            language=None,
            save_json=None,
        )
        args = apply_config(args, defaults)
        self.api_key_var.set(args.api_key or "")
        self.input_dir_var.set(str(args.input_dir) if args.input_dir else "input")
        self.output_dir_var.set(str(args.output_dir) if args.output_dir else "output")
        self.recursive_var.set(bool(args.recursive))
        self.overwrite_var.set(bool(args.overwrite))
        self.save_json_var.set(bool(args.save_json))
        self.retries_var.set(int(args.retries))

    def _choose_input_dir(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.input_dir_var.get() or ".")
        if selected:
            self.input_dir_var.set(selected)

    def _choose_output_dir(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.output_dir_var.get() or ".")
        if selected:
            self.output_dir_var.set(selected)

    def _build_args(self) -> argparse.Namespace:
        return argparse.Namespace(
            input_dir=Path(self.input_dir_var.get().strip()),
            output_dir=Path(self.output_dir_var.get().strip()),
            config=self.config_path,
            api_key=self.api_key_var.get().strip(),
            app_key=None,
            access_key=None,
            resource_id=DEFAULT_RESOURCE_ID,
            extensions=sorted(SUPPORTED_EXTENSIONS),
            recursive=self.recursive_var.get(),
            overwrite=self.overwrite_var.get(),
            retries=self.retries_var.get(),
            retry_wait=3.0,
            request_timeout=600,
            language="",
            save_json=self.save_json_var.get(),
        )

    def _save_config(self) -> None:
        args = self._build_args()
        save_config(self.config_path, namespace_to_config(args))
        self._append_log(f"已保存配置到 {self.config_path.resolve()}")
        self.status_var.set("配置已保存")

    def _set_running(self, running: bool) -> None:
        state = "disabled" if running else "normal"
        self.start_button.configure(state=state)
        self.save_button.configure(state=state)
        self.open_button.configure(state=state)
        self.scan_button.configure(state=state)

    def _append_log(self, message: str) -> None:
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def _collect_audio_files(self) -> tuple[Path, list[Path]]:
        input_dir = Path(self.input_dir_var.get().strip())
        if not str(input_dir).strip():
            raise ValueError("请选择输入目录。")
        if not input_dir.exists() or not input_dir.is_dir():
            raise ValueError("输入目录不存在，或不是有效文件夹。")

        files = iter_audio_files(
            input_dir,
            self.recursive_var.get(),
            normalized_extensions(sorted(SUPPORTED_EXTENSIONS)),
        )
        return input_dir, files

    def _refresh_preview_list(self, input_dir: Path, files: list[Path]) -> None:
        self.preview_list.delete(0, "end")
        if not files:
            self.preview_list.insert("end", "没有找到支持的音频文件")
            self.preview_var.set("0 个文件")
            return

        for audio_path in files[: self.preview_limit]:
            try:
                label = str(audio_path.relative_to(input_dir))
            except ValueError:
                label = audio_path.name
            self.preview_list.insert("end", label)

        hidden_count = len(files) - self.preview_limit
        if hidden_count > 0:
            self.preview_list.insert("end", f"... 还有 {hidden_count} 个文件")

        self.preview_var.set(f"{len(files)} 个文件")

    def _scan_files(self) -> None:
        try:
            input_dir, files = self._collect_audio_files()
        except ValueError as exc:
            messagebox.showerror("无法预扫描", str(exc))
            return

        self._refresh_preview_list(input_dir, files)
        self._append_log(f"预扫描完成：找到 {len(files)} 个待处理文件。")
        self.status_var.set("已完成预扫描")

    def _start_transcription(self) -> None:
        if self.worker and self.worker.is_alive():
            return

        args = self._build_args()
        if not args.api_key:
            messagebox.showerror("缺少 API Key", "请先填写 API Key。")
            return
        if not str(args.input_dir).strip():
            messagebox.showerror("缺少输入目录", "请选择输入目录。")
            return
        if not str(args.output_dir).strip():
            messagebox.showerror("缺少输出目录", "请选择输出目录。")
            return

        try:
            input_dir, files = self._collect_audio_files()
        except ValueError as exc:
            messagebox.showerror("无法开始转写", str(exc))
            return
        self._refresh_preview_list(input_dir, files)
        if not files:
            messagebox.showwarning("没有可处理文件", "输入目录中没有找到支持的音频文件。")
            return

        save_config(self.config_path, namespace_to_config(args))
        self.log_text.delete("1.0", "end")
        self._append_log(f"准备转写：共 {len(files)} 个音频文件。")
        self.status_var.set("正在运行...")
        self.summary_var.set("成功 0 | 跳过 0 | 失败 0")
        self.progress_var.set(0)
        self._set_running(True)

        def worker() -> None:
            try:
                result = run_batch_transcription(
                    args,
                    log_fn=lambda message: self.queue.put(("log", message)),
                    progress_fn=lambda index, total, path: self.queue.put(
                        ("progress", (index, total, path.name))
                    ),
                )
                self.queue.put(("done", result))
            except Exception as exc:  # noqa: BLE001
                self.queue.put(("error", str(exc)))

        self.worker = threading.Thread(target=worker, daemon=True)
        self.worker.start()

    def _open_output_dir(self) -> None:
        output_dir = Path(self.output_dir_var.get().strip())
        output_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(output_dir.resolve())  # type: ignore[attr-defined]

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "log":
                    self._append_log(str(payload))
                elif kind == "status":
                    self.status_var.set(str(payload))
                elif kind == "progress":
                    index, total, file_name = payload
                    self.status_var.set(f"处理中 {index}/{total}")
                    self.progress_var.set((index - 1) / total * 100 if total else 0)
                elif kind == "done":
                    result = payload
                    self.status_var.set("已完成")
                    self.summary_var.set(
                        f"成功 {result.success_count} | 跳过 {result.skipped_count} | "
                        f"失败 {result.failed_count}"
                    )
                    self.preview_var.set(f"{result.total} 个文件")
                    self.progress_var.set(100 if result.total else 0)
                    self._set_running(False)
                    if result.failed_count:
                        messagebox.showwarning(
                            "部分文件失败",
                            "部分文件转写失败，请查看日志面板了解详情。",
                        )
                    else:
                        messagebox.showinfo("完成", "批量转写已完成。")
                elif kind == "error":
                    self.status_var.set("运行失败")
                    self._append_log(f"ERROR: {payload}")
                    self._set_running(False)
                    messagebox.showerror("转写失败", str(payload))
        except queue.Empty:
            pass
        self.root.after(120, self._poll_queue)


def main() -> int:
    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
