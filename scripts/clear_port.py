#!/usr/bin/env python3
"""
Utility script to clear port 5003
"""
import subprocess
import sys
import time

def clear_port(port=5003):
    """Clear any processes running on the specified port."""
    try:
        print(f"🔍 Checking for processes on port {port}...")
        
        # Find processes using the port
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True, check=False)
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"📋 Found {len(pids)} process(es) on port {port}")
            
            for pid in pids:
                if pid:
                    try:
                        # Get process info
                        proc_info = subprocess.run(['ps', '-p', pid, '-o', 'comm='], 
                                                 capture_output=True, text=True, check=False)
                        process_name = proc_info.stdout.strip() if proc_info.returncode == 0 else "unknown"
                        
                        print(f"🔄 Terminating process {pid} ({process_name})...")
                        
                        # Try graceful termination first
                        subprocess.run(['kill', '-15', pid], check=False)
                        time.sleep(2)
                        
                        # Check if still running
                        check_result = subprocess.run(['kill', '-0', pid], 
                                                    capture_output=True, check=False)
                        if check_result.returncode == 0:
                            print(f"💀 Force killing process {pid}...")
                            subprocess.run(['kill', '-9', pid], check=False)
                        
                    except Exception as e:
                        print(f"⚠️  Error killing process {pid}: {e}")
            
            print(f"✅ Port {port} cleared")
            return True
        else:
            print(f"✅ Port {port} is already free")
            return True
            
    except Exception as e:
        print(f"❌ Error clearing port {port}: {e}")
        return False

def main():
    """Main function."""
    print("🧹 DiagnoseAI Port Cleaner")
    print("=" * 30)
    
    if clear_port(5003):
        print("\n🎉 Ready to start DiagnoseAI!")
        print("💡 Run: python start.py")
    else:
        print("\n❌ Failed to clear port 5003")
        print("💡 You may need to manually stop processes or restart your system")
        sys.exit(1)

if __name__ == '__main__':
    main()