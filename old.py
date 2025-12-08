import tkinter as tk
from tkinter import ttk
from strategies.buy_and_hold import BuyAndHold
from strategies.pairs_trading import PairsTradingStrategy
from strategies.markowitz import Markowitz
import config
import importlib
import json
import os
import sys
import tkinter.scrolledtext as scrolledtext


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


class TextRedirector:
    def __init__(self, widget, tag):
        self.widget = widget
        self.tag = tag
        self.terminal = sys.__stdout__

    def write(self, message):
        self.widget.configure(state='normal')
        self.widget.insert('end', message)
        self.widget.configure(state='disabled')
        self.widget.see('end')  # scroll auto
        self.terminal.write(message)
        
    def flush(self):
        pass  # nécessaire pour compatibilité avec stdout
    

class StrategyApp:
    def __init__(self, root):
        self.root = root
        self.general_config = self.load_json_config("general.json")
        self.buy_and_hold_config = self.load_json_config("buy_and_hold.json")
        self.pairs_trading_config = self.load_json_config("pairs_trading.json")
        self.markowitz_config = self.load_json_config("markowitz.json")
        self.root.title("Backtesteur de Stratégies")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both')

        self.param_frame = self.create_param_tab()
        self.strategy_tabs = {}
        self.benchmark_vars = {}
        self.plot_vars = {}

        self.create_strategy_tab("Buy & Hold", BuyAndHold)
        self.create_strategy_tab("Pairs Trading", PairsTradingStrategy)
        self.create_strategy_tab("Markowitz", Markowitz)
        
        self.console_output = scrolledtext.ScrolledText(self.root, height=15, state='disabled', wrap='word')
        self.console_output.pack(side="bottom", fill='x', padx=5, pady=5)

        sys.stdout = TextRedirector(self.console_output, "stdout")
        sys.stderr = TextRedirector(self.console_output, "stderr")


    def create_param_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Paramètres")

        inner = ttk.Frame(frame)
        inner.pack(expand=True)
    
        self.start_var = tk.StringVar(value=self.general_config["start_date"])
        self.end_var = tk.StringVar(value=self.general_config["end_date"])
        self.capital_var = tk.StringVar(value=str(self.general_config["capital"]))
        self.fee_rate_var = tk.StringVar(value=str(self.general_config["fee_rate"]*100))
        self.slippage_var = tk.StringVar(value=str(self.general_config["slippage"]*100))
    
        def on_change_start(*_):  # *_ ignore les args inutiles
            self.general_config["start_date"] = self.start_var.get()
            self.save_json_config(self.general_config, "general.json")

        def on_change_end(*_):
            self.general_config["end_date"] = self.end_var.get()
            self.save_json_config(self.general_config, "general.json")

        def on_change_capital(*_):
            self.general_config["capital"] = float(self.capital_var.get())
            self.save_json_config(self.general_config, "general.json")
            
        def on_change_fee_rate(*_):
            self.general_config["fee_rate"] = float(self.fee_rate_var.get())/100
            self.save_json_config(self.general_config, "general.json")    
        
        def on_change_slippage(*_):
            self.general_config["slippage"] = float(self.slippage_var.get())/100
            self.save_json_config(self.general_config, "general.json") 
        
        self.start_var.trace_add("write", on_change_start)
        self.end_var.trace_add("write", on_change_end)
        self.capital_var.trace_add("write", on_change_capital) 
        self.fee_rate_var.trace_add("write", on_change_fee_rate)
        self.slippage_var.trace_add("write", on_change_slippage) 
    
        ttk.Label(inner, text="Date de début:").grid(row=0, column=0, sticky='e', padx=10, pady=5)
        ttk.Entry(inner, textvariable=self.start_var, width=20).grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(inner, text="Date de fin:").grid(row=1, column=0, sticky='e', padx=10, pady=5)
        ttk.Entry(inner, textvariable=self.end_var, width=20).grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(inner, text="Capital initial:").grid(row=2, column=0, sticky='e', padx=10, pady=5)
        ttk.Entry(inner, textvariable=self.capital_var, width=20).grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(inner, text="Frais de transactions (%):").grid(row=3, column=0, sticky='e', padx=10, pady=5)
        ttk.Entry(inner, textvariable=self.fee_rate_var, width=20).grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Label(inner, text="Glissement (%):").grid(row=4, column=0, sticky='e', padx=10, pady=5)
        ttk.Entry(inner, textvariable=self.slippage_var, width=20).grid(row=4, column=1, padx=10, pady=5)

        return frame

    def create_strategy_tab(self, name, strategy_class):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=name)
        # En-tête avec nom + bouton paramètres
        header = ttk.Frame(frame)
        header.pack(fill="x", pady=5, padx=5)

        # Bouton avec icône crantée
        param_button = ttk.Button(header, text="⚙️", width=3)
        param_button.pack(side="right")

        ttk.Label(frame, text=f"Lancer la stratégie {name}:").pack(pady=5)
        
        if name == "Buy & Hold":
            plot_attr = "SHOW_PLOT_BUYANDHOLD"
        elif name == "Pairs Trading":
            plot_attr = "SHOW_PLOT_PAIRSTRADING"  
        elif name == "Markowitz":
            plot_attr = "SHOW_PLOT_MARKOWITZ"  
        
        plot_var = tk.BooleanVar(value=getattr(config, plot_attr, False))
        self.plot_vars[name] = plot_var
        ttk.Checkbutton(frame, text="Afficher le plot", variable=plot_var).pack()
        

        if name == "Buy & Hold":
            param_button.config(command=self.open_buy_and_hold_settings)
            ttk.Label(frame, text="Preset:").pack()
            last_preset = self.buy_and_hold_config.get("buy_and_hold_preset", "balanced")
            preset_var = tk.StringVar(value=last_preset)

            def on_change_preset(*_):
                self.buy_and_hold_config["buy_and_hold_preset"] = preset_var.get()
                self.save_json_config(self.buy_and_hold_config, "buy_and_hold.json")

            preset_var.trace_add("write", on_change_preset)

            preset_menu = ttk.Combobox(frame, textvariable=preset_var, values=list(self.buy_and_hold_config["portfolio_presets"].keys()))
            preset_menu.pack()
            
            def launch():
                importlib.reload(config)
                preset = preset_var.get()
                strategy = strategy_class(preset=preset)
                strategy.run_backtest(plot=plot_var.get())


        elif name == "Pairs Trading":
            param_button.config(command=self.open_pairs_trading_settings)
            last_pair = self.pairs_trading_config.get("pair",())
            pair_var = tk.StringVar(value=last_pair)

            def on_change_pair(*_):
                self.pairs_trading_config["pairs_trading_pair"] = pair_var.get()
                self.save_json_config(self.pairs_trading_config, "pairs_trading.json")

            pair_var.trace_add("write", on_change_pair)

            ttk.Label(frame, text="Paire:").pack()
            ttk.Entry(frame, textvariable=pair_var).pack()

            def launch():
                importlib.reload(config)

                pair_input = pair_var.get().strip()
                try:
                    symbols = [s.strip().upper() for s in pair_input.split(",")]
                    if len(symbols) != 2:
                        raise ValueError
                    pair = tuple(symbols)
                except ValueError:
                    tk.messagebox.showerror("Erreur", "Veuillez entrer deux symboles séparés par une virgule.")
                    return

                self.pairs_trading_config["pair"] = pair_input
                self.save_json_config(self.pairs_trading_config, "pairs_trading.json")

                strategy = strategy_class(pair)
                strategy.run_backtest(plot=plot_var.get())


        elif name == "Markowitz":
            param_button.config(command=self.open_markowitz_settings)
            ttk.Label(frame, text="Actifs à inclure :").pack()

            # Dernière sélection enregistrée
            selected_assets = self.markowitz_config.get("assets",[])
            self.markowitz_vars = {asset: tk.BooleanVar(value=(asset in selected_assets)) for asset in self.markowitz_config["asset_pool"]}

            def open_asset_selector():
                top = tk.Toplevel(self.root)
                top.title("Sélection des actifs")

                ASSET_CATEGORIES = {
                    "Indices US": {
                        "SPY": "S&P 500",
                        "VOO": "S&P 500 (Vanguard)",
                        "VTI": "Marché total US",
                        "IVV": "S&P 500 (iShares)",
                        "QQQ": "Nasdaq-100",
                        "DIA": "Dow Jones",
                        "IWM": "Russell 2000 (small caps)",
                        "RSP": "S&P 500 équipondéré"
                    },
                    "Secteurs US": {
                        "XLK": "Technologie",
                        "XLF": "Finance",
                        "XLV": "Santé",
                        "XLY": "Consommation discrétionnaire",
                        "XLE": "Énergie",
                        "XLI": "Industrie",
                        "XLB": "Matériaux",
                        "XLU": "Services publics",
                        "XLRE": "Immobilier",
                        "XLC": "Communication"
                    },
                    "Smart Beta / Facteurs": {
                        "SPLV": "Volatilité faible",
                        "USMV": "Volatilité minimale",
                        "MTUM": "Momentum",
                        "QUAL": "Qualité",
                        "VIG": "Dividendes croissants",
                        "DVY": "Dividendes élevés",
                        "SPHD": "Rendement élevé + faible volatilité"
                    },
                    "International Développé": {
                        "VEA": "Europe, Japon, etc.",
                        "IEFA": "Pays développés hors US",
                        "ACWI": "Monde développé + émergents",
                        "VT": "Marché mondial total",
                        "VXUS": "Monde hors US"
                    },
                    "Marchés Émergents": {
                        "EEM": "ETF marchés émergents",
                        "VWO": "Large marchés émergents",
                        "IEMG": "ETF émergents (core)",
                        "EMXC": "Émergents hors Chine"
                    },
                    "Obligations US": {
                        "BND": "Obligations agrégées US",
                        "AGG": "US Aggregate Bond Index",
                        "TLT": "Oblig. long terme",
                        "IEF": "Oblig. moyen terme",
                        "SHY": "Oblig. court terme",
                        "LQD": "Oblig. corporate IG",
                        "HYG": "Oblig. haut rendement (junk)"
                    },
                    "Trésorerie / Sans Risque": {
                        "SGOV": "Bons du Trésor 0-3 mois",
                        "BIL": "Treasury Bills 1-3 mois",
                        "SHV": "Obligations ≤ 1 an"
                    },
                    "Matières Premières": {
                        "GLD": "Or",
                        "SLV": "Argent",
                        "DBC": "Panier matières premières",
                        "USO": "Pétrole brut WTI",
                        "DBA": "Agriculture",
                        "PPLT": "Platine",
                        "CPER": "Cuivre"
                    },
                    "Immobilier (REITs)": {
                        "VNQ": "REITs US (Vanguard)",
                        "IYR": "REITs US (iShares)",
                        "SCHH": "REITs US (Schwab)",
                        "REET": "REITs globaux"
                    },
                    "Devises": {
                        "UUP": "Dollar US haussier",
                        "FXE": "Euro haussier",
                        "FXF": "Franc suisse haussier"
                    }
                }


                container = ttk.Frame(top)
                container.pack(padx=20, pady=20)


                col_count = 3
                for i in range(col_count):
                    container.grid_columnconfigure(i, weight=1)  # étale les colonnes

                current_col = 0
                current_row = 0

                for category, assets in ASSET_CATEGORIES.items():
                    lf = ttk.LabelFrame(container, text=category, padding=10)
                    lf.grid(row=current_row, column=current_col, padx=10, pady=10, sticky="nsew")

                    for sym, desc in assets.items():
                        if sym not in self.markowitz_vars:
                            self.markowitz_vars[sym] = tk.BooleanVar(value=False)
                        cb = ttk.Checkbutton(lf, text=f"{sym} – {desc}", variable=self.markowitz_vars[sym])
                        cb.pack(anchor="w")
                        first_valid_dates = self.markowitz_config["start_dates"]
                        start_date = first_valid_dates.get(sym, "Inconnue")
                        ToolTip(cb, f"{start_date}")

                    current_col += 1
                    if current_col >= col_count:
                        current_col = 0
                        current_row += 1

                # Bouton Valider centré
                validate_btn = ttk.Button(container, text="Valider", command=lambda: (
                    self.markowitz_config.update({
                        "assets": [sym for sym, var in self.markowitz_vars.items() if var.get()]
                    }),
                    self.save_json_config(self.markowitz_config, "markowitz.json"),
                    top.destroy()
                ))
                validate_btn.grid(row=current_row + 1, column=0, columnspan=col_count, pady=(20, 0), sticky="ew")

            ttk.Button(frame, text="Choisir les actifs", command=open_asset_selector).pack(pady=5)


            def launch():
                importlib.reload(config)

                selected_assets = [sym for sym, var in self.markowitz_vars.items() if var.get()]
                if not selected_assets:
                    tk.messagebox.showerror("Erreur", "Veuillez sélectionner au moins un actif.")
                    return

                self.markowitz_config["assets"] = selected_assets
                self.save_json_config(self.markowitz_config, "markowitz.json")
                if len(selected_assets) == 1:
                    strategy = BuyAndHold(preset=selected_assets[0])
                else:
                    strategy = strategy_class(selected_assets)
                strategy.run_backtest(plot=plot_var.get())

                
        ttk.Button(frame, text="Lancer le backtest", command=launch).pack(pady=10)
        self.strategy_tabs[name] = frame

    
    def on_markowitz_toggle(self, symbol, var):
        # Met à jour automatiquement assets quand un actif est coché/décoché
        assets = self.markowitz_config.get("assets", [])
        if var.get() and symbol not in assets:
            assets.append(symbol)
        elif not var.get() and symbol in assets:
            assets.remove(symbol)
        self.markowitz_config["assets"] = assets
        self.save_json_config(self.markowitz_config, "markowitz.json")



    def load_json_config(self, filename):
        path = os.path.join("config", filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_json_config(self, data, filename):
        path = os.path.join("config", filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        
if __name__ == "__main__":
    root = tk.Tk()
    app = StrategyApp(root)
    root.mainloop()
    root.geometry("800x600")  # ou "1000x700"
    root.update_idletasks()

    # Centrer la fenêtre à l’écran
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (800 // 2)
    y = (screen_height // 2) - (600 // 2)
    root.geometry(f"800x600+{x}+{y}")
