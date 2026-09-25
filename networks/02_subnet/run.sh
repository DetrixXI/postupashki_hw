
import subprocess, sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.exit(subprocess.run([sys.executable, "02_subnet.py", *sys.argv[1:]]).returncode)