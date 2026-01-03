
import pandas as pd
import os

def verify_bars():
    log_dir = r"C:\Users\HMz\Documents\cAlgo\Logfiles"
    
    # Python files (Reference)
    fp_m1 = os.path.join(log_dir, "OHLC_Test_Python_M1.csv")
    fp_h1 = os.path.join(log_dir, "OHLC_Test_Python_H1.csv")
    fp_h4 = os.path.join(log_dir, "OHLC_Test_Python_H4.csv")

    # C# Logged files (Target)
    fc_m1 = os.path.join(log_dir, "OHLC_Test_CSharp_M1.csv")
    fc_h1 = os.path.join(log_dir, "OHLC_Test_CSharp_H1.csv")
    fc_h4 = os.path.join(log_dir, "OHLC_Test_CSharp_H4.csv")

    def load_df(path):
        if not os.path.exists(path): 
            print(f"Warning: {path} not found")
            return None
        try:
            df = pd.read_csv(path)
            if df.empty: return None
            df['Time'] = pd.to_datetime(df['Time'])
            df.set_index('Time', inplace=True)
            df = df[~df.index.duplicated(keep='first')]
            return df
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return None

    p_m1, p_h1, p_h4 = load_df(fp_m1), load_df(fp_h1), load_df(fp_h4)
    c_m1, c_h1, c_h4 = load_df(fc_m1), load_df(fc_h1), load_df(fc_h4)

    def fmt(val): return f"{val: .5f}" if isinstance(val, (int, float)) and pd.notnull(val) else "   -   "
    def fmt_v(val): return f"{int(val):>5}" if pd.notnull(val) else "  -  "

    def compare_tfs(tf_name, df_p, df_c):
        if df_p is None or df_c is None: return

        common_times = sorted(set(df_p.index).intersection(set(df_c.index)))
        if not common_times:
            print(f"\n--- {tf_name} No overlapping timestamps found ---")
            return

        print(f"\n--- {tf_name} Comparison (Common Bars: {len(common_times)}) ---")
        print(f"{'Time':<20} | {'PyOpen':<8} {'CsOpen':<8} | {'PyHigh':<8} {'CsHigh':<8} | {'PyLow':<8} {'CsLow':<8} | {'PyCls':<8} {'CsCls':<8} | {'PyVol':<5} {'CsVol':<5} | {'Check'}")
        print("-" * 125)

        for t in common_times:
            row_p = df_p.loc[t]
            row_c = df_c.loc[t]
            
            po, co = row_p['Open'], row_c['Open']
            ph, ch = row_p['High'], row_c['High']
            pl, cl = row_p['Low'], row_c['Low']
            pc, cc = row_p['Close'], row_c['Close']
            pv, cv = row_p['Volume'], row_c['Volume']

            matches_price = abs(po-co) < 1e-6 and abs(ph-ch) < 1e-6 and abs(pl-cl) < 1e-6 and abs(pc-cc) < 1e-6 
            matches_vol = int(pv) == int(cv)
            
            if matches_price and matches_vol:
                check = "MATCH"
            elif not matches_price:
                check = f"DIFF PRC ({abs(po-co):.6f})"
            else:
                check = f"DIFF VOL ({int(pv-cv)})"
            
            print(f"{str(t):<20} | {fmt(po)} {fmt(co)} | {fmt(ph)} {fmt(ch)} | {fmt(pl)} {fmt(cl)} | {fmt(pc)} {fmt(cc)} | {fmt_v(pv)} {fmt_v(cv)} | {check}")

    compare_tfs("M1", p_m1, c_m1)
    compare_tfs("H1", p_h1, c_h1)
    compare_tfs("H4", p_h4, c_h4)

if __name__ == "__main__":
    verify_bars()
