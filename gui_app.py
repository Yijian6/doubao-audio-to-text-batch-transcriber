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
    load_config,
    namespace_to_config,
    run_batch_transcription,
    save_config,
)


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("豆包音频转文字批量工具")
        self.root.geometry("980x760")
        self.root.minsize(900, 680)
        self.root.configure(bg="#f5f5f3")

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

        self._build_ui()
        self._load_config_into_form()
        self.root.after(120, self._poll_queue)

    def _configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        bg = "#f5f5f3"
        panel = "#fbfbfa"
        border = "#dad7d2"
        text = "#1d1d1b"
        muted = "#6f6a63"
        accent = "#111111"

        style.configure(".", background=bg, foreground=text)
        style.configure("TFrame", background=bg)
        style.configure("Panel.TFrame", background=panel, borderwidth=1, relief="solid")
        style.configure("TLabel", background=bg, foreground=text, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=bg, foreground=text, font=("Segoe UI", 20, "bold"))
        style.configure("Subtle.TLabel", background=bg, foreground=muted, font=("Segoe UI", 10))
        style.configure("PanelTitle.TLabel", background=panel, foreground=text, font=("Segoe UI", 11, "bold"))
        style.configure("PanelBody.TLabel", background=panel, foreground=muted, font=("Segoe UI", 9))
        style.configure("Value.TLabel", background=panel, foreground=text, font=("Segoe UI", 10, "bold"))
        style.configure("TEntry", fieldbackground="#ffffff", bordercolor=border, lightcolor=border, darkcolor=border)
        style.configure("TSpinbox", fieldbackground="#ffffff", bordercolor=border, lightcolor=border, darkcolor=border)
        style.configure("TCheckbutton", background=bg, foreground=text, font=("Segoe UI", 10))
        style.configure("TButton", padding=(12, 8), font=("Segoe UI", 10))
        style.configure("Primary.TButton", background=accent, foreground="#ffffff", borderwidth=0, padding=(14, 9))
        style.map(
            "Primary.TButton",
            background=[("active", "#222222"), ("disabled", "#bdb7af")],
            foreground=[("disabled", "#f1efeb")],
        )
        style.configure("Quiet.TButton", background=panel, foreground=text, bordercolor=border, lightcolor=border, darkcolor=border)
        style.map("Quiet.TButton", background=[("active", "#f0efec")])
        style.configure("TSeparator", background=border)

    def _build_ui(self) -> None:
        self._configure_style()
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=1)

        header = ttk.Frame(self.root, padding=(24, 24, 24, 10))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="豆包音频转文字批量工具",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="填写 Key，选择目录，然后开始批量转写。",
            style="Subtle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        form = ttk.Frame(self.root, style="Panel.TFrame", padding=18)
        form.grid(row=1, column=0, sticky="ew", padx=24)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="基础配置", style="PanelTitle.TLabel").grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(form, text="本地目录和 API Key 会保存到 config.json。", style="PanelBody.TLabel").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(2, 12)
        )

        ttk.Label(form, text="API Key").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(form, textvariable=self.api_key_var, show="*").grid(
            row=2,
            column=1,
            sticky="ew",
            pady=6,
        )

        ttk.Label(form, text="输入目录").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(form, textvariable=self.input_dir_var).grid(
            row=3,
            column=1,
            sticky="ew",
            pady=6,
        )
        ttk.Button(form, text="选择", command=self._choose_input_dir, style="Quiet.TButton").grid(
            row=3,
            column=2,
            padx=(8, 0),
            pady=6,
        )

        ttk.Label(form, text="输出目录").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Entry(form, textvariable=self.output_dir_var).grid(
            row=4,
            column=1,
            sticky="ew",
            pady=6,
        )
        ttk.Button(form, text="选择", command=self._choose_output_dir, style="Quiet.TButton").grid(
            row=4,
            column=2,
            padx=(8, 0),
            pady=6,
        )

        options = ttk.Frame(self.root, padding=(24, 14, 24, 10))
        options.grid(row=2, column=0, sticky="ew")
        options.columnconfigure(0, weight=1)
        options.columnconfigure(1, weight=1)
        options.columnconfigure(2, weight=1)
        options.columnconfigure(3, weight=1)

        ttk.Checkbutton(options, text="递归扫描", variable=self.recursive_var).grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Checkbutton(options, text="覆盖已有结果", variable=self.overwrite_var).grid(
            row=0,
            column=1,
            sticky="w",
        )
        ttk.Checkbutton(options, text="保存 JSON", variable=self.save_json_var).grid(
            row=0,
            column=2,
            sticky="w",
        )
        retries_group = ttk.Frame(options)
        retries_group.grid(row=0, column=3, sticky="e")
        ttk.Label(retries_group, text="重试次数").pack(side="left", padx=(0, 6))
        ttk.Spinbox(
            retries_group,
            from_=0,
            to=10,
            width=5,
            textvariable=self.retries_var,
        ).pack(side="left")

        status_row = ttk.Frame(self.root, padding=(24, 0, 24, 12))
        status_row.grid(row=3, column=0, sticky="ew")
        status_row.columnconfigure(0, weight=1)
        status_row.columnconfigure(1, weight=1)
        status_row.columnconfigure(2, weight=1)
        status_row.columnconfigure(3, weight=1)

        self._build_metric_card(status_row, 0, "状态", self.status_var)
        self._build_metric_card(status_row, 1, "统计", self.summary_var)

        action_card = ttk.Frame(status_row, style="Panel.TFrame", padding=12)
        action_card.grid(row=0, column=2, columnspan=2, sticky="nsew", padx=(12, 0))
        action_card.columnconfigure(0, weight=1)
        button_bar = ttk.Frame(action_card, style="Panel.TFrame")
        button_bar.grid(row=0, column=0, sticky="e")
        self.save_button = ttk.Button(button_bar, text="保存配置", command=self._save_config, style="Quiet.TButton")
        self.save_button.pack(side="left", padx=(0, 8))
        self.open_button = ttk.Button(
            button_bar,
            text="打开输出目录",
            command=self._open_output_dir,
            style="Quiet.TButton",
        )
        self.open_button.pack(side="left", padx=(0, 8))
        self.start_button = ttk.Button(
            button_bar,
            text="开始转写",
            command=self._start_transcription,
            style="Primary.TButton",
        )
        self.start_button.pack(side="left")

        controls = ttk.Frame(self.root, padding=(24, 0, 24, 18))
        controls.grid(row=4, column=0, sticky="nsew")
        controls.columnconfigure(0, weight=1)
        controls.rowconfigure(1, weight=1)

        ttk.Label(controls, text="运行日志", style="Subtle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        log_frame = ttk.Frame(controls, style="Panel.TFrame", padding=8)
        log_frame.grid(row=1, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_frame,
            wrap="word",
            font=("Consolas", 10),
            height=18,
            bd=0,
            relief="flat",
            bg="#ffffff",
            fg="#1d1d1b",
            insertbackground="#1d1d1b",
            padx=12,
            pady=12,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _build_metric_card(self, parent: ttk.Frame, column: int, title: str, variable: tk.StringVar) -> None:
        card = ttk.Frame(parent, style="Panel.TFrame", padding=12)
        card.grid(row=0, column=column, sticky="nsew")
        ttk.Label(card, text=title, style="PanelBody.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(card, textvariable=variable, style="Value.TLabel").grid(row=1, column=0, sticky="w", pady=(6, 0))

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

    def _append_log(self, message: str) -> None:
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

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

        save_config(self.config_path, namespace_to_config(args))
        self.log_text.delete("1.0", "end")
        self.status_var.set("正在运行...")
        self.summary_var.set("成功 0 | 跳过 0 | 失败 0")
        self._set_running(True)

        def worker() -> None:
            try:
                result = run_batch_transcription(
                    args,
                    log_fn=lambda message: self.queue.put(("log", message)),
                    progress_fn=lambda index, total, path: self.queue.put(
                        ("status", f"正在处理 {index}/{total}：{path.name}")
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
                elif kind == "done":
                    result = payload
                    self.status_var.set("已完成")
                    self.summary_var.set(
                        f"成功 {result.success_count} | 跳过 {result.skipped_count} | "
                        f"失败 {result.failed_count}"
                    )
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
