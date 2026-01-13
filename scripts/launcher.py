import logging
import math
import os
import signal
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from tkinterdnd2 import DND_FILES, DND_TEXT, TkinterDnD

from crimereporter.sources.source import Source
from crimereporter.utils.config import Config
from crimereporter.utils.directories import Directories
from crimereporter.utils.log_maintenance import GlobalScriptLogger

config = Config()  # Load your YAML configuration
global_logger = GlobalScriptLogger()
PROJECT_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)


class ScriptRunner:
    def __init__(self, root):
        self.root = root
        self.root.title("Script Runner")
        self.root.geometry(config.launcher.geometry)

        self.current_process = None
        self.source_choice = None
        self.program_choice = None
        self.id_entry = None
        self.url_entry = None
        self.output_box = None

        self.gui_logger = global_logger.get_logger()
        self.gui_logger.info("ScriptRunner initialized")

        # --- GUI Setup ---
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=5, fill=tk.X)

        self.create_program_dropdown(top_frame)
        self.create_source_dropdown(top_frame)
        self.create_id_input(top_frame)
        self.create_url_input()
        self.create_buttons()
        self.create_output_box()

    # ----------------- Active Program Dropdown / Number -----------------
    def create_program_dropdown(self, frame):
        tk.Label(frame, text="Program:").pack(side="left", padx=5)

        options = ["0"] + Directories.get_active_programs()

        self.program_choice = ttk.Combobox(frame, values=options, width=10)
        self.program_choice.pack(side="left", padx=5)
        if options:
            self.program_choice.set(options[-1])

        self.program_choice.config(validate="key", validatecommand=(self.root.register(self.validate_number), "%P"))

    @staticmethod
    def validate_number(value):
        return value == "" or value.isdigit()

    # ----------------- Source Dropdown -----------------
    def create_source_dropdown(self, frame):
        tk.Label(frame, text="Source:").pack(side="left", padx=5)
        self.source_choice = ttk.Combobox(frame, values=Source.shortnames(), state="readonly", width=15)
        self.source_choice.current(0)
        self.source_choice.pack(side="left", padx=5)

    # ----------------- Text Entry -----------------
    def create_id_input(self, frame):
        tk.Label(frame, text="Id:").pack(side="left", padx=5)
        self.id_entry = tk.Entry(frame, width=15)
        self.id_entry.pack(side="left", padx=5)

    def create_url_input(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=5, fill=tk.X)

        tk.Label(frame, text="URL:").pack(side=tk.LEFT, padx=5)
        self.url_entry = tk.Entry(frame, width=80)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.url_entry.drop_target_register(DND_TEXT, DND_FILES)
        self.url_entry.dnd_bind("<<Drop>>", self.handle_url_drop)

    def handle_url_drop(self, event):
        dropped = event.data.strip()
        if dropped.startswith("{") and dropped.endswith("}"):
            dropped = dropped[1:-1]
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, dropped)

    def create_buttons(self, columns=4):
        frame = tk.Frame(self.root)
        frame.pack(pady=10, fill=tk.X)

        for idx, cmd in enumerate(config.Commands):
            row = idx // columns
            col = idx % columns
            btn = tk.Button(frame, text=cmd["name"], command=lambda c=cmd: self.run_script(c))
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

        stop_row = math.ceil(len(config.Commands) / columns)
        stop_btn = tk.Button(frame, text="Stop", fg="red", command=self.stop_script)
        stop_btn.grid(row=stop_row, column=0, columnspan=columns, padx=5, pady=5, sticky="ew")

        for i in range(columns):
            frame.grid_columnconfigure(i, weight=1)

    def create_output_box(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.output_box = tk.Text(frame, height=25, width=120, yscrollcommand=scrollbar.set)
        self.output_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.output_box.yview)

        self.output_box.tag_configure("stdout", foreground="black")
        self.output_box.tag_configure("stderr", foreground="red")

    # ----------------- Script Execution -----------------
    def run_script(self, command_dict):
        """Run a script in a separate thread and display output."""
        if self.current_process:
            self.append_output("[Another process is already running]\n", "stderr")
            return

        cmd_str = command_dict["command"]

        # Build formatting arguments
        program_val = self.program_choice.get() if self.program_choice else ""
        format_args = {
            "source": self.source_choice.get() if self.source_choice else "",
            "identifier": self.id_entry.get() if self.id_entry else "",
            "program": program_val if program_val else "0",  # Pass 0 if blank
        }

        # Format the command string
        cmd_str = cmd_str.format(**format_args).strip()

        # Show the command in the output box
        self.output_box.config(state=tk.NORMAL)
        self.output_box.delete("1.0", tk.END)
        self.append_output(f"$ {cmd_str}\n")  # Print the command

        # Run the command in a thread
        threading.Thread(target=self.task, args=(cmd_str, command_dict.get("refresh", False)), daemon=True).start()

    def task(self, command, refresh):
        try:
            popen_args = dict(
                shell=True,
                cwd=PROJECT_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",  # 🔥 FIXES UnicodeDecodeError
                errors="replace",  # avoids crashes on edge cases
                bufsize=1,
            )

            if sys.platform == "win32":
                popen_args["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                popen_args["preexec_fn"] = os.setsid

            self.current_process = subprocess.Popen(command, **popen_args)

            threads = [
                threading.Thread(target=self.stream_output, args=(self.current_process.stdout, "stdout")),
                threading.Thread(target=self.stream_output, args=(self.current_process.stderr, "stderr")),
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.current_process.wait()
            self.append_output(f"\n[Process finished with code {self.current_process.returncode}]\n")

            if refresh:
                self.refresh_script_dropdown()

        except Exception as e:
            self.append_output(f"Error: {e}\n", "stderr")
        finally:
            self.current_process = None

    def stream_output(self, pipe, tag):
        for line in iter(pipe.readline, ""):
            self.output_box.after(0, lambda l=line: self.append_output(l, tag))
        pipe.close()

    def append_output(self, text, tag="stdout"):
        self.output_box.config(state=tk.NORMAL)
        self.output_box.insert(tk.END, text, tag)
        self.output_box.see(tk.END)
        self.output_box.config(state=tk.NORMAL)

        global_logger.append(text)

    def stop_script(self):
        if not self.current_process:
            self.append_output("[No process running]\n", "stderr")
            return
        try:
            if sys.platform == "win32":
                self.current_process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
            self.append_output("\n[Process terminated by user]\n", "stderr")
        except Exception as e:
            self.append_output(f"\n[Error terminating process: {e}]\n", "stderr")
        finally:
            self.current_process = None

    # ----------------- Refresh Script Dropdown -----------------
    def refresh_script_dropdown(self):
        options = ["0"] + Directories.get_active_programs()
        self.program_choice["values"] = options
        if options:
            self.program_choice.set(options[-1])


def main():
    Source.load_sources()
    root = TkinterDnD.Tk()
    ScriptRunner(root)
    root.mainloop()


if __name__ == "__main__":
    main()
