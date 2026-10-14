# codex-sabia

A few Python tools I made for my own use and to try out ideas: a statistics calculator, a scheduling simulator, and some Linux utilities.

Each program runs on its own and has a Tkinter interface. If something here is useful to you, feel free to take it apart and make it your own. The layouts are just how I put the first versions together; you can change the colors, move things around, or build a different interface.

## What's here

### Statistics calculator

[CalculadoraEstatistica.py](CalculadoraEstatistica.py)

Calculates sample sizes using either proportions or standard deviation. It keeps a history of results while the app is open and can export them to an Excel file in the working directory.

**Needs:** pandas, openpyxl, and Tkinter.

The calculations are in `formula_amostra_proporcao`, `formula_amostra_desvio`, and the calculation methods in `CalculadoraEstatistica`. For the layout, start with `_configurar_janela`, `_criar_grupo_formula`, and `_criar_interface`. Excel export is handled by `_exportar_resultados`.

```sh
.venv/bin/python CalculadoraEstatistica.py
```

### Scheduling simulator

[SimuladorDeEscalonamentoV2.py](SimuladorDeEscalonamentoV2.py)

Add processes with execution times, priorities, and arrival times, then compare FIFO, SJF, priority scheduling, and Round Robin. The app displays Gantt charts, calculates waiting and turnaround times, and lets you export the charts.

**Needs:** NumPy, Matplotlib, and Tkinter.

The scheduling code is in `simular_execucao`, `round_robin`, `sjf`, and `prioridade`, inside `SchedulerApp`. Metrics are calculated in `calcular_tme_tmp`. The interface and charts are built in `setup_ui`, `configurar_tema`, `criar_seletor_tema`, and `gerar_gantt`.

The button labeled “IA” generates random example processes. It doesn't use an AI model.

```sh
.venv/bin/python SimuladorDeEscalonamentoV2.py
```

### Bash alias manager

[alias_manager.py](alias_manager.py)

A small interface for viewing, adding, editing, and removing aliases in `~/.bash_aliases`. It shows the alias name, command, and description, and can copy aliases or commands to the clipboard.

**Needs:** pyperclip and Tkinter. It works with Bash aliases.

File handling is in `read_aliases`, `write_alias`, and `remove_alias_from_file`. The interface is built in `create_gui`, with separate functions for the button actions and context menu.

Back up `~/.bash_aliases` before trying changes. The “open terminal” action assumes a command named `terminal` is available on your system.

```sh
.venv/bin/python alias_manager.py
```

### FlatTrash

[FlatTrash.py](FlatTrash.py)

A Linux utility for listing installed Flatpak apps and their sizes, uninstalling apps, and checking which directories take up space in your home folder. It also has a cache and trash cleanup button.

**Needs:** Tkinter, Flatpak, and the Linux commands used by the script: `du`, `sort`, `head`, and `rm`.

The operations are in `get_flatpaks`, `get_big_dirs`, `uninstall_flatpak`, and `clean_trash_and_cache`. The interface is built at the bottom of the file; `refresh_app_list` updates the app list.

Check the cleanup code before using it: it deletes the contents of `~/.cache` and `~/.local/share/Trash` without asking for confirmation. Flatpak removal does ask, but the app currently reports success without checking the command's exit status.

```sh
.venv/bin/python FlatTrash.py
```

### Password storage experiment

[CofreDeSenhas.py](CofreDeSenhas.py)

Stores service names and passwords locally, using Fernet to encrypt the data. It creates `chave.key` and `senhas.dat` in the working directory.

**Needs:** cryptography and Tkinter.

Storage is handled by `carregar_ou_criar_chave`, `salvar_senhas`, and `carregar_senhas`. The interface is in `CofreGUI`.

This is a learning project: the encryption key is stored alongside the data, and there's no master password. Use dummy passwords when experimenting, and keep both generated files out of any code you share.

```sh
.venv/bin/python CofreDeSenhas.py
```

## Getting started

You'll need Python 3, Tkinter, and a graphical desktop session. The alias manager and FlatTrash depend on Linux. I haven't verified the other programs on other operating systems.

```sh
git clone https://github.com/ZSabia/codex-sabia.git
cd codex-sabia
python3 -m venv .venv
```

Install the packages for whichever program you want to run:

| Program | Command |
| --- | --- |
| Statistics calculator | `.venv/bin/python -m pip install pandas openpyxl` |
| Scheduling simulator | `.venv/bin/python -m pip install numpy matplotlib` |
| Alias manager | `.venv/bin/python -m pip install pyperclip` |
| Password storage experiment | `.venv/bin/python -m pip install cryptography` |
| FlatTrash | No extra Python packages beyond Tkinter |

On Debian/Ubuntu-based distributions, Tkinter and virtual environment support are provided by `python3-tk` and `python3-venv`. Depending on your desktop session, pyperclip may also need a clipboard utility.

## Changing the interface

There isn't a shared layout system or a visual editor here. Each program has its own interface code, in the same file as its logic.

Use the functions mentioned above as starting points. If you replace or rearrange widgets, check their callbacks too. For a bigger rewrite, moving the calculations or system operations into separate modules would make them easier to reuse with another interface.

## License

[MIT](LICENSE).
