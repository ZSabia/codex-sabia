# codex-sabia

Coleção de aplicações pessoais em Python, desenvolvidas por Zé Sabiá para explorar estatística, escalonamento de processos e ferramentas para o desktop Linux.

Os programas são independentes e utilizam interfaces gráficas em Tkinter. Este README apresenta suas funcionalidades, dependências e pontos de entrada para quem deseja executar, estudar ou adaptar o código.

## Sobre as interfaces

As interfaces atuais são implementações iniciais e podem ser adaptadas conforme a necessidade. Cores, fontes, organização dos componentes e disposição das telas não constituem um padrão definitivo.

A personalização é feita no código. Atualmente não existe um editor de layouts ou uma API comum de temas entre as aplicações; a interface e parte da lógica estão no mesmo arquivo de cada programa.

## Aplicações

### Calculadora estatística

[CalculadoraEstatistica.py](CalculadoraEstatistica.py)

Calcula tamanho de amostra usando proporção ou desvio padrão, com entradas para população, nível de confiança e margem de erro. Mantém um histórico durante a execução e exporta os resultados para Excel (`.xlsx`) no diretório de trabalho.

- **Dependências:** pandas e openpyxl, além de Tkinter.
- **Lógica:** `formula_amostra_proporcao`, `formula_amostra_desvio` e os métodos de cálculo da classe `CalculadoraEstatistica`.
- **Interface:** `_configurar_janela`, `_criar_grupo_formula` e `_criar_interface`.
- **Exportação:** `_exportar_resultados`.

```sh
.venv/bin/python CalculadoraEstatistica.py
```

### Simulador de escalonamento

[SimuladorDeEscalonamentoV2.py](SimuladorDeEscalonamentoV2.py)

Permite cadastrar processos com tempo de execução, prioridade e instante de entrada, além de definir o quantum. Compara FIFO, SJF, prioridade e Round Robin por meio de gráficos de Gantt e calcula métricas de espera e permanência. Também permite exportar os gráficos.

- **Dependências:** NumPy e Matplotlib, além de Tkinter.
- **Lógica:** `simular_execucao`, `round_robin`, `sjf`, `prioridade` e `calcular_tme_tmp` na classe `SchedulerApp`.
- **Interface e aparência:** `setup_ui`, `configurar_tema`, `criar_seletor_tema` e `gerar_gantt`.
- **Dados de exemplo:** o botão chamado “IA” gera processos aleatórios; não utiliza um modelo de inteligência artificial.

```sh
.venv/bin/python SimuladorDeEscalonamentoV2.py
```

### Gerenciador de aliases

[alias_manager.py](alias_manager.py)

Interface para consultar, adicionar, editar e remover aliases armazenados em `~/.bash_aliases`. Exibe nome, comando e descrição e permite copiar aliases ou comandos para a área de transferência.

- **Dependência:** pyperclip, além de Tkinter.
- **Leitura e escrita:** `read_aliases`, `write_alias` e `remove_alias_from_file`.
- **Interface:** `create_gui` e as funções associadas aos botões e ao menu de contexto.
- **Ambiente:** foi escrito para Bash. O botão de abrir terminal depende da existência do comando `terminal` no sistema.

Faça uma cópia de `~/.bash_aliases` antes de experimentar alterações.

```sh
.venv/bin/python alias_manager.py
```

### FlatTrash

[FlatTrash.py](FlatTrash.py)

Ferramenta para Linux que lista aplicações Flatpak e seus tamanhos, permite solicitar a desinstalação de aplicações e consulta os maiores diretórios da pasta pessoal. Inclui uma ação de limpeza de cache e lixeira.

- **Requisitos:** Tkinter, Flatpak e os utilitários Linux chamados pelo código (`du`, `sort`, `head` e `rm`).
- **Operações:** `get_flatpaks`, `get_big_dirs`, `uninstall_flatpak` e `clean_trash_and_cache`.
- **Interface:** criada no bloco principal do arquivo, com atualização da lista em `refresh_app_list`.
- **Comportamento atual:** a limpeza apaga o conteúdo de `~/.cache` e `~/.local/share/Trash` sem confirmação específica. A remoção de Flatpaks pede confirmação, mas o retorno do comando não é validado antes da mensagem de sucesso.

Revise essas operações antes de usar a ferramenta em seu ambiente.

```sh
.venv/bin/python FlatTrash.py
```

### Cofre de senhas experimental

[CofreDeSenhas.py](CofreDeSenhas.py)

Experimento de armazenamento local que associa serviços a senhas e utiliza Fernet para criptografar os dados. Cria os arquivos `chave.key` e `senhas.dat` no diretório de trabalho.

- **Dependência:** cryptography, além de Tkinter.
- **Persistência:** `carregar_ou_criar_chave`, `salvar_senhas` e `carregar_senhas`.
- **Interface:** classe `CofreGUI`.
- **Limitação:** não há autenticação por senha mestra e a chave fica junto dos dados. Use dados fictícios para estudo; o projeto não foi apresentado como um gerenciador de senhas pronto para uso real.

Não publique a chave nem o arquivo de senhas ao compartilhar sua adaptação.

```sh
.venv/bin/python CofreDeSenhas.py
```

## Preparar o ambiente

É necessário Python 3 com suporte a Tkinter e uma sessão gráfica. As ferramentas de aliases e manutenção dependem de Linux; a compatibilidade das demais aplicações em outros sistemas não foi verificada.

```sh
git clone https://github.com/ZSabia/codex-sabia.git
cd codex-sabia
python3 -m venv .venv
```

Instale apenas as dependências da aplicação que deseja utilizar:

| Aplicação | Comando |
| --- | --- |
| Calculadora estatística | `.venv/bin/python -m pip install pandas openpyxl` |
| Simulador de escalonamento | `.venv/bin/python -m pip install numpy matplotlib` |
| Gerenciador de aliases | `.venv/bin/python -m pip install pyperclip` |
| Cofre de senhas | `.venv/bin/python -m pip install cryptography` |
| FlatTrash | Não possui dependências Python adicionais além de Tkinter |

Em distribuições baseadas em Debian/Ubuntu, Tkinter e o suporte a ambientes virtuais são disponibilizados pelos pacotes `python3-tk` e `python3-venv`. O pyperclip pode exigir uma ferramenta de área de transferência compatível com sua sessão gráfica.

## Estudar e adaptar

Cada aplicação está em um arquivo próprio. Os pontos de entrada descritos acima ajudam a localizar os cálculos, as operações e a construção da interface.

Ao modificar o layout, preserve ou atualize as associações entre componentes e callbacks. Para adaptações maiores, separar a lógica da interface em módulos facilita a reutilização e os testes.

São projetos pessoais em evolução. As descrições foram conferidas no código; não representam uma certificação de funcionamento em todas as plataformas.

## Licença

Distribuído sob a [licença MIT](LICENSE).
