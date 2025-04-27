#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SchedulerApp:
    TEMAS = {
        "light_soft": {
            "bg": "#F4F4F4", "fg": "#333333", "btn_bg": "#D1D1D1", "entry_bg": "#FFFFFF",
            "btn_active_bg": "#C5C5C5", "btn_active_fg": "#000000"
        },
        "dark_soft": {
            "bg": "#2E2E2E", "fg": "#DCDCDC", "btn_bg": "#444", "entry_bg": "#3C3C3C",
            "btn_active_bg": "#5A5A5A", "btn_active_fg": "#FFFFFF"
        },
        "dark": {
            "bg": "#181818", "fg": "#E0E0E0", "btn_bg": "#333333", "entry_bg": "#2C2C2C",
            "btn_active_bg": "#4A4A4A", "btn_active_fg": "#FFFFFF"
        },
        "light": {
            "bg": "#FFFFFF", "fg": "#333333", "btn_bg": "#DDDDDD", "entry_bg": "#FFFFFF",
            "btn_active_bg": "#BBBBBB", "btn_active_fg": "#000000"
        },
        "blue_soft": {
            "bg": "#EAF2FB", "fg": "#1F3B57", "btn_bg": "#A9CCE3", "entry_bg": "#FFFFFF",
            "btn_active_bg": "#85C1E9", "btn_active_fg": "#000000"
        },
        "green_terminal": {
            "bg": "#1A1F16", "fg": "#B5E853", "btn_bg": "#2A2F26", "entry_bg": "#1F261D",
            "btn_active_bg": "#3A4A36", "btn_active_fg": "#FFFFFF"
        },
        "cyberpunk_violet": {
            "bg": "#1A001F", "fg": "#DA70D6", "btn_bg": "#3D1A47", "entry_bg": "#260033",
            "btn_active_bg": "#551A8B", "btn_active_fg": "#FFFFFF"
        },
        "solar_desert": {
            "bg": "#FCEECF", "fg": "#8B572A", "btn_bg": "#F5D9A0", "entry_bg": "#FFFFFF",
            "btn_active_bg": "#E6B97E", "btn_active_fg": "#000000"
        },
        "pastel_candy": {
            "bg": "#FFF5F7", "fg": "#7B4B94", "btn_bg": "#FFD1DC", "entry_bg": "#FFFFFF",
            "btn_active_bg": "#FFB6C1", "btn_active_fg": "#5A3A6D"
        },
        "frost_mint": {
            "bg": "#E8F6F3", "fg": "#117864", "btn_bg": "#A3E4D7", "entry_bg": "#D1F2EB",
            "btn_active_bg": "#76D7C4", "btn_active_fg": "#000000"
        },
        "tech_night": {
            "bg": "#121212", "fg": "#00FFFF", "btn_bg": "#1F1F1F", "entry_bg": "#2A2A2A",
            "btn_active_bg": "#004C4C", "btn_active_fg": "#FFFFFF"
        },
        "morning_glory": {
            "bg": "#FFF3E0", "fg": "#6E2C00", "btn_bg": "#FFDAB9", "entry_bg": "#FFF8E1",
            "btn_active_bg": "#FFB074", "btn_active_fg": "#000000"
        },
        "elegant_gray": {
            "bg": "#F2F2F2", "fg": "#4D4D4D", "btn_bg": "#CCCCCC", "entry_bg": "#FFFFFF",
            "btn_active_bg": "#BFBFBF", "btn_active_fg": "#000000"
        },
        "dark_metal": {
            "bg": "#1C1C1C", "fg": "#C0C0C0", "btn_bg": "#2E2E2E", "entry_bg": "#2E2E2E",
            "btn_active_bg": "#3E3E3E", "btn_active_fg": "#FFFFFF"
        },
        "inferno_red": {
            "bg": "#2A0000", "fg": "#FF5C5C", "btn_bg": "#660000", "entry_bg": "#400000",
            "btn_active_bg": "#990000", "btn_active_fg": "#FFFFFF"
        },
        "pastel_sky": {
            "bg": "#E3F2FD", "fg": "#1565C0", "btn_bg": "#90CAF9", "entry_bg": "#FFFFFF",
            "btn_active_bg": "#64B5F6", "btn_active_fg": "#000000"
        },
        "purple_dream": {
            "bg": "#F3E5F5", "fg": "#6A1B9A", "btn_bg": "#CE93D8", "entry_bg": "#F8BBD0",
            "btn_active_bg": "#AB47BC", "btn_active_fg": "#FFFFFF"
        },
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Escalonamento")
        self.processos = []
        self.quantum = 4 ## Define o quantum
        self.configurar_tema("purple_dream")   ## Pode mudar o tema de acordo
        self.setup_ui()

    def configurar_tema(self, nome_tema: str):
        tema = self.TEMAS.get(nome_tema)
        if not tema:
            raise ValueError(f"Tema '{nome_tema}' não encontrado")
        style = ttk.Style()
        self.root.configure(bg=tema["bg"])
        style.theme_use("clam")
        style.configure("TLabel", background=tema["bg"], foreground=tema["fg"])
        style.configure("TButton", background=tema["btn_bg"], foreground=tema["fg"], relief="flat")
        style.configure("TEntry", fieldbackground=tema["entry_bg"], foreground=tema["fg"])
        style.configure("TFrame", background=tema["bg"])
        style.map("TButton",
            background=[('active', tema["btn_active_bg"])],
            foreground=[('active', tema["btn_active_fg"])])

    def setup_ui(self):
        frm_input = ttk.Frame(self.root)
        frm_input.pack(pady=10)

        ttk.Label(frm_input, text="Nome:").grid(row=0, column=0)
        self.nome_entry = ttk.Entry(frm_input, width=10)
        self.nome_entry.grid(row=0, column=1)

        ttk.Label(frm_input, text="Tempo Exec:").grid(row=0, column=2)
        self.tempo_entry = ttk.Entry(frm_input, width=5)
        self.tempo_entry.grid(row=0, column=3)

        ttk.Label(frm_input, text="Prioridade:").grid(row=0, column=4)
        self.prioridade_entry = ttk.Entry(frm_input, width=5)
        self.prioridade_entry.grid(row=0, column=5)

        ttk.Label(frm_input, text="Tempo Entrada:").grid(row=0, column=6)
        self.entrada_entry = ttk.Entry(frm_input, width=5)
        self.entrada_entry.grid(row=0, column=7)

        ttk.Button(frm_input, text="Adicionar Processo", command=self.adicionar_processo).grid(row=0, column=8, padx=5)

        self.lista = tk.Listbox(self.root, width=70, bg="#3C3C3C", fg="#DCDCDC")
        self.lista.pack(pady=10)

        frm_buttons = ttk.Frame(self.root)
        frm_buttons.pack()

        ttk.Button(frm_buttons, text="Gerar Gráfico Gantt", command=self.gerar_gantt).pack(side=tk.LEFT, padx=10)
        ttk.Button(frm_buttons, text="Exportar Gráfico", command=self.exportar_gantt).pack(side=tk.LEFT, padx=10)

        self.tmp_label = ttk.Label(self.root, text="TMP: N/A   TME: N/A")
        self.tmp_label.pack(pady=10)

    def adicionar_processo(self):
        nome = self.nome_entry.get()
        tempo = self.tempo_entry.get()
        prioridade = self.prioridade_entry.get()
        entrada = self.entrada_entry.get()

        if nome and tempo.isdigit() and prioridade.isdigit() and entrada.isdigit():
            cor = self.gerar_cor_unica(nome)
            self.processos.append({
                "nome": nome,
                "tempo_exec": int(tempo),
                "prioridade": int(prioridade),
                "entrada": int(entrada),
                "cor": cor
            })
            self.lista.insert(tk.END, f"{nome} - {tempo} - Prioridade {prioridade} - Entrada {entrada}")
            self.nome_entry.delete(0, tk.END)
            self.tempo_entry.delete(0, tk.END)
            self.prioridade_entry.delete(0, tk.END)
            self.entrada_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Erro", "Preencha todos os campos corretamente.")

    def gerar_cor_unica(self, nome):
        random.seed(nome)
        return f"#{random.randint(0, 0xFFFFFF):06x}"

    def simular_execucao(self, lista):
        tempo = 0
        result = []
        for p in lista:
            result.append({"nome": p["nome"], "inicio": tempo, "duracao": p["tempo_exec"], "cor": p["cor"]})
            tempo += p["tempo_exec"]
        return result

    def round_robin(self, procs, q):
        fila = [{"nome": p["nome"], "restante": p["tempo_exec"], "entrada": p["entrada"], "cor": p["cor"]} for p in procs]
        tempo = 0
        execucao = []
        while any(p["restante"] > 0 for p in fila):
            for p in fila:
                if p["restante"] > 0 and p["entrada"] <= tempo:
                    duracao = min(q, p["restante"])
                    execucao.append({"nome": p["nome"], "inicio": tempo, "duracao": duracao, "cor": p["cor"]})
                    tempo += duracao
                    p["restante"] -= duracao
        return execucao

    def calcular_tme_tmp(self, execucao):
        tempos_finais = {}
        tempos_iniciais = {}
        for p in execucao:
            nome = p["nome"]
            if nome not in tempos_iniciais:
                tempos_iniciais[nome] = p["inicio"]
            tempos_finais[nome] = p["inicio"] + p["duracao"]

        total_espera = 0
        total_execucao = 0
        n = len(self.processos)

        for proc in self.processos:
            nome = proc["nome"]
            entrada = proc["entrada"]
            duracao = proc["tempo_exec"]
            fim = tempos_finais[nome]
            inicio = tempos_iniciais[nome]

            espera = inicio - entrada
            execucao = fim - entrada

            total_espera += espera
            total_execucao += execucao

        tmp = total_espera / n
        tme = total_execucao / n
        return round(tmp, 2), round(tme, 2)

    def gerar_gantt(self):
        if not self.processos:
            messagebox.showinfo("Aviso", "Adicione pelo menos um processo.")
            return

        fifo = sorted(self.processos, key=lambda x: x["entrada"])
        sjf = sorted(self.processos, key=lambda x: x["tempo_exec"])
        prioridade = sorted(self.processos, key=lambda x: x["prioridade"])
        rr = self.round_robin(self.processos, self.quantum)

        exec_fifo = self.simular_execucao(fifo)
        exec_sjf = self.simular_execucao(sjf)
        exec_prio = self.simular_execucao(prioridade)
        execucoes = [exec_fifo, exec_sjf, exec_prio, rr]
        nomes = ["FIFO", "SJF", "Prioridade", f"Round Robin (Q={self.quantum})"]

        plt.style.use('dark_background')
        fig, axs = plt.subplots(4, 1, figsize=(10, 6), sharex=True)
        for i, (ax, nome, execucao) in enumerate(zip(axs, nomes, execucoes)):
            for bloco in execucao:
                ax.barh(0, bloco['duracao'], left=bloco['inicio'], color=bloco['cor'])
                ax.text(bloco['inicio'] + bloco['duracao']/2, 0, bloco['nome'], ha='center', va='center', color='white')
            ax.set_yticks([])
            ax.set_ylabel(nome, rotation=0, labelpad=60)

        # Aplica os labels de cada gráfico
        axs[-1].set_xlabel("Tempo")

        # >>> AQUI: define os ticks personalizados no eixo X
        tempo_maximo = max(
            max(bloco["inicio"] + bloco["duracao"] for bloco in execucao)
            for execucao in execucoes
        )
        ticks = np.arange(0, tempo_maximo + 1, self.quantum)  # 1 ou self.quantum
        for ax in axs:
            ax.set_xticks(ticks)

        plt.tight_layout()
       
        # Calcula TMP e TME e atualiza o label
        tmp, tme = self.calcular_tme_tmp(exec_fifo)
        self.tmp_label.config(text=f"Tempo Médio de Espera (TMP): {tmp:.2f}   Tempo Médio de Execução (TME): {tme:.2f}")


        if hasattr(self, 'canvas'):
            self.canvas.get_tk_widget().destroy()

        self.canvas = FigureCanvasTkAgg(fig, master=self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(pady=10)

        self.fig = fig

    def exportar_gantt(self):
        if not hasattr(self, 'fig'):
            messagebox.showinfo("Aviso", "Gere o gráfico antes de exportar.")
            return

        arquivo = filedialog.asksaveasfilename(defaultextension=".png",
                                               filetypes=[("PNG files", "*.png")],
                                               title="Salvar gráfico como")
        if arquivo:
            self.fig.savefig(arquivo)
            messagebox.showinfo("Sucesso", f"Gráfico salvo em: {arquivo}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SchedulerApp(root)
    root.mainloop()

