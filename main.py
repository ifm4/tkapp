import tkinter as tk
from pathlib import Path
from random import shuffle
from tkinter import messagebox as msg
from tkinter import ttk

import psycopg

DB = "postgresql://postgres:postgres@127.0.0.1:5432/users"
IMG = Path(__file__).with_name("img")
SCALE = 3
MAX_ATTEMPTS = 3
MSG_LOGIN = {
    "Empty": lambda: msg.showwarning("Внимание", "Введите логин и пароль!"),
    "Wrong": lambda: msg.showerror("Ошибка входа", "Проверьте логин/пароль/паззл!"),
    "Block": lambda: msg.showwarning("Внимание", "Учетная запись заблокирована!"),
}
MSG_ADMIN = {
    "Empty": lambda: msg.showwarning("Внимание", "Введите логин и пароль!"),
    "EmptyUsername": lambda: msg.showwarning("Внимание", "Пустое имя пользователя!"),
    "NotSelected": lambda: msg.showwarning("Внимание", "Выберите пользователя из списка!"),
    "AlreadyExists": lambda: msg.showerror("Ошибка", "Пользователь уже существует!"),
}


def db(query, params=()):
    with psycopg.connect(DB) as c:
        result = c.execute(query, params)
        return result.fetchall() if result.description else []


def pack(widget, **options):
    widget.pack(**options)
    return widget


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.resizable(False,False)
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.order = [0,1,2,3]
        self.images = [tk.PhotoImage(file=IMG/f"{i}.png").subsample(SCALE) for i in range(4)]
        self.login_page()

    def run(self):
        self.root.mainloop()

    def clear(self):
        self.username.set("")
        self.password.set("")
        for widget in self.root.winfo_children():
            widget.destroy()

    def login_page(self):
        self.clear()
        self.root.title("Авторизация")

        box = pack(ttk.Frame(self.root), padx=12, pady=12)
        ttk.Label(box, text="Пользователь:").grid(row=0, column=0, sticky="e")
        ttk.Entry(box, textvariable=self.username).grid(row=0, column=1, sticky="w")
        ttk.Label(box, text="Пароль:").grid(row=1, column=0, sticky="e")
        ttk.Entry(box, textvariable=self.password, show="\u2022").grid(row=1, column=1, sticky="w")

        box = pack(ttk.Labelframe(self.root, text="Соберите паззл:"), padx=12, pady=12)
        self.tiles = []
        for pos in range(4):
            tile = ttk.Button(box, command=lambda p=pos: self.swap(p))
            tile.grid(row=pos // 2, column=pos % 2)
            self.tiles.append(tile)
        self.reset_puzzle()

        box = pack(ttk.Frame(self.root), padx=12, pady=12)
        pack(ttk.Button(box, text="Сброс", command=self.reset_puzzle), side="left")
        pack(ttk.Button(box, text="Войти", command=self.login), side="left")

    def swap(self, pos):
        if self.first is None:
            self.first = pos
            self.tiles[pos].state(["disabled"])
            return
        first = self.first
        self.order[first], self.order[pos] = self.order[pos], self.order[first]
        self.sync_puzzle()

    def reset_puzzle(self):
        order = [0, 1, 2, 3]
        while order == [0, 1, 2, 3] or order == self.order:
            shuffle(order)
        self.order = order
        self.sync_puzzle()

    def sync_puzzle(self):
        self.first = None
        for pos, tile in enumerate(self.tiles):
            tile.config(image=self.images[self.order[pos]])
            tile.state(["!disabled"])

    def login(self):
        username = self.username.get().strip()
        password = self.password.get()
        if not username or not password:
            return MSG_LOGIN["Empty"]()

        users = db("SELECT id, password, is_admin, attempts FROM users WHERE username = %s", (username,))
        if not users:
            return MSG_LOGIN["Wrong"]()

        uid, saved, is_admin, attempts = users[0]
        if attempts >= MAX_ATTEMPTS:
            return MSG_LOGIN["Block"]()

        if password != saved or self.order != [0, 1, 2, 3]:
            attempts += 1
            db("UPDATE users SET attempts = %s WHERE id = %s", (attempts, uid))
            MSG_LOGIN["Wrong"]()
            self.reset_puzzle()
            return

        db("UPDATE users SET attempts = 0 WHERE id = %s", (uid,))
        self.main_page(is_admin, self.username.get())

    def load_users(self):
        self.tree.delete(*self.tree.get_children())
        users = db("SELECT * FROM users ORDER BY username")
        for uid, username, _, is_admin, attempts in users:
            self.tree.insert(
                "",
                tk.END,
                iid=uid,
                values=(
                    username,
                    "АДМИН" if is_admin else "ПОЛЬЗОВАТЕЛЬ",
                    "ЗАБЛОКИРОВАН" if attempts >= MAX_ATTEMPTS else "АКТИВЕН",
                ),
            )

    def select(self, _):
        selected = self.tree.selection()
        if selected:
            self.username.set(self.tree.item(selected[0], "values")[0])
            self.password.set("")

    def add_user(self):
        username = self.username.get().strip()
        password = self.password.get()
        if not username or not password:
            return MSG_ADMIN["Empty"]()

        try:
            db("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        except psycopg.errors.UniqueViolation:
            return MSG_ADMIN["AlreadyExists"]()
        self.load_users()

    def update_user(self):
        username = self.username.get().strip()
        password = self.password.get()
        selected = self.tree.selection()
        if not selected:
            return MSG_ADMIN["NotSelected"]()
        if not username:
            return MSG_ADMIN["EmptyUsername"]()

        try:
            db(
                "UPDATE users SET username = %s, password = COALESCE(%s, password) WHERE id = %s",
                (username, password or None, int(selected[0])),
            )
        except psycopg.errors.UniqueViolation:
            return MSG_ADMIN["AlreadyExists"]()
        self.load_users()

    def unlock_user(self):
        selected = self.tree.selection()
        if not selected:
            return MSG_ADMIN["NotSelected"]()
        db("UPDATE users SET attempts = 0 WHERE id = %s", (int(selected[0]),))
        self.load_users()

    def lock_user(self):
        selected = self.tree.selection()
        if not selected:
            return MSG_ADMIN["NotSelected"]()
        db("UPDATE users SET attempts = %s WHERE id = %s", (MAX_ATTEMPTS, int(selected[0]),))
        self.load_users()

    def main_page(self, is_admin, logged_as):
        self.clear()
        self.root.title("Главная")

        box = pack(ttk.Frame(self.root), padx=12, pady=12)
        ttk.Label(box, text=f"Текущий пользователь: {logged_as}").grid(row=0, column=0, sticky="w")
        ttk.Button(box, text="Выйти", command=self.login_page).grid(row=0, column=1, sticky="e")
        if not is_admin:
            return

        columns = "Пользователь", "Роль", "Статус"
        self.tree = pack(
            ttk.Treeview(self.root, columns=columns, show="headings"),
            fill="both",
            expand=True,
            padx=12,
            pady=12,
        )
        for column in columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=120)
        self.tree.bind("<<TreeviewSelect>>", self.select)
        self.load_users()

        box = pack(ttk.LabelFrame(self.root, text="Текущий выбор:"), padx=12, pady=12)
        pack(ttk.Label(box, text="Пользователь:"), side="left")
        pack(ttk.Entry(box, textvariable=self.username), side="left")
        pack(ttk.Label(box, text="Пароль:"), side="left")
        pack(ttk.Entry(box, textvariable=self.password, show="\u2022"), side="left")

        box = pack(ttk.Frame(self.root), padx=12, pady=12)
        pack(ttk.Button(box, text="Добавить", command=self.add_user), side="left")
        pack(ttk.Button(box, text="Изменить", command=self.update_user), side="left")
        pack(ttk.Button(box, text="Разблокировать", command=self.unlock_user), side="left")
        pack(ttk.Button(box, text="Заблокировать", command=self.lock_user), side="left")


if __name__ == "__main__":
    app = App()
    app.run()
