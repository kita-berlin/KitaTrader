"""
Comprehensive OHLCV Verification Script
Tests: Ticks, M1, H1, H3, and Daily bars for Summer and Winter periods
"""
import os
import subprocess
import time
from datetime import datetime

# Test configurations
TESTS = [
    # Summer tests (EDT, UTC-4)
    {
        "name": "Summer_Ticks",
        "season": "Summer",
        "start": "22/07/2025",
        "end": "25/07/2025",
        "period": "m1",  # Use M1 for tick data mode
        "timeframe": 0,  # 0 = ticks in Python
        "py_log": "PriceVerify_Python_Summer_Ticks.csv",
        "cs_log": "PriceVerify_CSharp_Summer_Ticks.txt"
    },
    {
        "name": "Summer_M1",
        "season": "Summer",
        "start": "22/07/2025",
        "end": "25/07/2025",
        "period": "m1",
        "timeframe": 60,
        "py_log": "PriceVerify_Python_Summer_M1.csv",
        "cs_log": "PriceVerify_CSharp_Summer_M1.txt"
    },
    {
        "name": "Summer_H1",
        "season": "Summer",
        "start": "22/07/2025",
        "end": "25/07/2025",
        "period": "h1",
        "timeframe": 3600,
        "py_log": "PriceVerify_Python_Summer_H1.csv",
        "cs_log": "PriceVerify_CSharp_Summer_H1.txt"
    },
    {
        "name": "Summer_H3",
        "season": "Summer",
        "start": "22/07/2025",
        "end": "25/07/2025",
        "period": "h3",
        "timeframe": 10800,
        "py_log": "PriceVerify_Python_Summer_H3.csv",
        "cs_log": "PriceVerify_CSharp_Summer_H3.txt"
    },
    {
        "name": "Summer_Daily",
        "season": "Summer",
        "start": "22/07/2025",
        "end": "25/07/2025",
        "period": "d1",
        "timeframe": 86400,
        "py_log": "PriceVerify_Python_Summer_D1.csv",
        "cs_log": "PriceVerify_CSharp_Summer_D1.txt"
    },
    # Winter tests (EST, UTC-5)
    {
        "name": "Winter_Ticks",
        "season": "Winter",
        "start": "15/01/2025",
        "end": "18/01/2025",
        "period": "m1",
        "timeframe": 0,
        "py_log": "PriceVerify_Python_Winter_Ticks.csv",
        "cs_log": "PriceVerify_CSharp_Winter_Ticks.txt"
    },
    {
        "name": "Winter_M1",
        "season": "Winter",
        "start": "15/01/2025",
        "end": "18/01/2025",
        "period": "m1",
        "timeframe": 60,
        "py_log": "PriceVerify_Python_Winter_M1.csv",
        "cs_log": "PriceVerify_CSharp_Winter_M1.txt"
    },
    {
        "name": "Winter_H1",
        "season": "Winter",
        "start": "15/01/2025",
        "end": "18/01/2025",
        "period": "h1",
        "timeframe": 3600,
        "py_log": "PriceVerify_Python_Winter_H1.csv",
        "cs_log": "PriceVerify_CSharp_Winter_H1.txt"
    },
    {
        "name": "Winter_H3",
        "season": "Winter",
        "start": "15/01/2025",
        "end": "18/01/2025",
        "period": "h3",
        "timeframe": 10800,
        "py_log": "PriceVerify_Python_Winter_H3.csv",
        "cs_log": "PriceVerify_CSharp_Winter_H3.txt"
    },
    {
        "name": "Winter_Daily",
        "season": "Winter",
        "start": "15/01/2025",
        "end": "18/01/2025",
        "period": "d1",
        "timeframe": 86400,
        "py_log": "PriceVerify_Python_Winter_D1.csv",
        "cs_log": "PriceVerify_CSharp_Winter_D1.txt"
    }
]

CTRADER_CLI = r"C:\Users\HMz\AppData\Local\Spotware\cTrader\abb70432efbee65d18af69e79fe8efe1\ctrader-cli.exe"
ROBOT_ALGO = r"C:\Users\HMz\Documents\cAlgo\Sources\Robots\PriceVerifyBot\bin\Release\net6.0\Robots.algo"
PWD_FILE = r"C:\Users\HMz\Documents\Source\cTraderTools\Apps\PyDownload\password.txt"
LOG_DIR = r"C:\Users\HMz\Documents\cAlgo\Logfiles"

def update_python_config(test):
    """Update MainConsole.py and PriceVerifyBot.py for the test"""
    # Parse dates
    start_parts = test["start"].split("/")
    end_parts = test["end"].split("/")
    start_date = f"{start_parts[0]}.{start_parts[1]}.{start_parts[2]}"
    end_date = f"{end_parts[0]}.{end_parts[1]}.{end_parts[2]}"
    
    # Update MainConsole.py
    main_console_path = r"C:\Users\HMz\Documents\Source\KitaTrader\MainConsole.py"
    with open(main_console_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace date lines
    import re
    content = re.sub(
        r'self\.robot\.AllDataStartUtc = datetime\.strptime\(".*?", "%d\.%m\.%Y"\)',
        f'self.robot.AllDataStartUtc = datetime.strptime("{start_date}", "%d.%m.%Y")',
        content
    )
    content = re.sub(
        r'self\.robot\.AllDataEndUtc = datetime\.strptime\(".*?", "%d\.%m\.%Y"\)',
        f'self.robot.AllDataEndUtc = datetime.strptime("{end_date}", "%d.%m.%Y")',
        content
    )
    content = re.sub(
        r'self\.robot\.BacktestStartUtc = datetime\.strptime\(".*?", "%d\.%m\.%Y"\)',
        f'self.robot.BacktestStartUtc = datetime.strptime("{start_date}", "%d.%m.%Y")',
        content
    )
    content = re.sub(
        r'self\.robot\.BacktestEndUtc = datetime\.strptime\(".*?", "%d\.%m\.%Y"\)',
        f'self.robot.BacktestEndUtc = datetime.strptime("{end_date}", "%d.%m.%Y")',
        content
    )
    
    with open(main_console_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Update PriceVerifyBot.py
    bot_path = r"C:\Users\HMz\Documents\Source\KitaTrader\Robots\PriceVerifyBot.py"
    with open(bot_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update log file name
    content = re.sub(
        r'log_path = os\.path\.join\(log_dir, ".*?"\)',
        f'log_path = os.path.join(log_dir, "{test["py_log"]}")',
        content
    )
    
    # Update timeframe
    content = re.sub(
        r'self\.active_symbol\.request_bars\(\d+\)',
        f'self.active_symbol.request_bars({test["timeframe"]})',
        content
    )
    content = re.sub(
        r'err, bars = symbol\.get_bars\(\d+\)',
        f'err, bars = symbol.get_bars({test["timeframe"]})',
        content
    )
    
    with open(bot_path, 'w', encoding='utf-8') as f:
        f.write(content)

def run_csharp_test(test):
    """Run C# backtest"""
    print(f"  Running C# backtest...")
    cmd = [
        CTRADER_CLI,
        "backtest",
        ROBOT_ALGO,
        f"--start={test['start']}",
        f"--end={test['end']}",
        "--data-mode=ticks",
        "--balance=10000",
        "--commission=0",
        "--spread=0",
        "--ctid=Quantrosoft",
        f"--pwd-file={PWD_FILE}",
        "--account=5166098",
        "--symbol=AUDNZD",
        f"--period={test['period']}"
    ]
    
    output_file = os.path.join(LOG_DIR, test["cs_log"])
    with open(output_file, 'w') as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, text=True)
    
    return result.returncode == 0

def run_python_test(test):
    """Run Python backtest"""
    print(f"  Running Python backtest...")
    result = subprocess.run(
        ["python", "MainConsole.py"],
        cwd=r"C:\Users\HMz\Documents\Source\KitaTrader",
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def compare_logs(test):
    """Compare C# and Python logs"""
    print(f"  Comparing logs...")
    # Update compare_logs.py to point to current test files
    compare_script = r"C:\Users\HMz\Documents\Source\KitaTrader\compare_logs.py"
    with open(compare_script, 'r', encoding='utf-8') as f:
        content = f.read()
    
    import re
    content = re.sub(
        r'c_data = parse_csharp_log\(r".*?"\)',
        f'c_data = parse_csharp_log(r"{os.path.join(LOG_DIR, test["cs_log"])}")',
        content
    )
    content = re.sub(
        r'p_data = parse_python_log\(r".*?"\)',
        f'p_data = parse_python_log(r"{os.path.join(LOG_DIR, test["py_log"])}")',
        content
    )
    
    with open(compare_script, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Run comparison
    result = subprocess.run(
        ["python", "compare_logs.py"],
        cwd=r"C:\Users\HMz\Documents\Source\KitaTrader",
        capture_output=True,
        text=True
    )
    
    return "SUCCESS" in result.stdout, result.stdout

def main():
    print("=" * 80)
    print("COMPREHENSIVE OHLCV VERIFICATION")
    print("=" * 80)
    print()
    
    results = []
    
    for test in TESTS:
        print(f"\n[{test['name']}] Testing {test['season']} - {test['period'].upper()}")
        print("-" * 80)
        
        try:
            # Update configurations
            print(f"  Configuring test...")
            update_python_config(test)
            
            # Run C# test
            cs_success = run_csharp_test(test)
            if not cs_success:
                print(f"  ❌ C# backtest failed")
                results.append((test['name'], False, "C# backtest failed"))
                continue
            
            # Run Python test
            py_success = run_python_test(test)
            if not py_success:
                print(f"  ❌ Python backtest failed")
                results.append((test['name'], False, "Python backtest failed"))
                continue
            
            # Compare results
            success, output = compare_logs(test)
            if success:
                print(f"  ✅ PASSED - Logs match perfectly")
                results.append((test['name'], True, "SUCCESS"))
            else:
                print(f"  ⚠️  FAILED - Logs differ")
                print(f"     {output[:200]}")
                results.append((test['name'], False, "Logs differ"))
            
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            results.append((test['name'], False, f"Error: {str(e)}"))
        
        # Small delay between tests
        time.sleep(2)
    
    # Print summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10} | {name:25} | {message}")
    
    print("-" * 80)
    print(f"Results: {passed}/{total} tests passed ({100*passed//total if total > 0 else 0}%)")
    print("=" * 80)

if __name__ == "__main__":
    main()
