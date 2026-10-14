# codex-sabia

A few Python tools I made for my own use and to try out ideas: a statistics calculator, a scheduling simulator, a Twitch client, a nutrition calculator, and some Linux utilities.

Each program runs on its own. Most desktop tools use Tkinter; the Twitch client uses PyQt6, and the nutrition calculator runs in the terminal. If something here is useful to you, feel free to take it apart and make it your own. The layouts are just how I put the first versions together; you can change the colors, move things around, or build a different interface.

## What's here

### Statistics calculator

[CalculadoraEstatistica.py](CalculadoraEstatistica.py)

Calculates sample sizes using either proportions or standard deviation. It keeps a history of results while the app is open and can export them to an Excel file in the working directory.

**Needs:** pandas, openpyxl, and Tkinter.

The calculations are in `formula_amostra_proporcao`, `formula_amostra_desvio`, and the calculation methods in `CalculadoraEstatistica`. For the layout, start with `_configurar_janela`, `_criar_grupo_formula`, and `_criar_interface`. Excel export is handled by `_exportar_resultados`.

```sh
.venv/bin/python CalculadoraEstatistica.py
```

### CPU Scheduling simulator

[SimuladorDeEscalonamentoV2.py](SimuladorDeEscalonamentoV2.py)

Add processes with execution times, priorities, and arrival times, then compare FIFO, SJF, priority scheduling, and Round Robin. The app displays Gantt charts, calculates waiting and turnaround times, and lets you export the charts.

**Needs:** NumPy, Matplotlib, and Tkinter.

The scheduling code is in `simular_execucao`, `round_robin`, `sjf`, and `prioridade`, inside `SchedulerApp`. Metrics are calculated in `calcular_tme_tmp`. The interface and charts are built in `setup_ui`, `configurar_tema`, `criar_seletor_tema`, and `gerar_gantt`.

The button labeled “IA” generates random example processes. It doesn't use an AI model.

```sh
.venv/bin/python SimuladorDeEscalonamentoV2.py
```

### Fish alias manager

[alias_manager.py](alias_manager.py)

A small interface for viewing, adding, editing, and removing aliases in `~/.config/fish/conf.d/aliases.fish`. It shows the alias name, command, and description, and can copy aliases or commands to the clipboard.

**Needs:** pyperclip and Tkinter. It works with Fish aliases and opens new sessions in gnome-terminal.

File handling is in `read_aliases`, `write_alias`, and `remove_alias_from_file`. The interface is built in `create_gui`, with separate functions for the button actions and context menu.

Back up your alias file before trying changes. The editor defaults to `gedit`; set `EDITOR` to use another one. The alias file is created when you first add an alias.

```sh
.venv/bin/python alias_manager.py
```

### FlatTrash

[FlatTrash.py](FlatTrash.py)

A Linux utility for listing installed Flatpak apps and their sizes, uninstalling apps, and checking which directories take up space in your home folder. It also has a cache and trash cleanup button.

**Needs:** Tkinter, Flatpak, and the Linux commands used by the script: `du`, `sort`, `head`, and `rm`.

The operations are in `get_flatpaks`, `get_big_dirs`, `uninstall_flatpak`, and `clean_trash_and_cache`. The interface is built at the bottom of the file; `refresh_app_list` updates the app list.

Cleanup asks for confirmation before deleting the contents of `~/.cache` and `~/.local/share/Trash`. Close your apps first. Flatpak removal also asks for confirmation and reports command failures.

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

### SabiáCast — unofficial client for Twitch

[sabiacast.py](sabiacast.py) · [sabiacast.sh](sabiacast.sh)

SabiáCast is an independent personal project. It is not affiliated with, sponsored by, or endorsed by Twitch Interactive, Inc. Twitch is a trademark of Twitch Interactive, Inc.

I made this because I wanted to watch Twitch without ads, without paying for a subscription, and with as little delay as possible.

The app opens streams in tabs, lets you search live channels and browse followed streams, and includes chat with Twitch, BTTV, FFZ, and 7TV emotes. Video playback uses Streamlink and VLC; the interface uses PyQt6.

Streamlink filters embedded ads automatically, but playback can pause while an ad is running. The app enables low-latency streaming; “zero delay” is the goal, rather than a guarantee. See [Streamlink’s Twitch notes](https://streamlink.github.io/cli/plugins/twitch.html) for how ad filtering and latency work.

**Needs:** PyQt6, requests, streamlink, python-vlc, and VLC/libVLC installed on the system. Internet access and your own Twitch Client ID and user access token are required. Features depend on the permissions of that token.

`TwitchApp.init_ui` builds the main window; `StreamTab.init_ui` builds each stream tab. Playback starts in `_resolve_and_play`, and `IRCClient` handles chat over TLS.

```sh
bash sabiacast.sh
```

The launcher creates a separate `.venv-twitch` environment and checks `requirements-twitch.txt` on each run. It adds that environment to `PATH` so the app can find the Streamlink command. Set `TWITCH_APP_VENV` to choose another environment.

Credentials are saved locally in `~/.twitch_app_credentials.json` with owner-only permissions. They are not encrypted. Emotes are cached in `emotes_cache` in the working directory. Neither belongs in a commit. The login dialog links to a third-party token generator; review the permissions you grant before using it.

### Nutrition calculator

[tabelaNutricionalV2.py](tabelaNutricionalV2.py) · [alimentos_taco_597.csv](alimentos_taco_597.csv)

A terminal exercise based on the Brazilian TACO food composition table, fourth edition (NEPA/UNICAMP, 2011). Search for foods, enter portions in grams, and calculate totals for carbohydrates, protein, fat, sodium, and a simplified protein utilization estimate.

**Needs:** Python 3 and the CSV in the same directory as the script. No extra Python packages or graphical desktop are needed.

```sh
python3 tabelaNutricionalV2.py
```

The prompts are in Portuguese: enter a food name and its weight, use `info` to inspect a food, and `fim` to finish. Search is handled by `buscar_alimentos` and `localizar_alimento`; `calcular_totais` scales the values per 100 g to the chosen portions. `main` and `imprimir_resultado` handle terminal interaction.

The protein utilization factors are exercise assumptions, not values supplied by TACO. Missing values and trace amounts are treated as zero, and categories for mixed foods are approximate. The dataset's source is TACO; the repository's MIT license applies to the code, not a claim of ownership over the source table.

### Tibia update repair

[fix-tibia.sh](fix-tibia.sh)

This wraps an existing community workaround for a Tibia update error on Linux. When I looked for a fix, I found long command sequences to copy and run, but no ready-to-run script. I put those steps into one so they would be easier to use; the workaround itself is not my discovery.

The script asks before closing Tibia, backs up `characterdata` and `minimap`, removes specific package directories and metadata, then starts the launcher to download them again.

```sh
bash fix-tibia.sh
# If your launcher is elsewhere:
bash fix-tibia.sh "/path/to/Tibia"
```

The defaults are `$HOME/Games/Tibia` for the launcher and `$HOME/.local/share/CipSoft GmbH/Tibia/packages/Tibia` for package data. Set `TIBIA_GAME_DIR` and `TIBIA_DATA_DIR` to change them.

Backups go into `${XDG_STATE_HOME:-$HOME/.local/state}/tibia-backups`, each in its own directory. A failed backup stops the script before deletion. This helper is intended for that package layout; it isn't a general repair tool for every Tibia installation.

**Needs:** Bash and the commands used in the script: `pkill`, `pgrep`, `sleep`, `mkdir`, `mktemp`, `cp`, and `rm`, plus the installed Tibia launcher. Deleted game files must be downloaded again.

## Getting started

You'll need Python 3, Tkinter, and a graphical desktop session. The alias manager, FlatTrash, and Tibia helper depend on Linux. I haven't verified the other programs on other operating systems.

```sh
git clone https://github.com/ZSabia/codex-sabia.git
cd codex-sabia
python3 -m venv .venv
```

For all the original desktop utilities, run `.venv/bin/python -m pip install -r requirements.txt`. Or install only what you need:

| Program | Command |
| --- | --- |
| Statistics calculator | `.venv/bin/python -m pip install pandas openpyxl` |
| Scheduling simulator | `.venv/bin/python -m pip install numpy matplotlib` |
| Alias manager | `.venv/bin/python -m pip install pyperclip` |
| Password storage experiment | `.venv/bin/python -m pip install cryptography` |
| FlatTrash | No extra Python packages beyond Tkinter |
| SabiáCast | `.venv/bin/python -m pip install -r requirements-twitch.txt` (also requires VLC) |
| Nutrition calculator | Python standard library only |

On Debian/Ubuntu-based distributions, Tkinter and virtual environment support are provided by `python3-tk` and `python3-venv`. Depending on your desktop session, pyperclip may also need a clipboard utility.

## Changing the interface

There isn't a shared layout system or a visual editor here. Each program has its own interface code, in the same file as its logic. The nutrition calculator has a text interface; the Tibia helper is a shell script.

Use the functions mentioned above as starting points. If you replace or rearrange widgets, check their callbacks too. For a bigger rewrite, moving the calculations or system operations into separate modules would make them easier to reuse with another interface.

## License

Code: [MIT](LICENSE). Nutritional data is attributed to TACO/NEPA/UNICAMP separately.
