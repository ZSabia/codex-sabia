#!/usr/bin/env python3

import os
import json
from tkinter import *
from tkinter import messagebox
from cryptography.fernet import Fernet

ARQUIVO_CHAVES = "chave.key"
ARQUIVO_SENHAS = "senhas.dat"

def carregar_ou_criar_chave():
    if not os.path.exists(ARQUIVO_CHAVES):
        chave = Fernet.generate_key()
        with open(ARQUIVO_CHAVES, "wb") as f:
            f.write(chave)
    else:
        with open(ARQUIVO_CHAVES, "rb") as f:
            chave = f.read()
    return Fernet(chave)

fernet = carregar_ou_criar_chave()

def salvar_senhas(senhas):
    data = json.dumps(senhas).encode()
    criptografado = fernet.encrypt(data)
    with open(ARQUIVO_SENHAS, "wb") as f:
        f.write(criptografado)

def carregar_senhas():
    if not os.path.exists(ARQUIVO_SENHAS):
        return {}
    with open(ARQUIVO_SENHAS, "rb") as f:
        criptografado = f.read()
    try:
        data = fernet.decrypt(criptografado)
        return json.loads(data.decode())
    except:
        messagebox.showerror("Erro", "Falha ao descriptografar as senhas.")
        return {}

class CofreGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cofre de Senhas - Eevee Boladão")
        self.senhas = carregar_senhas()

        self.label_site = Label(root, text="Serviço:")
        self.label_site.grid(row=0, column=0, sticky=W)
        self.entry_site = Entry(root, width=30)
        self.entry_site.grid(row=0, column=1)

        self.label_senha = Label(root, text="Senha:")
        self.label_senha.grid(row=1, column=0, sticky=W)
        self.entry_senha = Entry(root, width=30, show="*")
        self.entry_senha.grid(row=1, column=1)

        self.botao_salvar = Button(root, text="Salvar", command=self.salvar_senha)
        self.botao_salvar.grid(row=2, column=0, pady=5)

        self.botao_buscar = Button(root, text="Buscar", command=self.buscar_senha)
        self.botao_buscar.grid(row=2, column=1, pady=5)

    def salvar_senha(self):
        site = self.entry_site.get()
        senha = self.entry_senha.get()
        if site and senha:
            self.senhas[site] = senha
            salvar_senhas(self.senhas)
            messagebox.showinfo("Sucesso", f"Senha salva pra: {site}")
            self.entry_site.delete(0, END)
            self.entry_senha.delete(0, END)
        else:
            messagebox.showwarning("Aviso", "Preenche tudo aí, doido.")

    def buscar_senha(self):
        site = self.entry_site.get()
        senha = self.senhas.get(site)
        if senha:
            messagebox.showinfo("Senha encontrada", f"{site}: {senha}")
        else:
            messagebox.showwarning("Não achei", f"Nada salvo pra {site}.")

if __name__ == "__main__":
    root = Tk()
    app = CofreGUI(root)
    root.mainloop()
