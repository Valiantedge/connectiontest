#!/usr/bin/env python3
"""
Simple test to verify SSH connection tester components work
This tests the basic functionality without requiring actual SSH connections
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import tkinter as tk
        print("✓ tkinter (GUI support) - Available")
        gui_available = True
    except ImportError:
        print("✗ tkinter (GUI support) - Not available")
        gui_available = False
    
    try:
        import paramiko
        print("✓ paramiko (SSH library) - Available")
        ssh_available = True
    except ImportError:
        print("✗ paramiko (SSH library) - Not available")
        print("  Install with: pip install paramiko")
        ssh_available = False
    
    try:
        import threading
        print("✓ threading - Available")
    except ImportError:
        print("✗ threading - Not available")
    
    try:
        from datetime import datetime
        print("✓ datetime - Available")
    except ImportError:
        print("✗ datetime - Not available")
    
    return gui_available, ssh_available

def test_gui():
    """Test if GUI can be created"""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the window
        print("✓ GUI can be created")
        root.destroy()
        return True
    except Exception as e:
        print(f"✗ GUI creation failed: {e}")
        return False

def test_ssh_client():
    """Test if SSH client can be created"""
    try:
        import paramiko
        client = paramiko.SSHClient()
        print("✓ SSH client can be created")
        client.close()
        return True
    except Exception as e:
        print(f"✗ SSH client creation failed: {e}")
        return False

def test_files():
    """Test if all required files exist"""
    print("\nTesting files...")
    
    files = [
        "ssh_connection_tester.py",
        "ssh_tester_cli.py", 
        "requirements.txt",
        "README.md"
    ]
    
    all_exist = True
    for file in files:
        if os.path.exists(file):
            print(f"✓ {file} - Found")
        else:
            print(f"✗ {file} - Missing")
            all_exist = False
    
    return all_exist

def main():
    print("=== SSH Connection Tester - Component Test ===\n")
    
    # Test imports
    gui_available, ssh_available = test_imports()
    
    print("\nTesting components...")
    
    # Test GUI if available
    if gui_available:
        gui_works = test_gui()
    else:
        gui_works = False
        print("✗ GUI test skipped (tkinter not available)")
    
    # Test SSH if available
    if ssh_available:
        ssh_works = test_ssh_client()
    else:
        ssh_works = False
        print("✗ SSH test skipped (paramiko not available)")
    
    # Test files
    files_exist = test_files()
    
    print("\n=== Test Summary ===")
    print(f"GUI Support: {'✓' if gui_available else '✗'}")
    print(f"SSH Support: {'✓' if ssh_available else '✗'}")
    print(f"GUI Functionality: {'✓' if gui_works else '✗'}")
    print(f"SSH Functionality: {'✓' if ssh_works else '✗'}")
    print(f"All Files Present: {'✓' if files_exist else '✗'}")
    
    print("\n=== Recommendations ===")
    
    if not ssh_available:
        print("• Install paramiko: pip install paramiko")
    
    if not gui_available:
        print("• For GUI support on Linux: sudo apt install python3-tkinter")
        print("• For headless servers: Use the CLI version (ssh_tester_cli.py)")
    
    if ssh_available and files_exist:
        print("• Ready to test SSH connections!")
        if gui_available:
            print("• Run GUI version: python ssh_connection_tester.py")
        print("• Run CLI version: python ssh_tester_cli.py --help")
    
    # Return 0 if basic functionality is available
    return 0 if (ssh_available and files_exist) else 1

if __name__ == "__main__":
    sys.exit(main())
