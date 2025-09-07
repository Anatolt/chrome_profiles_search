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
from tkinter import messagebox, simpledialog
from tkinter import ttk

NOTES_FILE = os.path.join(os.path.dirname(__file__), "profile_notes.json")


def load_notes():
    if os.path.isfile(NOTES_FILE):
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_notes(notes):
    try:
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def save_profiles_to_cloud(profiles):
    cloud_file = os.path.join(os.path.dirname(__file__), "profiles_cloud.json")
    try:
        with open(cloud_file, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

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

def load_profiles(notes):
    user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    local_state = os.path.join(user_data_dir, "Local State")
    if not os.path.isfile(local_state):
        return [], user_data_dir, local_state

    try:
        with open(local_state, "r", encoding="utf-8") as f:
            data = json.load(f)
        info_cache = data.get("profile", {}).get("info_cache", {})
        items = []
        for profile_dir, info in info_cache.items():
            name = info.get("name") or profile_dir
            email = info.get("user_name", "")
            last_used = int(info.get("last_used", 0))
            note = notes.get(profile_dir, "")
            if name.strip():
                items.append({
                    "name": name,
                    "dir": profile_dir,
                    "email": email,
                    "note": note,
                    "last_used": last_used,
                })
        items.sort(key=lambda x: x["last_used"], reverse=True)
        return items, user_data_dir, local_state
    except Exception as e:
        messagebox.showerror("Ошибка чтения профилей", f"Не удалось прочитать Local State.\n{e}")
        return [], user_data_dir, local_state


class LauncherUI(tk.Tk):
    def __init__(self, chrome_path, profiles, notes, local_state):
        super().__init__()
        self.title("Chrome Profile Launcher")
        self.geometry("700x420")
        self.minsize(520, 320)

        self.chrome_path = chrome_path
        self.profiles = profiles[:]
        self.filtered = self.profiles[:]
        self.notes = notes
        self.local_state = local_state

        self.search_var = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.search_var, font=("Segoe UI", 12))
        self.entry.pack(fill=tk.X, padx=10, pady=(12, 6))
        self.entry.focus_set()

        self.tree = ttk.Treeview(self, columns=("email", "dir", "note"), show="tree headings")
        self.tree.heading("#0", text="Имя")
        self.tree.heading("email", text="Email")
        self.tree.heading("dir", text="Каталог")
        self.tree.heading("note", text="Примечание")
        self.tree.column("email", width=160)
        self.tree.column("dir", width=160)
        self.tree.column("note", width=200)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.status = tk.Label(self, anchor="w")
        self.status.pack(fill=tk.X, padx=10, pady=(0,10))

        self.entry.bind("<KeyRelease>", self.on_search_changed)
        self.entry.bind("<Down>", self.on_focus_list)
        self.tree.bind("<Return>", self.launch_selected)
        self.tree.bind("<Double-Button-1>", self.launch_selected)
        self.tree.bind("<F2>", self.rename_selected)
        self.tree.bind("<Control-n>", self.edit_note)
        self.tree.bind("<Escape>", lambda e: self.destroy())
        self.entry.bind("<Escape>", lambda e: self.destroy())

        self.refresh_tree()

    def on_focus_list(self, event):
        children = self.tree.get_children()
        if children:
            self.tree.focus(children[0])
            self.tree.selection_set(children[0])

    def on_search_changed(self, event=None):
        q = self.search_var.get().strip().lower()
        if not q:
            self.filtered = self.profiles[:]
        else:
            self.filtered = [
                p for p in self.profiles
                if q in p["name"].lower() or q in p["email"].lower() or q in p["dir"].lower() or q in p["note"].lower()
            ]
        self.refresh_tree()

    def refresh_tree(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for p in self.filtered:
            self.tree.insert("", tk.END, iid=p["dir"], text=p["name"], values=(p["email"], p["dir"], p["note"]))
        self.status.config(text=f"Профилей: {len(self.profiles)} | Отфильтровано: {len(self.filtered)}")

    def get_selected_profile(self):
        sel = self.tree.selection()
        if not sel:
            return None
        pid = sel[0]
        for p in self.filtered:
            if p["dir"] == pid:
                return p
        return None

    def launch_selected(self, event=None):
        profile = self.get_selected_profile()
        if not profile:
            if len(self.filtered) == 1:
                profile = self.filtered[0]
            else:
                return
        try:
            subprocess.Popen([self.chrome_path, f"--profile-directory={profile['dir']}"] , close_fds=True)
        except Exception as e:
            messagebox.showerror("Ошибка запуска", f"Не удалось запустить Chrome.\n{e}")
            return
        self.destroy()

    def rename_selected(self, event=None):
        profile = self.get_selected_profile()
        if not profile:
            return
        new_name = simpledialog.askstring("Переименовать профиль", "Новое имя:", initialvalue=profile["name"])
        if not new_name:
            return
        profile["name"] = new_name.strip()
        try:
            with open(self.local_state, "r", encoding="utf-8") as f:
                data = json.load(f)
            info_cache = data.get("profile", {}).get("info_cache", {})
            if profile["dir"] in info_cache:
                info_cache[profile["dir"]]["name"] = profile["name"]
                with open(self.local_state, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Переименование", f"Не удалось переименовать профиль.\n{e}")
        self.refresh_tree()

    def edit_note(self, event=None):
        profile = self.get_selected_profile()
        if not profile:
            return
        new_note = simpledialog.askstring("Примечание", "Введите примечание:", initialvalue=profile["note"])
        if new_note is None:
            return
        profile["note"] = new_note
        self.notes[profile["dir"]] = new_note
        self.refresh_tree()


def main():
    chrome_path = find_chrome_executable()
    if not chrome_path:
        messagebox.showerror("Chrome не найден", "Не удалось найти chrome.exe в стандартных местах и PATH.")
        return

    notes = load_notes()
    profiles, user_data_dir, local_state = load_profiles(notes)
    if not profiles:
        messagebox.showerror(
            "Профили не найдены",
            f"Не нашёл профили в:\n{user_data_dir}\n\nУбедитесь, что Chrome установлен и у вас есть хотя бы один профиль."
        )
        return

    app = LauncherUI(chrome_path, profiles, notes, local_state)
    app.mainloop()
    save_notes(notes)
    save_profiles_to_cloud(profiles)


if __name__ == "__main__":
    main()

