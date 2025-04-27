#!/usr/bin/env python3

import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import os

# Função pra rodar comandos shell e pegar a saída
def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

# Pega flatpaks e tamanhos
def get_flatpaks():
    cmd = "flatpak list --app --columns=application,size"
    output = run_cmd(cmd)
    apps = []
    for line in output.splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) == 2:
            apps.append((parts[0], parts[1]))
    return apps

# Lista diretórios pesados no ~
def get_big_dirs():
    cmd = "du -h --max-depth=1 ~ | sort -hr | head -n 10"
    output = run_cmd(cmd)
    return output

# Função para desinstalar
def uninstall_flatpak(app_id):
    confirm = messagebox.askyesno("Confirmar", f"Deseja remover {app_id}?")
    if confirm:
        run_cmd(f"flatpak uninstall -y {app_id}")
        messagebox.showinfo("Sucesso", f"{app_id} removido.")
        refresh_app_list()

# Limpa lixeira e cache defaut
def clean_trash_and_cache():
    os.system("rm -rf ~/.cache/* ~/.local/share/Trash/*")
    messagebox.showinfo("Limpeza", "Cache e Lixeira limpos!")

# Atualiza a lista de flatpaks
def refresh_app_list():
    for widget in frame_apps.winfo_children():
        widget.destroy()
    for app_id, size in get_flatpaks():
        app_frame = tk.Frame(frame_apps)
        app_frame.pack(fill="x", pady=2)
        label = tk.Label(app_frame, text=f"{app_id} ({size})", anchor="w")
        label.pack(side="left", fill="x", expand=True)
        btn = tk.Button(app_frame, text="Remover", command=lambda i=app_id: uninstall_flatpak(i))
        btn.pack(side="right")

# GUI
root = tk.Tk()
root.title("Central de Limpeza do Sabiá")
root.geometry("600x600")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# Aba Flatpaks
tab_flatpaks = tk.Frame(notebook)
notebook.add(tab_flatpaks, text="Flatpaks")

frame_apps = tk.Frame(tab_flatpaks)
frame_apps.pack(fill="both", expand=True, padx=10, pady=10)

btn_refresh = tk.Button(tab_flatpaks, text="Atualizar Lista", command=refresh_app_list)
btn_refresh.pack(pady=5)

# Aba Diretórios pesados
tab_dirs = tk.Frame(notebook)
notebook.add(tab_dirs, text="Diretórios Pesados")

text_dirs = tk.Text(tab_dirs, height=15)
text_dirs.pack(fill="both", expand=True, padx=10, pady=10)
text_dirs.insert("1.0", get_big_dirs())
text_dirs.config(state="disabled")

# Botão de limpeza
btn_clean = tk.Button(root, text="Limpar Cache e Lixeira", bg="red", fg="white", command=clean_trash_and_cache)
btn_clean.pack(pady=10)

refresh_app_list()
root.mainloop()
