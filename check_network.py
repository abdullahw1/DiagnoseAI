#!/usr/bin/env python3
"""
Network connectivity checker for DiagnoseAI
Helps troubleshoot network access issues
"""
import socket
import subprocess
import platform

def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return None

def check_port_available(host, port):
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0
    except Exception:
        return False

def get_network_info():
    """Get detailed network information."""
    try:
        if platform.system() == "Darwin":  # macOS
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            return result.stdout
        else:
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
            return result.stdout
    except Exception as e:
        return f"Error getting network info: {e}"

def main():
    """Check network configuration for DiagnoseAI."""
    print("🔍 DiagnoseAI Network Configuration Check")
    print("=" * 50)
    
    # Get local IP
    local_ip = get_local_ip()
    port = 5003
    
    if local_ip:
        print(f"✅ Local IP Address: {local_ip}")
        print(f"🌐 Network URL: http://{local_ip}:{port}")
    else:
        print("❌ Could not determine local IP address")
        return
    
    # Check if port is available
    if check_port_available('0.0.0.0', port):
        print(f"✅ Port {port} is available")
    else:
        print(f"⚠️  Port {port} is in use")
        print("   Stop any running DiagnoseAI instances first")
    
    print("\n📋 Network Information:")
    print("-" * 30)
    
    # Show network interfaces
    network_info = get_network_info()
    lines = network_info.split('\n')
    
    # Extract relevant network interfaces
    current_interface = None
    for line in lines:
        if line.startswith(('en0:', 'en1:', 'wlan0:', 'eth0:')):
            current_interface = line.split(':')[0]
            print(f"\n🔌 Interface: {current_interface}")
        elif 'inet ' in line and '127.0.0.1' not in line and current_interface:
            ip_part = line.strip().split()[1]
            if '/' in ip_part:
                ip_part = ip_part.split('/')[0]
            print(f"   IP: {ip_part}")
    
    print("\n🔒 Firewall Check:")
    print("-" * 20)
    
    # Check macOS firewall status
    try:
        result = subprocess.run(['sudo', 'pfctl', '-s', 'info'], 
                              capture_output=True, text=True, timeout=5)
        if 'Status: Enabled' in result.stdout:
            print("⚠️  macOS Firewall is enabled")
            print("   You may need to allow Python in firewall settings")
        else:
            print("✅ macOS Firewall appears to be disabled")
    except:
        print("ℹ️  Could not check firewall status (normal)")
    
    print("\n📱 Sharing Instructions:")
    print("-" * 25)
    print(f"1. Start DiagnoseAI: python run_network.py")
    print(f"2. Share this URL: http://{local_ip}:{port}")
    print(f"3. Login: admin / admin123")
    print(f"4. Make sure both devices are on the same WiFi network")
    
    print("\n🧪 Test Connectivity:")
    print("-" * 20)
    print("From another device, try:")
    print(f"• Open web browser")
    print(f"• Go to: http://{local_ip}:{port}")
    print(f"• You should see the DiagnoseAI login page")
    
    print("\n🔧 Troubleshooting:")
    print("-" * 15)
    print("If connection fails:")
    print("• Check both devices are on same WiFi")
    print("• Try disabling Mac firewall temporarily")
    print("• Restart your router if needed")
    print("• Try a different port (edit run_network.py)")

if __name__ == '__main__':
    main()