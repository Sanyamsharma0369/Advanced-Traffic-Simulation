import os
import subprocess
import sys
import logging.config

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Load logging configuration
logging_config_path = os.path.join(project_root, 'backend', 'api', 'logging.conf')
logging.config.fileConfig(logging_config_path, disable_existing_loggers=False)

# Add the backend directory to the Python path as well, for internal imports
sys.path.insert(0, os.path.join(project_root, 'backend'))

# Command to run uvicorn
command = [
    sys.executable, '-m', 'uvicorn',
    'api.main:app',
    '--host', '0.0.0.0',
    '--port', '8080'
]

# Change to the backend directory
os.chdir(os.path.join(project_root, 'backend'))

# Execute the uvicorn command
subprocess.Popen(command)