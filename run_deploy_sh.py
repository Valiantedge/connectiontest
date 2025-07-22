import subprocess

# Run deploy.sh script using bash
result = subprocess.run(["bash", "deploy.sh"], capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
