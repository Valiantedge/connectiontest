#!/usr/bin/env python3
"""
SSH Connection Tester with GUI
A tool to test SSH connections to on-premise Linux servers through VPN
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import paramiko
import threading
import os
import sys
from datetime import datetime

class SSHConnectionTester:
    def __init__(self, root):
        self.root = root
        self.root.title("SSH Connection Tester")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # SSH client instance
        self.ssh_client = None
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="SSH Connection Tester", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Connection Details Frame
        conn_frame = ttk.LabelFrame(main_frame, text="Connection Details", padding="10")
        conn_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        conn_frame.columnconfigure(1, weight=1)
        
        # Server IP
        ttk.Label(conn_frame, text="Server IP:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.server_ip = tk.StringVar()
        ip_entry = ttk.Entry(conn_frame, textvariable=self.server_ip, width=30)
        ip_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # Port
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        self.port = tk.StringVar(value="22")
        port_entry = ttk.Entry(conn_frame, textvariable=self.port, width=10)
        port_entry.grid(row=0, column=3, sticky=tk.W, padx=(5, 0), pady=5)
        
        # Username
        ttk.Label(conn_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.username = tk.StringVar()
        username_entry = ttk.Entry(conn_frame, textvariable=self.username, width=30)
        username_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # SSH Tunnel Frame
        tunnel_frame = ttk.LabelFrame(main_frame, text="SSH Tunnel (Optional)", padding="10")
        tunnel_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        tunnel_frame.columnconfigure(1, weight=1)
        
        # Use tunnel checkbox
        self.use_tunnel = tk.BooleanVar(value=False)
        tunnel_check = ttk.Checkbutton(tunnel_frame, text="Use SSH Tunnel through laptop", 
                                      variable=self.use_tunnel, command=self.toggle_tunnel)
        tunnel_check.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=5)
        
        # Tunnel host (your laptop)
        self.tunnel_host_label = ttk.Label(tunnel_frame, text="Laptop IP:")
        self.tunnel_host = tk.StringVar()
        self.tunnel_host_entry = ttk.Entry(tunnel_frame, textvariable=self.tunnel_host, width=20)
        
        # Tunnel port
        self.tunnel_port_label = ttk.Label(tunnel_frame, text="SSH Port:")
        self.tunnel_port = tk.StringVar(value="22")
        self.tunnel_port_entry = ttk.Entry(tunnel_frame, textvariable=self.tunnel_port, width=10)
        
        # Tunnel username
        self.tunnel_user_label = ttk.Label(tunnel_frame, text="Laptop User:")
        self.tunnel_user = tk.StringVar()
        self.tunnel_user_entry = ttk.Entry(tunnel_frame, textvariable=self.tunnel_user, width=20)
        
        # Tunnel password
        self.tunnel_pass_label = ttk.Label(tunnel_frame, text="Laptop Password:")
        self.tunnel_pass = tk.StringVar()
        self.tunnel_pass_entry = ttk.Entry(tunnel_frame, textvariable=self.tunnel_pass, show="*", width=20)
        
        # Authentication Method Frame
        auth_frame = ttk.LabelFrame(main_frame, text="Target Server Authentication", padding="10")
        auth_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        auth_frame.columnconfigure(1, weight=1)
        
        # Authentication method selection
        self.auth_method = tk.StringVar(value="password")
        ttk.Radiobutton(auth_frame, text="Password", variable=self.auth_method, 
                       value="password", command=self.toggle_auth_method).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(auth_frame, text="Private Key", variable=self.auth_method, 
                       value="key", command=self.toggle_auth_method).grid(row=0, column=1, sticky=tk.W)
        
        # Password field
        self.password_label = ttk.Label(auth_frame, text="Password:")
        self.password_label.grid(row=1, column=0, sticky=tk.W, pady=(10, 5))
        self.password = tk.StringVar()
        self.password_entry = ttk.Entry(auth_frame, textvariable=self.password, 
                                       show="*", width=40)
        self.password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(10, 5))
        
        # Private key field
        self.key_label = ttk.Label(auth_frame, text="Private Key:")
        self.key_file = tk.StringVar()
        self.key_entry = ttk.Entry(auth_frame, textvariable=self.key_file, width=40)
        self.key_browse_btn = ttk.Button(auth_frame, text="Browse", command=self.browse_key_file)
        
        # Commands Frame
        cmd_frame = ttk.LabelFrame(main_frame, text="Commands to Execute", padding="10")
        cmd_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        cmd_frame.columnconfigure(0, weight=1)
        
        # Default commands
        self.commands = tk.Text(cmd_frame, height=4, width=60)
        self.commands.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        self.commands.insert("1.0", "hostname\nuptime\nwhoami\ndf -h")
        
        # Buttons Frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=(0, 10))
        
        # Connect and Test button
        self.test_btn = ttk.Button(btn_frame, text="Test SSH Connection", 
                                  command=self.start_ssh_test, style="Accent.TButton")
        self.test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear button
        clear_btn = ttk.Button(btn_frame, text="Clear Output", command=self.clear_output)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Save Output button
        save_btn = ttk.Button(btn_frame, text="Save Output", command=self.save_output)
        save_btn.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Output Frame
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="10")
        output_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        # Output text area with scrollbar
        self.output_text = scrolledtext.ScrolledText(output_frame, height=20, width=80,
                                                    font=("Consolas", 10))
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        # Initialize auth method display
        self.toggle_auth_method()
        # Initialize tunnel display
        self.toggle_tunnel()
        
    def toggle_tunnel(self):
        """Toggle tunnel configuration fields visibility"""
        if self.use_tunnel.get():
            # Show tunnel fields
            self.tunnel_host_label.grid(row=1, column=0, sticky=tk.W, pady=5, padx=(20, 0))
            self.tunnel_host_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(5, 10))
            self.tunnel_port_label.grid(row=1, column=2, sticky=tk.W, pady=5, padx=(10, 0))
            self.tunnel_port_entry.grid(row=1, column=3, sticky=tk.W, pady=5, padx=(5, 0))
            
            self.tunnel_user_label.grid(row=2, column=0, sticky=tk.W, pady=5, padx=(20, 0))
            self.tunnel_user_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(5, 10))
            self.tunnel_pass_label.grid(row=2, column=2, sticky=tk.W, pady=5, padx=(10, 0))
            self.tunnel_pass_entry.grid(row=2, column=3, sticky=tk.W, pady=5, padx=(5, 0))
        else:
            # Hide tunnel fields
            self.tunnel_host_label.grid_remove()
            self.tunnel_host_entry.grid_remove()
            self.tunnel_port_label.grid_remove()
            self.tunnel_port_entry.grid_remove()
            self.tunnel_user_label.grid_remove()
            self.tunnel_user_entry.grid_remove()
            self.tunnel_pass_label.grid_remove()
            self.tunnel_pass_entry.grid_remove()
    
    def toggle_auth_method(self):
        """Toggle between password and key authentication UI elements"""
        if self.auth_method.get() == "password":
            # Show password fields
            self.password_label.grid(row=1, column=0, sticky=tk.W, pady=(10, 5))
            self.password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(10, 5))
            # Hide key fields
            self.key_label.grid_remove()
            self.key_entry.grid_remove()
            self.key_browse_btn.grid_remove()
        else:
            # Hide password fields
            self.password_label.grid_remove()
            self.password_entry.grid_remove()
            # Show key fields
            self.key_label.grid(row=1, column=0, sticky=tk.W, pady=(10, 5))
            self.key_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(10, 5))
            self.key_browse_btn.grid(row=1, column=2, padx=(5, 0), pady=(10, 5))
    
    def browse_key_file(self):
        """Browse for private key file"""
        filename = filedialog.askopenfilename(
            title="Select Private Key File",
            filetypes=[("All files", "*.*"), ("PEM files", "*.pem"), ("Key files", "*.key")]
        )
        if filename:
            self.key_file.set(filename)
    
    def log_message(self, message, level="INFO"):
        """Add message to output with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}\n"
        
        self.output_text.insert(tk.END, formatted_message)
        self.output_text.see(tk.END)
        self.root.update()
    
    def clear_output(self):
        """Clear the output text area"""
        self.output_text.delete(1.0, tk.END)
    
    def save_output(self):
        """Save output to file"""
        content = self.output_text.get(1.0, tk.END)
        if not content.strip():
            messagebox.showwarning("Warning", "No output to save!")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Output saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def validate_inputs(self):
        """Validate user inputs"""
        if not self.server_ip.get().strip():
            raise ValueError("Server IP is required")
        
        if not self.username.get().strip():
            raise ValueError("Username is required")
        
        try:
            port = int(self.port.get())
            if port < 1 or port > 65535:
                raise ValueError("Port must be between 1 and 65535")
        except ValueError:
            raise ValueError("Port must be a valid number")
        
        # Validate tunnel settings if enabled
        if self.use_tunnel.get():
            if not self.tunnel_host.get().strip():
                raise ValueError("Laptop IP is required for SSH tunnel")
            if not self.tunnel_user.get().strip():
                raise ValueError("Laptop username is required for SSH tunnel")
            if not self.tunnel_pass.get():
                raise ValueError("Laptop password is required for SSH tunnel")
            try:
                tunnel_port = int(self.tunnel_port.get())
                if tunnel_port < 1 or tunnel_port > 65535:
                    raise ValueError("Tunnel port must be between 1 and 65535")
            except ValueError:
                raise ValueError("Tunnel port must be a valid number")
        
        if self.auth_method.get() == "password":
            if not self.password.get():
                raise ValueError("Password is required")
        else:
            if not self.key_file.get().strip():
                raise ValueError("Private key file is required")
            if not os.path.exists(self.key_file.get()):
                raise ValueError("Private key file does not exist")
    
    def start_ssh_test(self):
        """Start SSH test in a separate thread"""
        try:
            self.validate_inputs()
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return
        
        # Disable button and start progress
        self.test_btn.config(state="disabled")
        self.progress.start(10)
        self.status_var.set("Connecting...")
        
        # Clear previous output
        self.clear_output()
        
        # Start SSH test in thread
        thread = threading.Thread(target=self.ssh_test_worker, daemon=True)
        thread.start()
    
    def ssh_test_worker(self):
        """Worker function for SSH testing (runs in separate thread)"""
        tunnel_client = None
        try:
            self.log_message("Starting SSH connection test...")
            
            if self.use_tunnel.get():
                self.log_message(f"Using SSH tunnel through: {self.tunnel_user.get()}@{self.tunnel_host.get()}:{self.tunnel_port.get()}")
                self.log_message(f"Target server: {self.username.get()}@{self.server_ip.get()}:{self.port.get()}")
                
                # Create tunnel connection to your laptop first
                self.log_message("Establishing SSH tunnel to laptop...")
                tunnel_client = paramiko.SSHClient()
                tunnel_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                tunnel_client.connect(
                    hostname=self.tunnel_host.get().strip(),
                    port=int(self.tunnel_port.get()),
                    username=self.tunnel_user.get().strip(),
                    password=self.tunnel_pass.get(),
                    timeout=10
                )
                self.log_message("✓ SSH tunnel to laptop established!", "SUCCESS")
                
                # Create a transport tunnel
                transport = tunnel_client.get_transport()
                dest_addr = (self.server_ip.get().strip(), int(self.port.get()))
                local_addr = ('127.0.0.1', 0)  # Let system choose local port
                
                self.log_message(f"Creating tunnel channel to {dest_addr[0]}:{dest_addr[1]}...")
                channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)
                
                # Create SSH client for final connection through tunnel
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Connect through the tunnel channel
                self.log_message("Connecting to target server through tunnel...")
                if self.auth_method.get() == "password":
                    self.ssh_client.connect(
                        hostname=self.server_ip.get().strip(),
                        port=int(self.port.get()),
                        username=self.username.get().strip(),
                        password=self.password.get(),
                        timeout=10,
                        sock=channel
                    )
                else:
                    self.ssh_client.connect(
                        hostname=self.server_ip.get().strip(),
                        port=int(self.port.get()),
                        username=self.username.get().strip(),
                        key_filename=self.key_file.get().strip(),
                        timeout=10,
                        sock=channel
                    )
            else:
                # Direct connection (original logic)
                self.log_message(f"Direct connection to: {self.username.get()}@{self.server_ip.get()}:{self.port.get()}")
                
                # Create SSH client
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Connect
                self.log_message("Establishing direct SSH connection...")
                
                if self.auth_method.get() == "password":
                    self.ssh_client.connect(
                        hostname=self.server_ip.get().strip(),
                        port=int(self.port.get()),
                        username=self.username.get().strip(),
                        password=self.password.get(),
                        timeout=10
                    )
                else:
                    self.ssh_client.connect(
                        hostname=self.server_ip.get().strip(),
                        port=int(self.port.get()),
                        username=self.username.get().strip(),
                        key_filename=self.key_file.get().strip(),
                        timeout=10
                    )
            
            self.log_message("✓ SSH connection to target server established successfully!", "SUCCESS")
            
            # Get commands to execute
            commands = self.commands.get("1.0", tk.END).strip().split('\n')
            commands = [cmd.strip() for cmd in commands if cmd.strip()]
            
            # Execute commands
            for command in commands:
                if command:
                    self.log_message(f"Executing: {command}")
                    stdin, stdout, stderr = self.ssh_client.exec_command(command)
                    
                    # Get output
                    output = stdout.read().decode('utf-8').strip()
                    error = stderr.read().decode('utf-8').strip()
                    
                    if output:
                        self.log_message(f"Output:\n{output}", "OUTPUT")
                    if error:
                        self.log_message(f"Error:\n{error}", "ERROR")
                    
                    self.log_message("-" * 50)
            
            self.log_message("✓ All commands executed successfully!", "SUCCESS")
            self.root.after(0, lambda: self.status_var.set("Connection test completed successfully"))
            
        except paramiko.AuthenticationException:
            error_msg = "Authentication failed. Please check your credentials."
            self.log_message(error_msg, "ERROR")
            self.root.after(0, lambda: self.status_var.set("Authentication failed"))
            
        except paramiko.SSHException as e:
            error_msg = f"SSH connection error: {str(e)}"
            self.log_message(error_msg, "ERROR")
            self.root.after(0, lambda: self.status_var.set("SSH connection failed"))
            
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            self.log_message(error_msg, "ERROR")
            self.root.after(0, lambda: self.status_var.set("Connection failed"))
            
        finally:
            # Clean up
            if self.ssh_client:
                self.ssh_client.close()
            if tunnel_client:
                tunnel_client.close()
            
            # Re-enable UI
            self.root.after(0, self.finish_test)
    
    def finish_test(self):
        """Clean up after test completion"""
        self.progress.stop()
        self.test_btn.config(state="normal")


def main():
    # Check if paramiko is installed
    try:
        import paramiko
    except ImportError:
        messagebox.showerror(
            "Missing Dependency", 
            "The 'paramiko' library is required but not installed.\n\n"
            "Please install it using:\n"
            "pip install paramiko\n\n"
            "The application will now close."
        )
        return
    
    # Create and run the application
    root = tk.Tk()
    app = SSHConnectionTester(root)
    
    # Handle window close
    def on_closing():
        if app.ssh_client:
            app.ssh_client.close()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
