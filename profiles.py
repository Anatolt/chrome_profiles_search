# -*- coding: utf-8 -*-
"""
ChromeProfileLauncher — быстрый поиск и запуск нужного профиля Google Chrome.
Работает на Windows. Зависимости: стандартный Python (tkinter из stdlib).

Как пользоваться:
1) Запустите файл (двойной клик или `py ChromeProfileLauncher.py`).
2) Печатайте часть названия профиля — список фильтруется.
3) Enter или двойной клик по профилю — профиль откроется в Chrome.
4) Esc — закрыть.

Подсказка: создайте ярлык на рабочем столе для быстрого вызова.
"""

import os
import json
import subprocess
import tkinter as tk
from tkinter import messagebox

def find_chrome_executable():
    # Популярные пути
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    # В PATH
    for name in ("chrome.exe", "google-chrome.exe"):
        try:
            from shutil import which
            p = which(name)
            if p:
                return p
        except Exception:
            pass
    return None

def load_profiles():
    user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    local_state = os.path.join(user_data_dir, "Local State")
    if not os.path.isfile(local_state):
        return [], user_data_dir

    try:
        with open(local_state, "r", encoding="utf-8") as f:
            data = json.load(f)
        info_cache = data.get("profile", {}).get("info_cache", {})
        items = []
        for profile_dir, info in info_cache.items():
            # Пропускаем гостевые и системные, если попадутся
            name = info.get("name") or profile_dir
            if name.strip():
                items.append((name, profile_dir))
        items.sort(key=lambda x: x[0].lower())
        return items, user_data_dir
    except Exception as e:
        messagebox.showerror("Ошибка чтения профилей", f"Не удалось прочитать Local State.\n{e}")
        return [], user_data_dir

class LauncherUI(tk.Tk):
    def __init__(self, chrome_path, profiles):
        super().__init__()
        self.title("Chrome Profile Launcher")
        self.geometry("520x420")
        self.minsize(420, 320)

        self.chrome_path = chrome_path
        self.profiles = profiles[:]
        self.filtered = self.profiles[:]

        self.search_var = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.search_var, font=("Segoe UI", 12))
        self.entry.pack(fill=tk.X, padx=10, pady=(12, 6))
        self.entry.focus_set()

        self.listbox = tk.Listbox(self, activestyle="dotbox", font=("Segoe UI", 11))
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.status = tk.Label(self, anchor="w")
        self.status.pack(fill=tk.X, padx=10, pady=(0,10))

        self.entry.bind("<KeyRelease>", self.on_search_changed)
        self.entry.bind("<Down>", self.on_focus_list)
        self.listbox.bind("<Return>", self.launch_selected)
        self.listbox.bind("<Double-Button-1>", self.launch_selected)
        self.listbox.bind("<Escape>", lambda e: self.destroy())
        self.entry.bind("<Escape>", lambda e: self.destroy())

        self.refresh_listbox()

    def on_focus_list(self, event):
        if self.listbox.size() > 0:
            self.listbox.focus_set()
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0)
            self.listbox.activate(0)

    def on_search_changed(self, event=None):
        q = self.search_var.get().strip().lower()
        if not q:
            self.filtered = self.profiles[:]
        else:
            self.filtered = [item for item in self.profiles if q in item[0].lower()]
        self.refresh_listbox()

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for display, profile_dir in self.filtered:
            self.listbox.insert(tk.END, f"{display}    [{profile_dir}]")
        self.status.config(text=f"Профилей: {len(self.profiles)} | Отфильтровано: {len(self.filtered)}")

    def launch_selected(self, event=None):
        sel = self.listbox.curselection()
        if not sel:
            if len(self.filtered) == 1:
                display, profile_dir = self.filtered[0]
            else:
                return
        else:
            display, profile_dir = self.filtered[sel[0]]

        try:
            subprocess.Popen([self.chrome_path, f"--profile-directory={profile_dir}"], close_fds=True)
        except Exception as e:
            messagebox.showerror("Ошибка запуска", f"Не удалось запустить Chrome.\n{e}")
            return
        self.destroy()

def main():
    chrome_path = find_chrome_executable()
    if not chrome_path:
        messagebox.showerror("Chrome не найден", "Не удалось найти chrome.exe в стандартных местах и PATH.")
        return

    profiles, user_data_dir = load_profiles()
    if not profiles:
        messagebox.showerror("Профили не найдены", f"Не нашёл профили в:\n{user_data_dir}\n\nУбедитесь, что Chrome установлен и у вас есть хотя бы один профиль.")
        return

    app = LauncherUI(chrome_path, profiles)
    app.mainloop()

if __name__ == "__main__":
    main()
