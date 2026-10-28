"""Layout Fixer desktop UI. Run: python app.py"""
import sys
import time
import tkinter as tk
from tkinter import ttk
from converter import convert


class App:
    def __init__(self, root):
        self.root = root
        self.api = None
        self.busy = False
        self.job = None
        self.hotkey_id = None
        root.title("Layout Fixer — исправление раскладки")
        root.geometry("780x680")
        root.minsize(740, 640)
        self.direction = tk.StringVar(value="Автоматически")
        self.key = tk.StringVar(value="Ctrl+Alt+F8")
        self.status = tk.StringVar(value="Вставьте текст или используйте горячую клавишу.")
        frame = ttk.Frame(root, padding=22)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Ошиблись раскладкой?", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(frame, text="ghbdtn → привет     •     руддщ → hello", font=("Segoe UI", 12)).pack(anchor="w", pady=(4, 14))
        options = ttk.Frame(frame)
        options.pack(fill="x")
        ttk.Label(options, text="Направление:").pack(side="left")
        ttk.Combobox(options, textvariable=self.direction, state="readonly", width=20,
                     values=("Автоматически", "Английская → русская", "Русская → английская")).pack(side="left", padx=8)
        ttk.Label(frame, text="Текст для исправления:").pack(anchor="w", pady=(16, 5))
        self.editor = tk.Text(frame, wrap="word", undo=True, font=("Segoe UI", 13), height=8)
        self.editor.pack(fill="both", expand=True)
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=10)
        ttk.Button(buttons, text="Заменить", command=self.local_replace).pack(side="left")
        ttk.Button(buttons, text="Копировать результат", command=self.copy).pack(side="left", padx=8)
        ttk.Button(buttons, text="Отменить", command=self.undo).pack(side="left")
        settings = ttk.Frame(frame)
        settings.pack(fill="x", pady=5)
        ttk.Label(settings, text="Горячая клавиша:").pack(side="left")
        combo = ttk.Combobox(settings, textvariable=self.key, state="readonly", width=17,
                             values=("Ctrl+Alt+F8", "Ctrl+Alt+F9", "Ctrl+Alt+F10"))
        combo.pack(side="left", padx=8)
        combo.bind("<<ComboboxSelected>>", lambda event: self.register_hotkey())
        ttk.Button(frame, text="Заменить в другом окне через 3 секунды", command=self.countdown).pack(anchor="w", pady=5)
        ttk.Label(frame, text="Выделите текст в другой программе и нажмите горячую клавишу.\n"
                  "Для кнопки с таймером: нажмите её, затем за 3 секунды перейдите к выделенному тексту.",
                  wraplength=690).pack(anchor="w", pady=5)
        ttk.Label(frame, textvariable=self.status, wraplength=690, foreground="#24568a").pack(anchor="w", pady=8)
        root.protocol("WM_DELETE_WINDOW", self.close)
        if sys.platform == "win32":
            import windows_api
            self.api = windows_api
            self.hotkeys = windows_api.HotkeyService()
            self.register_hotkey()
            self.poll()
        else:
            self.status.set("В этой ОС доступен редактор. Глобальная замена требует Windows.")

    def mode(self):
        return {"Автоматически": "auto", "Английская → русская": "en_ru",
                "Русская → английская": "ru_en"}[self.direction.get()]

    def local_replace(self):
        try:
            start, end = self.editor.index("sel.first"), self.editor.index("sel.last")
        except tk.TclError:
            start, end = "1.0", "end-1c"
        old = self.editor.get(start, end)
        result = convert(old, self.mode())
        if result != old:
            self.editor.edit_separator()
            self.editor.delete(start, end)
            self.editor.insert(start, result)
            self.editor.edit_separator()
        self.status.set("Готово. Для отмены нажмите «Отменить».")

    def copy(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.editor.get("1.0", "end-1c"))
        self.status.set("Результат скопирован.")

    def undo(self):
        try:
            self.editor.edit_undo()
        except tk.TclError:
            self.status.set("Нет изменений для отмены.")

    def register_hotkey(self):
        if not self.api:
            return
        new_id = 2 if self.hotkey_id == 1 else 1
        vk = {"Ctrl+Alt+F8": 0x77, "Ctrl+Alt+F9": 0x78, "Ctrl+Alt+F10": 0x79}[self.key.get()]
        if self.hotkeys.register(new_id, 0x4003, vk):
            if self.hotkey_id:
                self.hotkeys.unregister(self.hotkey_id)
            self.hotkey_id = new_id
            self.active_key = self.key.get()
            self.status.set(f"Готово: {self.active_key}. Окно можно свернуть.")
        else:
            if self.hotkey_id:
                self.key.set(self.active_key)
            self.status.set("Сочетание занято. Выберите другую горячую клавишу.")

    def poll(self):
        for key_id in self.hotkeys.hotkeys():
            if key_id == self.hotkey_id and not self.busy:
                if self.api.foreground() == self.api.ancestor(self.root.winfo_id(), 2):
                    self.local_replace()
                else:
                    self.begin()
        self.root.after(30, self.poll)

    def countdown(self):
        if not self.api:
            self.status.set("Замена в других окнах требует Windows.")
            return
        if self.busy:
            return
        self.busy = True
        self.tick(3)

    def tick(self, remaining):
        if remaining:
            self.status.set(f"Перейдите в нужное окно и выделите текст: {remaining}…")
            self.job = self.root.after(1000, lambda: self.tick(remaining - 1))
        else:
            self.busy = False
            self.begin()

    def begin(self):
        if self.busy:
            return
        self.busy = True
        self.target = self.api.foreground()
        if self.target == self.api.ancestor(self.root.winfo_id(), 2):
            self.finish("Для замены здесь используйте кнопку «Заменить» под текстом.")
            return
        self.deadline = time.monotonic() + 2
        self.wait_release()

    def finish(self, text):
        self.busy = False
        self.status.set(text)

    def wait_release(self):
        if self.api.foreground() != self.target:
            self.finish("Замена отменена: активное окно изменилось.")
        elif self.api.modifiers_down():
            if time.monotonic() > self.deadline:
                self.finish("Отпустите Ctrl, Alt, Shift и повторите замену.")
            else:
                self.job = self.root.after(30, self.wait_release)
        else:
            try:
                self.before = self.api.sequence()
                self.api.shortcut("c")
                self.deadline = time.monotonic() + 1.5
                self.job = self.root.after(50, self.wait_copy)
            except OSError as error:
                self.finish(str(error))

    def wait_copy(self):
        if self.api.foreground() != self.target:
            self.finish("Замена отменена: активное окно изменилось.")
            return
        if self.api.sequence() == self.before:
            if time.monotonic() < self.deadline:
                self.job = self.root.after(40, self.wait_copy)
            else:
                self.finish("Текст не скопирован. Выделите его и повторите замену.")
            return
        try:
            source = self.api.read_clipboard(self.root.winfo_id())
            if not source:
                self.finish("В выделении нет обычного текста.")
                return
            result = convert(source, self.mode())
            if result == source:
                self.finish("В выделенном тексте нечего менять.")
                return
            if self.api.modifiers_down() or self.api.foreground() != self.target:
                self.finish("Замена отменена: нажаты клавиши или изменилось окно.")
                return
            self.api.write_clipboard(self.root.winfo_id(), result)
            self.api.shortcut("v")
            self.finish("Команда вставки отправлена. Результат также в буфере. Отмена в редакторе: Ctrl+Z.")
        except (OSError, MemoryError) as error:
            self.finish(str(error))

    def close(self):
        if self.api and self.hotkey_id:
            self.hotkeys.unregister(self.hotkey_id)
        if self.api:
            self.hotkeys.close()
        if self.job:
            self.root.after_cancel(self.job)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
