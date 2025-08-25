import locale
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Union, Optional

# Configuração de localização
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'C')  # Fallback


class CalculadoraEstatistica:
    """Calculadora para fórmulas estatísticas com interface gráfica."""
    
    def __init__(self):
        self.resultados: List[Dict] = []
        self.root = tk.Tk()
        self._configurar_janela()
        self._criar_interface()
    
    def _configurar_janela(self):
        """Configura a janela principal."""
        self.root.title("Calculadora Estatística")
        self.root.geometry("400x600")
        self.root.resizable(True, True)
    
    @staticmethod
    def converter_float(valor: str) -> Optional[float]:
        """Converte string para float usando locale."""
        if not valor.strip():
            return None
        try:
            return locale.atof(valor.strip())
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def formula_amostra_proporcao(p: float, q: float, Z: float, N: float, E: float) -> float:
        """
        Fórmula para cálculo de amostra com proporção conhecida.
        n = (N * p * q * Z²) / (p * q * Z² + (N-1) * E²)
        """
        numerador = N * p * q * (Z**2)
        denominador = p * q * (Z**2) + ((N - 1) * (E**2))
        return numerador / denominador
    
    @staticmethod
    def formula_amostra_desvio(N: float, sigma: float, Z: float, E: float) -> float:
        """
        Fórmula para cálculo de amostra com desvio padrão conhecido.
        n = (N * σ² * Z²) / ((N-1) * E² + σ² * Z²)
        """
        numerador = N * (sigma**2) * (Z**2)
        denominador = ((N - 1) * (E**2)) + (sigma**2) * (Z**2)
        return numerador / denominador
    
    def _validar_entradas(self, valores: List[Optional[float]], nomes: List[str]) -> bool:
        """Valida se todas as entradas são números válidos."""
        for valor, nome in zip(valores, nomes):
            if valor is None:
                messagebox.showerror("Erro de Validação", 
                                   f"O campo '{nome}' contém um valor inválido!")
                return False
            if valor <= 0:
                messagebox.showerror("Erro de Validação", 
                                   f"O campo '{nome}' deve ser maior que zero!")
                return False
        return True
    
    def _criar_grupo_formula(self, parent: tk.Widget, titulo: str, campos: List[str], 
                           comando_calculo, linha_inicial: int) -> Dict[str, tk.Entry]:
        """Cria um grupo de campos para uma fórmula."""
        # Título do grupo
        titulo_frame = ttk.LabelFrame(parent, text=titulo, padding="10")
        titulo_frame.grid(row=linha_inicial, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # Dicionário para armazenar as entradas
        entradas = {}
        
        # Criar campos de entrada
        for i, campo in enumerate(campos):
            ttk.Label(titulo_frame, text=f"{campo}:").grid(row=i, column=0, sticky="w", pady=2)
            entrada = ttk.Entry(titulo_frame, width=15)
            entrada.grid(row=i, column=1, sticky="ew", pady=2, padx=(10, 0))
            entradas[campo] = entrada
        
        # Configurar expansão das colunas
        titulo_frame.columnconfigure(1, weight=1)
        
        # Botão de cálculo
        botao = ttk.Button(titulo_frame, text=f"Calcular {titulo}", command=comando_calculo)
        botao.grid(row=len(campos), column=0, columnspan=2, pady=10)
        
        # Label de resultado (criado dentro do frame)
        label_resultado = ttk.Label(titulo_frame, text="", foreground="blue")
        label_resultado.grid(row=len(campos) + 1, column=0, columnspan=2, pady=5)
        
        return entradas, label_resultado
    
    def _criar_interface(self):
        """Cria a interface gráfica completa."""
        # Configurar expansão da janela
        self.root.columnconfigure(0, weight=1)
        
        # Criar grupos de fórmulas
        self.entradas_formula1, self.label_resultado1 = self._criar_grupo_formula(
            self.root, "Fórmula 1 - Proporção", 
            ["p", "q", "Z", "N", "E"], 
            self._calcular_formula1, 
            0
        )
        
        self.entradas_formula2, self.label_resultado2 = self._criar_grupo_formula(
            self.root, "Fórmula 2 - Desvio Padrão", 
            ["N", "σ", "Z", "E"], 
            self._calcular_formula2, 
            1
        )
        
        # Frame para botões de ação
        frame_acoes = ttk.Frame(self.root, padding="10")
        frame_acoes.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        frame_acoes.columnconfigure(0, weight=1)
        frame_acoes.columnconfigure(1, weight=1)
        
        # Botões de ação
        ttk.Button(frame_acoes, text="Limpar Resultados", 
                  command=self._limpar_resultados).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        ttk.Button(frame_acoes, text="Exportar Resultados", 
                  command=self._exportar_resultados).grid(row=0, column=1, sticky="ew", padx=(5, 0))
        
        # Frame para histórico
        frame_historico = ttk.LabelFrame(self.root, text="Histórico", padding="10")
        frame_historico.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        frame_historico.columnconfigure(0, weight=1)
        
        # Listbox para histórico
        self.lista_historico = tk.Listbox(frame_historico, height=6)
        self.lista_historico.grid(row=0, column=0, sticky="ew")
        
        # Scrollbar para o histórico
        scrollbar = ttk.Scrollbar(frame_historico, orient="vertical", command=self.lista_historico.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.lista_historico.configure(yscrollcommand=scrollbar.set)
    
    def _calcular_formula1(self):
        """Calcula a primeira fórmula (proporção)."""
        try:
            # Extrair valores das entradas
            valores_str = {}
            for campo, entrada in self.entradas_formula1.items():
                valores_str[campo] = entrada.get().strip()
            
            # Converter para float
            valores = {}
            for campo, valor_str in valores_str.items():
                valor = self.converter_float(valor_str)
                if valor is None:
                    messagebox.showerror("Erro de Validação", 
                                       f"O campo '{campo}' contém um valor inválido: '{valor_str}'")
                    return
                if valor <= 0:
                    messagebox.showerror("Erro de Validação", 
                                       f"O campo '{campo}' deve ser maior que zero! Valor atual: {valor}")
                    return
                valores[campo] = valor
            
            # Calcular resultado
            resultado = self.formula_amostra_proporcao(
                p=valores['p'], 
                q=valores['q'], 
                Z=valores['Z'], 
                N=valores['N'], 
                E=valores['E']
            )
            
            # Debug: mostrar valores usados no cálculo
            print(f"DEBUG Formula 1 - p:{valores['p']}, q:{valores['q']}, Z:{valores['Z']}, N:{valores['N']}, E:{valores['E']}")
            print(f"DEBUG Formula 1 - Resultado: {resultado}")
            
            # Armazenar resultado
            registro = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Fórmula": "Proporção",
                **valores,
                "Resultado": round(resultado, 4)
            }
            self.resultados.append(registro)
            
            # Atualizar interface
            self.label_resultado1.config(text=f"Resultado: {resultado:.4f}")
            self._atualizar_historico()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro no cálculo da Fórmula 1: {str(e)}")
            print(f"ERRO Formula 1: {e}")
    
    def _calcular_formula2(self):
        """Calcula a segunda fórmula (desvio padrão)."""
        try:
            # Extrair valores das entradas
            valores_str = {}
            for campo, entrada in self.entradas_formula2.items():
                valores_str[campo] = entrada.get().strip()
            
            # Converter para float
            valores_numericos = {}
            for campo, valor_str in valores_str.items():
                valor = self.converter_float(valor_str)
                if valor is None:
                    messagebox.showerror("Erro de Validação", 
                                       f"O campo '{campo}' contém um valor inválido: '{valor_str}'")
                    return
                if valor <= 0:
                    messagebox.showerror("Erro de Validação", 
                                       f"O campo '{campo}' deve ser maior que zero! Valor atual: {valor}")
                    return
                valores_numericos[campo] = valor
            
            # Mapear os parâmetros para os nomes corretos da função
            N = valores_numericos['N']
            sigma = valores_numericos['σ']
            Z = valores_numericos['Z']
            E = valores_numericos['E']
            
            # Debug: mostrar valores usados no cálculo
            print(f"DEBUG Formula 2 - N:{N}, σ:{sigma}, Z:{Z}, E:{E}")
            
            # Calcular resultado
            resultado = self.formula_amostra_desvio(N=N, sigma=sigma, Z=Z, E=E)
            
            print(f"DEBUG Formula 2 - Resultado: {resultado}")
            
            # Armazenar resultado
            registro = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Fórmula": "Desvio Padrão",
                "N": N,
                "sigma": sigma,
                "Z": Z,
                "E": E,
                "Resultado": round(resultado, 4)
            }
            self.resultados.append(registro)
            
            # Atualizar interface
            self.label_resultado2.config(text=f"Resultado: {resultado:.4f}")
            self._atualizar_historico()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro no cálculo da Fórmula 2: {str(e)}")
            print(f"ERRO Formula 2: {e}")
    
    def _atualizar_historico(self):
        """Atualiza a lista de histórico."""
        self.lista_historico.delete(0, tk.END)
        for i, resultado in enumerate(self.resultados[-10:], 1):  # Últimos 10 resultados
            texto = f"{i}. {resultado['Fórmula']}: {resultado['Resultado']}"
            self.lista_historico.insert(tk.END, texto)
    
    def _limpar_resultados(self):
        """Limpa todos os resultados."""
        if messagebox.askyesno("Confirmar", "Deseja limpar todos os resultados?"):
            self.resultados.clear()
            self.label_resultado1.config(text="")
            self.label_resultado2.config(text="")
            self.lista_historico.delete(0, tk.END)
    
    def _exportar_resultados(self):
        """Exporta os resultados para um arquivo Excel."""
        if not self.resultados:
            messagebox.showinfo("Informação", "Nenhum resultado para exportar!")
            return
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            arquivo = f"resultados_calculadora_{timestamp}.xlsx"
            
            df = pd.DataFrame(self.resultados)
            df.to_excel(arquivo, index=False, engine='openpyxl')
            
            messagebox.showinfo("Sucesso", 
                              f"✅ {len(self.resultados)} resultado(s) exportado(s) para:\n{arquivo}")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {str(e)}")
    
    def executar(self):
        """Executa a aplicação."""
        self.root.mainloop()


# Execução da aplicação
if __name__ == "__main__":
    app = CalculadoraEstatistica()
    app.executar()