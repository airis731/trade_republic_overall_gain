import pandas as pd
import os
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox

def calculate_realized_gains(df):
    # Filter for only Buy and Sell orders
    trades = df[df['type'].isin(['BUY', 'SELL'])].copy()
    
    # Sort chronologically to ensure FIFO works correctly
    trades['datetime'] = pd.to_datetime(trades['datetime'])
    trades = trades.sort_values(by=['datetime'])
    
    open_lots = {} 
    sell_reports = [] 
    cumulative_pnl = 0.0  # Track running total of realized gains
    
    for _, row in trades.iterrows():
        sym = row['symbol']
        if pd.isna(sym):
            continue
            
        date = row['date']
        name = row['name']
        shares = abs(float(row['shares']))
        price = float(row['price'])
        
        # Safely extract fees and taxes
        fee = abs(float(row['fee'])) if pd.notna(row['fee']) else 0.0
        tax = abs(float(row['tax'])) if pd.notna(row['tax']) else 0.0
        
        if row['type'] == 'BUY':
            if sym not in open_lots:
                open_lots[sym] = []
                
            open_lots[sym].append({
                'date': date,
                'shares': shares,
                'price': price,
                'fee_per_share': fee / shares if shares > 0 else 0,
                'tax_per_share': tax / shares if shares > 0 else 0
            })
            
        elif row['type'] == 'SELL':
            shares_to_sell = shares
            sell_proceeds = shares * price
            sell_costs = fee + tax
            
            cost_basis = 0.0
            matched_buys = []
            
            if sym in open_lots:
                while shares_to_sell > 0 and len(open_lots[sym]) > 0:
                    lot = open_lots[sym][0]
                    
                    if lot['shares'] <= shares_to_sell:
                        shares_used = lot['shares']
                        cost_basis += (shares_used * lot['price']) + (shares_used * lot['fee_per_share']) + (shares_used * lot['tax_per_share'])
                        matched_buys.append(f"{shares_used:.4f} shrs from {lot['date']} @ €{lot['price']:.2f}")
                        
                        shares_to_sell -= shares_used
                        open_lots[sym].pop(0) 
                    else:
                        shares_used = shares_to_sell
                        cost_basis += (shares_used * lot['price']) + (shares_used * lot['fee_per_share']) + (shares_used * lot['tax_per_share'])
                        matched_buys.append(f"{shares_used:.4f} shrs from {lot['date']} @ €{lot['price']:.2f}")
                        
                        lot['shares'] -= shares_used
                        shares_to_sell = 0
            
            net_profit = sell_proceeds - cost_basis - sell_costs
            cumulative_pnl += net_profit  # Add to running total
            
            sell_reports.append({
                'date': date,
                'name': name,
                'symbol': sym,
                'shares_sold': shares,
                'sell_price': price,
                'net_profit': net_profit,
                'cumulative_pnl': cumulative_pnl, # Store the cumulative amount at this point in time
                'matched_buys': matched_buys
            })

    return sell_reports, open_lots

def build_gui(df, sell_reports, open_lots):
    """Creates the color-coded, user-friendly UI window."""
    root = tk.Tk()
    root.title("Trade Republic - Portfolio Performance")
    root.geometry("900x750")
    root.configure(bg="#121212")

    # --- CALCULATE PORTFOLIO METRICS ---
    # Total cash balance (sum of all amounts + fees + taxes)
    uninvested_cash = df['amount'].fillna(0).sum() + df['fee'].fillna(0).sum() + df['tax'].fillna(0).sum()
    
    # Calculate cost basis of currently held shares
    invested_value = 0.0
    for sym, lots in open_lots.items():
        for lot in lots:
            invested_value += (lot['shares'] * lot['price']) + (lot['shares'] * lot['fee_per_share']) + (lot['shares'] * lot['tax_per_share'])
            
    total_portfolio_cost = uninvested_cash + invested_value
    
    # Calculate passive income
    dividends = df[df['type'] == 'DIVIDEND']['amount'].fillna(0).sum() + df[df['type'] == 'DIVIDEND']['tax'].fillna(0).sum()
    interest = df[df['type'].isin(['INTEREST_PAYMENT', 'EARNINGS'])]['amount'].fillna(0).sum() + df[df['type'].isin(['INTEREST_PAYMENT', 'EARNINGS'])]['tax'].fillna(0).sum()
    tax_opt = df[df['type'].isin(['TAX_OPTIMIZATION', 'SEC_ACCOUNT'])]['tax'].fillna(0).sum()
    passive_income = dividends + interest + tax_opt

    # --- TOP FRAME: DASHBOARD SUMMARY ---
    summary_frame = tk.Frame(root, bg="#1e1e1e", pady=15, padx=20)
    summary_frame.pack(fill="x", padx=15, pady=15)

    def add_stat(frame, label_text, value, row, col, is_profit=False):
        tk.Label(frame, text=label_text, bg="#1e1e1e", fg="#a0a0a0", font=("Segoe UI", 10)).grid(row=row, column=col, sticky="w", padx=(0, 20))
        
        val_color = "#ffffff"
        if is_profit:
            val_color = "#4caf50" if value >= 0 else "#f44336"
            
        sign = "+" if is_profit and value > 0 else ""
        formatted_val = f"{sign}€{value:,.2f}"
        
        tk.Label(frame, text=formatted_val, bg="#1e1e1e", fg=val_color, font=("Segoe UI", 12, "bold")).grid(row=row, column=col+1, sticky="w", padx=(0, 40), pady=3)

    add_stat(summary_frame, "Uninvested Cash:", uninvested_cash, 0, 0)
    add_stat(summary_frame, "Invested Assets (Cost Basis):", invested_value, 1, 0)
    add_stat(summary_frame, "Total Account Value (Cost Basis):", total_portfolio_cost, 2, 0)

    final_realized = sell_reports[-1]['cumulative_pnl'] if sell_reports else 0.0
    add_stat(summary_frame, "Net Realized Trading PnL:", final_realized, 0, 2, is_profit=True)
    add_stat(summary_frame, "Dividends, Interest & Tax Opt:", passive_income, 1, 2, is_profit=True)
    add_stat(summary_frame, "Total Wealth Generated:", final_realized + passive_income, 2, 2, is_profit=True)

    # --- BOTTOM FRAME: TRANSACTION LOG ---
    log_frame = tk.Frame(root, bg="#121212")
    log_frame.pack(expand=True, fill="both", padx=15, pady=(0, 15))

    tk.Label(log_frame, text="Realized Gains History (FIFO)", bg="#121212", fg="#ffffff", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 5))

    # Create ScrolledText widget
    text_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, font=("Consolas", 10), bg="#1e1e1e", fg="#d4d4d4", selectbackground="#333333", borderwidth=0)
    text_area.pack(expand=True, fill="both")

    # Define color tags for eye-friendly text
    text_area.tag_config("header", foreground="#64b5f6", font=("Consolas", 10, "bold"))
    text_area.tag_config("normal", foreground="#b0b0b0")
    text_area.tag_config("profit", foreground="#4caf50")
    text_area.tag_config("loss", foreground="#f44336")
    text_area.tag_config("cum_profit", foreground="#81c784", font=("Consolas", 10, "bold"))
    text_area.tag_config("cum_loss", foreground="#e57373", font=("Consolas", 10, "bold"))

    # Insert transactions into the text area
    for report in sell_reports:
        # Header line
        text_area.insert(tk.INSERT, f"\n[SOLD] {report['date']} | {report['name']} ({report['symbol']})\n", "header")
        text_area.insert(tk.INSERT, f"       Sold: {report['shares_sold']} shares @ €{report['sell_price']:.2f}\n", "normal")
        text_area.insert(tk.INSERT, f"       Matched against buys:\n", "normal")
        
        for buy in report['matched_buys']:
            text_area.insert(tk.INSERT, f"         -> {buy}\n", "normal")
            
        # PnL Line
        pnl = report['net_profit']
        pnl_tag = "profit" if pnl >= 0 else "loss"
        pnl_sign = "+" if pnl > 0 else ""
        text_area.insert(tk.INSERT, f"       Trade PnL:       {pnl_sign}€{pnl:.2f}\n", pnl_tag)

        # Cumulative Line
        cum_pnl = report['cumulative_pnl']
        cum_tag = "cum_profit" if cum_pnl >= 0 else "cum_loss"
        cum_sign = "+" if cum_pnl > 0 else ""
        text_area.insert(tk.INSERT, f"       Cumulative PnL:  {cum_sign}€{cum_pnl:.2f}\n", cum_tag)
        
        text_area.insert(tk.INSERT, "       " + ("-" * 60) + "\n", "normal")

    text_area.configure(state='disabled') # Make read-only
    root.mainloop()

def main():
    # 1. Create a temporary hidden window to launch the file picker
    temp_root = tk.Tk()
    temp_root.withdraw() 
    
    # 2. Open the file picker dialog
    file_path = filedialog.askopenfilename(
        title="Select your Trade Republic CSV File",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
    )
    
    # Destroy the temporary window after a file is selected (or canceled)
    temp_root.destroy()
    
    # 3. Check if the user clicked "Cancel"
    if not file_path:
        print("No file selected. Exiting program...")
        return
        
    try:
        # Load the selected file
        df = pd.read_csv(file_path)
    except Exception as e:
        # If the file is corrupted or not a valid CSV, show an error box
        error_root = tk.Tk()
        error_root.withdraw()
        messagebox.showerror("Error", f"Could not read the file:\n\n{e}")
        return

    # Calculate Data
    sell_reports, open_lots = calculate_realized_gains(df)
    
    # Launch GUI
    build_gui(df, sell_reports, open_lots)

if __name__ == '__main__':
    main()
