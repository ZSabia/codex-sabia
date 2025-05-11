#!/usr/bin/env python3

import tkinter as tk
import numpy as np
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random



class SchedulerApp:
    TEMAS = {
        # Temas de cores para a interface
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
        # Inicialização da aplicação e variáveis principais
        self.root = root
        self.root.title("Simulador de Escalonamento")
        self.processos = []
        self.quantum = 0
        self.setup_ui()

    def configurar_tema(self, nome_tema: str):
        # Aplica o tema selecionado à interface
        tema = self.TEMAS.get(nome_tema)
        if not tema:
            raise ValueError(f"Tema '{nome_tema}' não encontrado")
        style = ttk.Style()
        self.root.configure(bg=tema["bg"])
        style.theme_use("clam")
        style.configure("TLabel", background=tema["bg"], foreground=tema["fg"], font=("Segoe UI", 12))
        style.configure("TButton", background=tema["btn_bg"], foreground=tema["fg"], relief="flat", padding=8, font=("Segoe UI", 12, "bold"), borderwidth=0)
        style.configure("TEntry", fieldbackground=tema["entry_bg"], foreground=tema["fg"], padding=6, font=("Segoe UI", 12))
        style.configure("TFrame", background=tema["bg"], borderwidth=0)
        style.map("TButton",
            background=[('active', tema["btn_active_bg"])],
            foreground=[('active', tema["btn_active_fg"])]
        )
        # Arredondar cantos (quando suportado)
        try:
            style.element_create("RoundedFrame", "from", "clam")
            style.layout("RoundedFrame", [('RoundedFrame', {'sticky': 'nswe'})])
            style.configure("RoundedFrame", borderwidth=0, relief="flat")
        except Exception:
            pass
        # Aplica cor de fundo geral
        self.root.update_idletasks()
        self.root.configure(bg=tema["bg"])

    def criar_seletor_tema(self):
        # Cria o menu de seleção de tema
        frm_tema = ttk.Frame(self.root)
        frm_tema.pack(pady=14)
        ttk.Label(frm_tema, text="Tema:").pack(side=tk.LEFT, padx=7)
        self.tema_var = tk.StringVar(value="dark_soft")
        tema_menu = ttk.OptionMenu(frm_tema, self.tema_var, "dark_soft", *self.TEMAS.keys(), command=self.alterar_tema)
        tema_menu.pack(side=tk.LEFT, padx=4)

    def alterar_tema(self, nome_tema):
        # Altera o tema da interface
        try:
            self.configurar_tema(nome_tema)
        except ValueError as e:
            messagebox.showerror("Erro", str(e))

    def limpar_campos(self):
        # Limpa todos os campos de entrada
        self.nome_entry.delete(0, tk.END)
        self.tempo_entry.delete(0, tk.END)
        self.prioridade_entry.delete(0, tk.END)
        self.entrada_entry.delete(0, tk.END)

    def preencher_campos(self, nome, tempo, prioridade, entrada):
        # Preenche os campos de entrada com os valores fornecidos
        self.nome_entry.insert(0, nome)
        self.tempo_entry.insert(0, str(tempo))
        self.prioridade_entry.insert(0, str(prioridade))
        self.entrada_entry.insert(0, str(entrada))

    def gerar_processos_aleatorios(self, quantidade):
        # Gera uma lista de com processos aleatórios
        nomes_processos = [
            "chrome.exe", "python.exe", "svchost.exe", "firefox.exe", 
            "notepad.exe", "explorer.exe", "java.exe", "System", "cmd.exe",
            "code.exe", "spotify.exe", "discord.exe", "steam.exe", "edge.exe",
            "outlook.exe", "winword.exe", "excel.exe", "photoshop.exe"
        ]
        random.shuffle(nomes_processos)
        processos = []
        for i in range(quantidade):
            nome = nomes_processos[i]
            tempo_exec = random.randint(2, 20) * (i + 1)
            entrada = random.randint(0, 5) * (i + 1)
            prioridade = random.randint(0, 15)
            processos.append((nome, tempo_exec, prioridade, entrada))
        return processos

    def ativar_ia(self):
        self.limpar_processos()
        num_processos = random.randint(1, 5)
        processos = self.gerar_processos_aleatorios(num_processos)
        for nome, tempo_exec, prioridade, entrada in processos:
            self.limpar_campos()
            self.preencher_campos(nome, tempo_exec, prioridade, entrada)
            self.adicionar_processo()
        self.gerar_gantt()

    def setup_ui(self):
        # Monta toda a interface gráfica (widgets)
        self.criar_seletor_tema()
        frm_input = ctk.CTkFrame(self.root, corner_radius=16)
        frm_input.pack(pady=18, padx=16)

        labels = ["Nome:", "Tempo Exec:", "Prioridade:", "Entrada:", "Quantum:"]
        for idx, text in enumerate(labels):
            ttk.Label(frm_input, text=text).grid(row=0, column=idx*2, padx=6, pady=8)
        self.nome_entry = ttk.Entry(frm_input, width=14); self.nome_entry.grid(row=0, column=1, padx=6, pady=8)
        self.tempo_entry = ttk.Entry(frm_input, width=9); self.tempo_entry.grid(row=0, column=3, padx=6, pady=8)
        self.prioridade_entry = ttk.Entry(frm_input, width=9); self.prioridade_entry.grid(row=0, column=5, padx=6, pady=8)
        self.entrada_entry = ttk.Entry(frm_input, width=9); self.entrada_entry.grid(row=0, column=7, padx=6, pady=8)
        self.quantum_entry = ttk.Entry(frm_input, width=9); self.quantum_entry.insert(0, "4"); self.quantum_entry.grid(row=0, column=9, padx=6, pady=8)
        ttk.Button(frm_input, text="Adicionar", command=self.adicionar_processo).grid(row=0, column=10, padx=10, pady=8)

        # Substitui Listbox por Treeview para visual moderno e cantos arredondados
        columns = ("Nome", "Execução", "Prioridae", "Entrada")
        self.lista = ttk.Treeview(self.root, columns=columns, show="headings", height=6)
        for col in columns:
            self.lista.heading(col, text=col)
            self.lista.column(col, anchor="center", width=120)
        self.lista.pack(pady=16, padx=16, ipady=8)

        frm_buttons = ctk.CTkFrame(self.root, corner_radius=16); frm_buttons.pack(pady=8)
        ttk.Button(frm_buttons, text="Gerar Gráfico", command=self.gerar_gantt).pack(side=tk.LEFT, padx=16, pady=8)
        ttk.Button(frm_buttons, text="Exportar", command=self.exportar_gantt).pack(side=tk.LEFT, padx=16, pady=8)
        ttk.Button(frm_buttons, text="Limpar", command=self.limpar_processos).pack(side=tk.LEFT, padx=16, pady=8)
        ttk.Button(self.root, text="IA", command=self.ativar_ia, width=3).place(relx=1.0, rely=0.0, anchor='ne')
        self.tmp_label = ttk.Label(self.root, text="TME: N/A   TMP: N/A", font=("Consolas", 12, "bold"))
        self.tmp_label.pack(pady=16)

    def adicionar_processo(self):
        # Adiciona um novo processo à lista interna e à interface
        nome = self.nome_entry.get()
        tempo = self.tempo_entry.get()
        prioridade = self.prioridade_entry.get()
        entrada = self.entrada_entry.get()
        if nome and tempo.isdigit() and prioridade.isdigit() and entrada.isdigit():
            pid = len(self.processos)
            cor = self.gerar_cor_unica(nome + str(pid))
            self.processos.append({
                "pid": pid,
                "nome": nome,
                "tempo_exec": int(tempo),
                "prioridade": int(prioridade),
                "entrada": int(entrada),
                "cor": cor
            })
            self.lista.insert("", tk.END, values=(nome, tempo, prioridade, entrada))
            self.limpar_campos()
        else:
            messagebox.showerror("Erro", "Preencha tudo certinho, parça.")

    def limpar_processos(self):
        # Limpa todos os processos e o gráfico
        self.processos.clear(); self.lista.delete(*self.lista.get_children())
        self.tmp_label.config(text="TMP: N/A   TME: N/A")
        if hasattr(self, 'canvas'):
            self.canvas.get_tk_widget().destroy()

    def gerar_cor_unica(self, nome):
        # Gera uma cor única baseada no nome do processo
        random.seed(nome)
        return f"#{random.randint(0, 0xFFFFFF):06x}"

    def simular_execucao(self, lista):
        # Simula execução FIFO dos processos
        tempo = 0
        result = []
        for p in lista:
            inicio = max(tempo, p["entrada"])
            dur = p.get("duracao", p["tempo_exec"])
            result.append({
                "pid": p["pid"],
                "nome": p["nome"],
                "entrada": p["entrada"],
                "duracao": dur,
                "inicio": inicio,
                "fim": inicio + dur,
                "cor": p["cor"]
            })
            tempo = inicio + dur
        return result

    def round_robin(self, procs, q):
        # Simula execução Round Robin
        from collections import deque
        fila = deque(sorted([{"pid":p["pid"],"nome":p["nome"],"restante":p["tempo_exec"],"entrada":p["entrada"],"cor":p["cor"]} for p in procs], key=lambda x: x["entrada"]))
        tempo = 0; execucao = []; pronta = deque()
        while fila or pronta:
            while fila and fila[0]["entrada"] <= tempo:
                pronta.append(fila.popleft())
            if not pronta:
                tempo += 1
                continue
            proc = pronta.popleft()
            dur = min(q, proc["restante"])
            execucao.append({**proc, "duracao": dur, "inicio": tempo, "fim": tempo + dur})
            tempo += dur
            proc["restante"] -= dur
            while fila and fila[0]["entrada"] <= tempo:
                pronta.append(fila.popleft())
            if proc["restante"] > 0:
                pronta.append(proc)
        return list(execucao)

    def sjf(self, procs):
        # Simula execução SJF (Shortest Job First)
        restos = sorted([{"pid":p["pid"],"nome":p["nome"],"tempo_exec":p["tempo_exec"],"entrada":p["entrada"],"cor":p["cor"]} for p in procs], key=lambda x: x["entrada"])
        tempo = 0; execucao = []
        while restos:
            avail = [p for p in restos if p["entrada"] <= tempo]
            if not avail:
                tempo += 1
                continue
            p = min(avail, key=lambda x: x["tempo_exec"])
            restos.remove(p)
            inicio = max(tempo, p["entrada"])
            dur = p["tempo_exec"]
            execucao.append({**p, "duracao": dur, "inicio": inicio, "fim": inicio + dur})
            tempo = inicio + dur
        return execucao

    def prioridade(self, procs):
        # Simula execução por prioridade
        restos = sorted([{"pid":p["pid"],"nome":p["nome"],"tempo_exec":p["tempo_exec"],"entrada":p["entrada"],"prioridade":p["prioridade"],"cor":p["cor"]} for p in procs], key=lambda x: x["entrada"])
        tempo = 0; execucao = []
        while restos:
            disponiveis = [p for p in restos if p["entrada"] <= tempo]
            if not disponiveis:
                tempo += 1
                continue
            p = min(disponiveis, key=lambda x: x["prioridade"])
            restos.remove(p)
            inicio = max(tempo, p["entrada"])
            dur = p["tempo_exec"]
            execucao.append({**p, "duracao": dur, "inicio": inicio, "fim": inicio + dur})
            tempo = inicio + dur
        return execucao


    def calcular_tme_tmp(self, execucao):
        # Calcula o Tempo Médio de Espera (TME) e o Tempo Médio de Retorno (TMP)
        stats = {}
        for seg in execucao:
            pid = seg["pid"]
            if pid not in stats:
                stats[pid] = {"entrada": seg["entrada"], "tempo_cpu": 0, "termino": 0}
            stats[pid]["tempo_cpu"] += seg["duracao"]
            stats[pid]["termino"] = max(stats[pid]["termino"], seg["fim"])

        total_espera = 0
        total_retorno = 0
        n = len(stats)

        for v in stats.values():
            tempo_retorno = v["termino"] - v["entrada"]    # tempo total até o processo terminar
            tempo_espera = tempo_retorno - v["tempo_cpu"]      # tempo que ficou esperando
            total_espera += tempo_espera
            total_retorno += tempo_retorno

        tme = total_espera / n
        tmp = total_retorno / n
        return round(tme, 2), round(tmp, 2)


    def gerar_gantt(self):
        # Gera o gráfico de Gantt para todos os algoritmos
        if not self.processos:
            messagebox.showinfo("Aviso", "Adiciona uns processos aí primeiro.")
            return
        try:
            quantum = int(self.quantum_entry.get())
            if quantum <= 0:
                messagebox.showerror("Erro", "Quantum deve ser maior que zero.")
                return
            self.quantum = quantum
        except ValueError:
            messagebox.showerror("Erro", "Quantum inválido.")
            return

        exec_fifo = self.simular_execucao(sorted(self.processos, key=lambda x: x["entrada"]))
        exec_sjf = self.sjf(self.processos)
        exec_pri = self.prioridade(self.processos)
        exec_rr = self.round_robin(self.processos, self.quantum)

        execucoes = [exec_fifo, exec_sjf, exec_pri, exec_rr]
        nomes = ["FIFO", "SJF", "Prioridade", f"Round Robin (Q={self.quantum})"]

        resultados = [self.calcular_tme_tmp(execucao) for execucao in execucoes]
        texto_original = "\n".join(
            f"{nome} -> TME: {tme:.2f} | TMP: {tmp:.2f}"
            for nome, (tme, tmp) in zip(nomes, resultados)
        )


        self.tmp_label.config(text=texto_original)

        plt.style.use('dark_background')
        fig, axs = plt.subplots(len(execucoes), 1, figsize=(10, 6), sharex=True)
        fig.patch.set_facecolor('#1e1e1e')
        self.execucoes = execucoes

        tempo_maximo = max(
            max(bloco["inicio"] + bloco["duracao"] for bloco in execucao)
            for execucao in execucoes
        )
        ticks = np.arange(0, tempo_maximo + 1, 1)

        def on_hover(event):
            if event.inaxes is not None:
                ax_index = axs.flatten().tolist().index(event.inaxes)
                execucao = execucoes[ax_index]
                for bloco in execucao:
                    if bloco['inicio'] <= event.xdata <= (bloco['inicio'] + bloco['duracao']):
                        texto = f"Processo: {bloco['nome']}\nInício: {bloco['inicio']}\nDuração: {bloco['duracao']}\nFim: {bloco['fim']}"
                        self.tmp_label.config(text=texto)
                        return
            self.tmp_label.config(text=texto_original)

        for ax, nome, execucao in zip(axs, nomes, execucoes):
            ax.set_facecolor('#1e1e1e')
            ax.tick_params(colors='white')
            for bloco in execucao:
                ax.barh(0, bloco['duracao'], left=bloco['inicio'], color=bloco['cor'])
                ax.text(
                    bloco['inicio'] + bloco['duracao'] / 2, 0, bloco['nome'],
                    ha='center', va='center', color='white', fontsize=8
                )
            ax.set_yticks([])
            ax.set_ylabel(nome, rotation=0, labelpad=60, color='white')
            ax.set_xticks(ticks)

        axs[-1].set_xlabel("Tempo", color='white')
        plt.tight_layout()

        if hasattr(self, 'canvas'):
            self.canvas.get_tk_widget().destroy()

        self.canvas = FigureCanvasTkAgg(fig, master=self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(pady=10)
        self.fig = fig

        self.canvas.mpl_connect('motion_notify_event', on_hover)
        self.canvas.mpl_connect('scroll_event', self.zoom)
        self.canvas.mpl_connect('button_press_event', self.handle_mouse_buttons)

    def zoom(self, event):
        # Função de zoom horizontal no gráfico
        ax = event.inaxes
        if ax is None:
            return
        cur_xlim = ax.get_xlim()
        if event.button == 'up':
            shift = (cur_xlim[1] - cur_xlim[0]) * 0.1
            ax.set_xlim(cur_xlim[0] + shift, cur_xlim[1] + shift)
        elif event.button == 'down':
            shift = (cur_xlim[1] - cur_xlim[0]) * 0.1
            ax.set_xlim(cur_xlim[0] - shift, cur_xlim[1] - shift)
        self.canvas.draw()

    def handle_mouse_buttons(self, event):
        # Gerencia cliques do mouse para zoom/reset
        if event.button == 1:
            self.zoom_section(event)
        elif event.button == 3:
            self.reset_zoom(event)

    def reset_zoom(self, event):
        # Reseta o zoom do gráfico
        if hasattr(self, 'execucoes'):
            tempo_maximo = max(
                max(bloco["inicio"] + bloco["duracao"] for bloco in execucao)
                for execucao in self.execucoes
            )
            for ax in self.fig.axes:
                ax.set_xlim(0, tempo_maximo)
            self.canvas.draw()

    def zoom_section(self, event):
        # Dá zoom em uma seção específica do gráfico
        xdata = event.xdata
        if xdata is None:
            return
        for ax in self.fig.axes:
            ax.set_xlim(xdata - 5, xdata + 5)
        self.canvas.draw()

    def exportar_gantt(self):
        # Exporta o gráfico de Gantt para arquivo com UX aprimorado
        if (not hasattr(self, 'fig') or 
            not hasattr(self, 'canvas') or 
            not plt.fignum_exists(self.fig.number) or 
            not self.processos):
            messagebox.showerror("Exportação Falhou", "Nenhum gráfico válido para exportar.\nGere um gráfico primeiro.", icon='warning')
            return

        file_path = filedialog.asksaveasfilename(
            title="Salvar Gráfico de Gantt",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("Todos os arquivos", "*.*")],
            initialfile="gantt.png"
        )
        if file_path:
            try:
                self.fig.savefig(file_path, dpi=300, facecolor=self.fig.get_facecolor())
                resposta = messagebox.askyesno(
                    "Exportação Concluída",
                    f"Gráfico exportado com sucesso para:\n{file_path}\n\nDeseja abrir a pasta?",
                    icon='info'
                )
                if resposta:
                    import os
                    import subprocess
                    pasta = os.path.dirname(file_path)
                    subprocess.Popen(["xdg-open", pasta])
            except Exception as e:
                messagebox.showerror("Erro ao Exportar", f"Ocorreu um erro ao salvar o arquivo:\n{e}")

def escolher_tema(temas):
    escolha = {"tema": None}
    def confirmar():
        escolha["tema"] = var.get()
        win.destroy()

    win = tk.Tk()
    win.title("Escolha o Tema")
    win.geometry("350x180")
    win.resizable(False, False)
    tk.Label(win, text="Escolha o tema para iniciar:", font=("Segoe UI", 12, "bold")).pack(pady=18)
    var = tk.StringVar(value="dark_soft")
    opcoes = list(temas.keys())
    tema_menu = ttk.OptionMenu(win, var, var.get(), *opcoes)
    tema_menu.pack(pady=8)
    ttk.Button(win, text="Confirmar", command=confirmar).pack(pady=16)
    win.grab_set()
    win.mainloop()
    return escolha["tema"]

if __name__ == "__main__":
    tema_escolhido = escolher_tema(SchedulerApp.TEMAS)
    root = tk.Tk()
    app = SchedulerApp(root)
    #app.configurar_tema(tema_escolhido)
    root.mainloop()
