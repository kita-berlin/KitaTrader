"""
Compare indicator values between C# and Python OHLC test logs
Extracts FINAL_IND entries and compares all indicator values
"""
import re
from datetime import datetime
from collections import defaultdict

def parse_python_indicators(log_file):
    """Parse Python log file and extract FINAL_IND entries"""
    indicators = {}
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('FINAL_IND|'):
                # Format: FINAL_IND|TF|TIME|SMA=...|EMA=...|...
                parts = line.strip().split('|')
                if len(parts) >= 4:
                    tf = parts[1]
                    time_str = parts[2]
                    # Filter: Only include indicators from 01.12. to 03.12. (exclude 04.12.)
                    if time_str.startswith('2025-12-04'):
                        continue  # Skip indicators from 04.12.
                    
                    # Parse indicator values from remaining parts
                    ind_values = {}
                    for part in parts[3:]:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            try:
                                ind_values[key] = float(value)
                            except ValueError:
                                pass  # Skip invalid values
                    
                    key = (tf, time_str)
                    indicators[key] = ind_values
    return indicators

def parse_csharp_indicators(log_file):
    """Parse C# log file and extract FINAL_IND entries"""
    indicators = {}
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if 'FINAL_IND|' in line:
                # Format: TIMESTAMP | Info | FINAL_IND|TF|TIME|SMA=...|EMA=...|...
                # Extract the FINAL_IND part
                final_ind_start = line.find('FINAL_IND|')
                if final_ind_start >= 0:
                    final_ind_line = line[final_ind_start:].strip()
                    parts = final_ind_line.split('|')
                    if len(parts) >= 4:
                        tf = parts[1]
                        time_str = parts[2]
                        
                        # Parse indicator values from remaining parts
                        ind_values = {}
                        for part in parts[3:]:
                            if '=' in part:
                                key, value = part.split('=', 1)
                                try:
                                    ind_values[key] = float(value)
                                except ValueError:
                                    pass  # Skip invalid values
                        
                        key = (tf, time_str)
                        indicators[key] = ind_values
    return indicators

def compare_indicators(python_inds, csharp_inds, tolerance=0.00001):
    """Compare indicators from Python and C# logs"""
    # Find common keys (same timeframe and time)
    common_keys = set(python_inds.keys()) & set(csharp_inds.keys())
    python_only = set(python_inds.keys()) - set(csharp_inds.keys())
    csharp_only = set(csharp_inds.keys()) - set(python_inds.keys())
    
    # Get all indicator names
    all_ind_names = set()
    for key in common_keys:
        all_ind_names.update(python_inds[key].keys())
        all_ind_names.update(csharp_inds[key].keys())
    all_ind_names = sorted(all_ind_names)
    
    matches = []
    mismatches = []
    
    for key in sorted(common_keys):
        tf, time_str = key
        py_inds = python_inds[key]
        cs_inds = csharp_inds[key]
        
        # Compare all indicator values
        diffs = {}
        max_diff = 0.0
        all_match = True
        
        for ind_name in all_ind_names:
            py_val = py_inds.get(ind_name)
            cs_val = cs_inds.get(ind_name)
            
            if py_val is None and cs_val is None:
                continue  # Both missing, skip
            elif py_val is None or cs_val is None:
                diffs[ind_name] = None  # One missing
                all_match = False
            else:
                diff = abs(py_val - cs_val)
                diffs[ind_name] = diff
                if diff > max_diff:
                    max_diff = diff
                if diff > tolerance:
                    all_match = False
        
        if all_match and max_diff <= tolerance:
            matches.append({
                'key': key,
                'max_diff': max_diff,
                'diffs': diffs
            })
        else:
            mismatches.append({
                'key': key,
                'python': py_inds,
                'csharp': cs_inds,
                'diffs': diffs,
                'max_diff': max_diff
            })
    
    return {
        'matches': matches,
        'mismatches': mismatches,
        'python_only': python_only,
        'csharp_only': csharp_only,
        'total_common': len(common_keys),
        'total_python': len(python_inds),
        'total_csharp': len(csharp_inds),
        'indicator_names': all_ind_names
    }

def main():
    python_log = r"C:\Users\HMz\Documents\cAlgo\Logfiles\OHLCTestBot_Python.log"
    csharp_log = r"C:\Users\HMz\Documents\cAlgo\Data\cBots\OHLCTestBot\29639f65-52c0-4443-a8c7-b6511867444a\Backtesting\log.txt"
    
    print("=== INDICATOR COMPARISON ===")
    print(f"Python Log: {python_log}")
    print(f"C# Log: {csharp_log}")
    print()
    
    print("Parsing Python indicators...")
    python_inds = parse_python_indicators(python_log)
    print(f"  Found {len(python_inds)} indicator entries")
    
    print("Parsing C# indicators...")
    csharp_inds = parse_csharp_indicators(csharp_log)
    print(f"  Found {len(csharp_inds)} indicator entries")
    print()
    
    print("Comparing indicators...")
    results = compare_indicators(python_inds, csharp_inds)
    
    print(f"=== COMPARISON RESULTS ===")
    print(f"Total Python entries: {results['total_python']}")
    print(f"Total C# entries: {results['total_csharp']}")
    print(f"Common entries: {results['total_common']}")
    print(f"Python-only entries: {len(results['python_only'])}")
    print(f"C#-only entries: {len(results['csharp_only'])}")
    print(f"Matches: {len(results['matches'])}")
    print(f"Mismatches: {len(results['mismatches'])}")
    print()
    
    if results['indicator_names']:
        print(f"Indicators compared: {', '.join(results['indicator_names'])}")
        print()
    
    if results['mismatches']:
        print("=== MISMATCHES ===")
        for i, mm in enumerate(results['mismatches'][:20], 1):
            tf, time_str = mm['key']
            print(f"\n{i}. {tf} @ {time_str}")
            print(f"   Max diff: {mm['max_diff']:.8f}")
            
            # Show mismatched indicators
            mismatched_inds = []
            for ind_name in results['indicator_names']:
                diff = mm['diffs'].get(ind_name)
                if diff is None:
                    py_val = mm['python'].get(ind_name, 'MISSING')
                    cs_val = mm['csharp'].get(ind_name, 'MISSING')
                    mismatched_inds.append(f"{ind_name}: Py={py_val}, C#={cs_val} (MISSING)")
                elif diff > 0.00001:
                    py_val = mm['python'].get(ind_name, 'MISSING')
                    cs_val = mm['csharp'].get(ind_name, 'MISSING')
                    mismatched_inds.append(f"{ind_name}: Py={py_val:.5f}, C#={cs_val:.5f}, Diff={diff:.8f}")
            
            if mismatched_inds:
                for ind_info in mismatched_inds[:10]:  # Show first 10 mismatched indicators
                    print(f"   {ind_info}")
                if len(mismatched_inds) > 10:
                    print(f"   ... and {len(mismatched_inds) - 10} more mismatched indicators")
        
        if len(results['mismatches']) > 20:
            print(f"\n... and {len(results['mismatches']) - 20} more mismatches")
    
    if results['python_only']:
        print(f"\n=== PYTHON-ONLY ENTRIES ({len(results['python_only'])}) ===")
        for key in sorted(results['python_only'])[:10]:
            print(f"  {key[0]} @ {key[1]}")
        if len(results['python_only']) > 10:
            print(f"  ... and {len(results['python_only']) - 10} more")
    
    if results['csharp_only']:
        print(f"\n=== C#-ONLY ENTRIES ({len(results['csharp_only'])}) ===")
        for key in sorted(results['csharp_only'])[:10]:
            print(f"  {key[0]} @ {key[1]}")
        if len(results['csharp_only']) > 10:
            print(f"  ... and {len(results['csharp_only']) - 10} more")
    
    # Summary by timeframe
    print("\n=== SUMMARY BY TIMEFRAME ===")
    for tf in ['M1', 'M5', 'H1', 'H4']:
        tf_python = [k for k in python_inds.keys() if k[0] == tf]
        tf_csharp = [k for k in csharp_inds.keys() if k[0] == tf]
        tf_common = [k for k in results['matches'] if k['key'][0] == tf]
        tf_mismatches = [k for k in results['mismatches'] if k['key'][0] == tf]
        
        print(f"{tf}: Python={len(tf_python)}, C#={len(tf_csharp)}, Common={len(tf_common)}, Mismatches={len(tf_mismatches)}")
    
    # Write detailed comparison to file
    output_file = r"C:\Users\HMz\Documents\cAlgo\Logfiles\indicator_comparison_results.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== INDICATOR COMPARISON RESULTS ===\n\n")
        f.write(f"Total Python entries: {results['total_python']}\n")
        f.write(f"Total C# entries: {results['total_csharp']}\n")
        f.write(f"Common entries: {results['total_common']}\n")
        f.write(f"Matches: {len(results['matches'])}\n")
        f.write(f"Mismatches: {len(results['mismatches'])}\n\n")
        
        if results['indicator_names']:
            f.write(f"Indicators compared: {', '.join(results['indicator_names'])}\n\n")
        
        if results['mismatches']:
            f.write("=== ALL MISMATCHES ===\n\n")
            for mm in results['mismatches']:
                tf, time_str = mm['key']
                f.write(f"{tf} @ {time_str}\n")
                f.write(f"Max diff: {mm['max_diff']:.8f}\n")
                
                for ind_name in results['indicator_names']:
                    diff = mm['diffs'].get(ind_name)
                    if diff is None:
                        py_val = mm['python'].get(ind_name, 'MISSING')
                        cs_val = mm['csharp'].get(ind_name, 'MISSING')
                        f.write(f"  {ind_name}: Py={py_val}, C#={cs_val} (MISSING)\n")
                    elif diff > 0.00001:
                        py_val = mm['python'].get(ind_name, 'MISSING')
                        cs_val = mm['csharp'].get(ind_name, 'MISSING')
                        f.write(f"  {ind_name}: Py={py_val:.5f}, C#={cs_val:.5f}, Diff={diff:.8f}\n")
                f.write("\n")
    
    print(f"\nDetailed results written to: {output_file}")

if __name__ == "__main__":
    main()
