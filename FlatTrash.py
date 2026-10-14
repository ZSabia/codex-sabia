#!/usr/bin/env python3

import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
from pathlib import Path
import shutil

def run_cmd(args):
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def get_flatpaks():
    output = run_cmd(["flatpak", "list", "--app", "--columns=application,size"])
    apps = []
    # Captured output has no header; do not drop the first application.
    for line in output.splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2:
            apps.append(tuple(parts))
    return apps


def get_big_dirs():
    result = subprocess.run(["du", "-h", "--max-depth=1", str(Path.home())],
                            capture_output=True, text=True)
    if result.returncode:
        return result.stdout + "\nNão consegui consultar todos os diretórios:\n" + result.stderr
    sorted_output = subprocess.run(["sort", "-hr"], input=result.stdout,
                                   capture_output=True, text=True, check=True)
    return "\n".join(sorted_output.stdout.splitlines()[:10])


def uninstall_flatpak(app_id):
    if not messagebox.askyesno("Confirmar", f"Deseja remover {app_id}?"):
        return
    try:
        run_cmd(["flatpak", "uninstall", "-y", app_id])
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", None) or str(exc)
        messagebox.showerror("Erro", f"Não consegui remover {app_id}:\n{detail}")
        return
    messagebox.showinfo("Sucesso", f"{app_id} removido.")
    refresh_app_list()


def clean_trash_and_cache():
    roots = [Path.home() / ".cache", Path.home() / ".local/share/Trash"]
    if not messagebox.askyesno("Confirmar limpeza",
                              "Apagar o conteúdo do cache e da lixeira?\n"
                              "Esta ação não pode ser desfeita. Feche os aplicativos antes de continuar."):
        return
    try:
        for root in roots:
            if root.is_symlink():
                raise OSError(f"Pasta é um link simbólico: {root}")
            if not root.exists():
                continue
            for item in root.iterdir():
                if item.is_symlink() or not item.is_dir():
                    item.unlink()
                else:
                    shutil.rmtree(item)
    except OSError as exc:
        messagebox.showerror("Limpeza incompleta", str(exc))
        return
    messagebox.showinfo("Limpeza", "Cache e lixeira limpos!")

# Atualiza a lista de flatpaks
def refresh_app_list():
    for widget in frame_apps.winfo_children():
        widget.destroy()
    try:
        apps = get_flatpaks()
    except (OSError, subprocess.CalledProcessError) as exc:
        messagebox.showerror("Erro", getattr(exc, "stderr", None) or str(exc))
        return
    for app_id, size in apps:
        app_frame = tk.Frame(frame_apps)
        app_frame.pack(fill="x", pady=2)
        label = tk.Label(app_frame, text=f"{app_id} ({size})", anchor="w")
        label.pack(side="left", fill="x", expand=True)
        btn = tk.Button(app_frame, text="Remover", command=lambda i=app_id: uninstall_flatpak(i))
        btn.pack(side="right")

def main():
    global root, frame_apps
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


if __name__ == "__main__":
    main()
