#!/usr/bin/env python3

import os
import re
import shlex
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pyperclip

ALIAS_FILE = os.path.expanduser("~/.config/fish/conf.d/aliases.fish")
EDITOR = os.getenv("EDITOR", "gedit")


def reload_terminal():
    try:
        subprocess.Popen(["gnome-terminal", "--", "fish"])
    except OSError as exc:
        messagebox.showerror("Erro", f"Não consegui abrir o terminal: {exc}")


def parse_alias(line):
    try:
        parts = shlex.split(line, comments=True)
    except ValueError:
        return None
    if not parts or parts.pop(0) != "alias":
        return None
    if parts and parts[0] == "--":
        parts.pop(0)
    if not parts or parts[0].startswith("-"):
        return None
    if "=" in parts[0]:
        name, command = parts[0].split("=", 1)
        if len(parts) != 1:
            return None
    elif len(parts) == 2:
        name, command = parts
    else:
        return None
    return (name, command) if name and command else None


def read_aliases():
    if not os.path.exists(ALIAS_FILE):
        return []
    aliases = []
    description = "Sem descrição."
    with open(ALIAS_FILE, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("#"):
                description = stripped.lstrip("# ")
                continue
            alias = parse_alias(stripped)
            if alias:
                aliases.append((*alias, description))
            description = "Sem descrição."
    return sorted(aliases, key=lambda x: x[0])


def write_alias(alias, command, description):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", alias):
        messagebox.showerror("Erro", "Use um nome sem espaços ou caracteres especiais.")
        return
    if any(c in command for c in "\r\n\0"):
        messagebox.showerror("Erro", "O comando precisa estar em uma única linha.")
        return
    os.makedirs(os.path.dirname(ALIAS_FILE), exist_ok=True)
    description = " ".join(description.splitlines())
    with open(ALIAS_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n# {description}\nalias -- {shlex.quote(alias)} {shlex.quote(command)}\n")
    reload_terminal()


def remove_alias_from_file(name):
    if not os.path.exists(ALIAS_FILE):
        return False
    with open(ALIAS_FILE, encoding="utf-8") as f:
        lines = f.readlines()
    kept = []
    removed = False
    for line in lines:
        alias = parse_alias(line.strip())
        if alias and alias[0] == name:
            if kept and kept[-1].lstrip().startswith("#"):
                kept.pop()
            removed = True
            continue
        kept.append(line)
    if removed:
        with open(ALIAS_FILE, "w", encoding="utf-8") as f:
            f.writelines(kept)
        reload_terminal()
    return removed


def add_alias():
    alias = simpledialog.askstring("Adicionar Alias", "Nome do alias:")
    if not alias:
        return
    command = simpledialog.askstring("Adicionar Alias", "Comando do alias:")
    if not command:
        return
    description = simpledialog.askstring("Adicionar Alias", "Descrição do alias:") or "Sem descrição."
    write_alias(alias, command, description)
    update_alias_list()

def remove_alias():
    selected_item = tree.focus()
    if not selected_item:
        messagebox.showerror("Erro", "Nenhum alias selecionado.")
        return
    alias = tree.item(selected_item)['values'][0]
    confirm = messagebox.askyesno("Confirmação", f"Tem certeza que deseja remover o alias '{alias}'?")
    if confirm:
        if remove_alias_from_file(alias):
            update_alias_list()
        else:
            messagebox.showerror("Erro", "Alias não encontrado.")

def edit_aliases():
    try:
        subprocess.Popen([*shlex.split(EDITOR), ALIAS_FILE])
    except (OSError, ValueError) as exc:
        messagebox.showerror("Erro", f"Não consegui abrir o editor: {exc}")

def update_alias_list():
    aliases = read_aliases()
    tree.delete(*tree.get_children())
    for name, command, description in aliases:
        tree.insert("", "end", values=(name, command, description))

def copy_alias():
    selected_item = tree.focus()
    if selected_item:
        alias = tree.item(selected_item)['values'][0]
        pyperclip.copy(alias)
        messagebox.showinfo("Copiado", "Alias copiado para a área de transferência.")

def copy_command():
    selected_item = tree.focus()
    if selected_item:
        command = tree.item(selected_item)['values'][1]
        pyperclip.copy(command)
        messagebox.showinfo("Copiado", "Comando copiado para a área de transferência.")

def show_context_menu(event):
    selected_item = tree.identify_row(event.y)
    if selected_item:
        tree.selection_set(selected_item)
        tree.focus(selected_item)
        context_menu.post(event.x_root, event.y_root)

def hide_context_menu(event=None):
    context_menu.unpost()

def create_gui():
    global tree, context_menu
    
    root = tk.Tk()
    root.title("Gerenciador de Aliases")
    root.geometry("900x500")
    root.minsize(600, 400)
    
    frame_top = ttk.Frame(root)
    frame_top.pack(pady=10)
    
    buttons = [
        ("➕ Adicionar", add_alias),
        ("❌ Remover", remove_alias),
        ("✏️ Editar", edit_aliases),
        ("🔄 Recarregar", update_alias_list),
        ("🖥️ Abrir Terminal", reload_terminal)
    ]
    
    for text, command in buttons:
        ttk.Button(frame_top, text=text, command=command).pack(side="left", padx=5)
    
    columns = ("Nome", "Comando", "Descrição")
    tree = ttk.Treeview(root, columns=columns, show="headings")
    tree.heading("Nome", text="Nome")
    tree.heading("Comando", text="Comando")
    tree.heading("Descrição", text="Descrição")
    tree.column("Nome", width=150)
    tree.column("Comando", width=400)
    tree.column("Descrição", width=250)
    
    tree.pack(fill="both", expand=True, padx=10, pady=10)
    tree.bind("<Double-1>", lambda e: copy_alias())
    tree.bind("<Button-3>", show_context_menu)
    root.bind("<Button-1>", hide_context_menu)
    
    context_menu = tk.Menu(root, tearoff=0)
    context_menu.add_command(label="Copiar Alias", command=copy_alias)
    context_menu.add_command(label="Copiar Comando", command=copy_command)
    context_menu.add_command(label="Editar", command=edit_aliases)
    context_menu.add_command(label="Remover", command=remove_alias)
    
    update_alias_list()
    root.mainloop()

if __name__ == "__main__":
    create_gui()

