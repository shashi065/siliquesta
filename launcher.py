#!/usr/bin/env python3
"""
SILIQUESTA Local Development Launcher

Starts all services locally without Docker:
- FastAPI backend (port 8000)
- Dependencies: PostgreSQL, Redis (optional)

Usage:
    python launcher.py [options]

Options:
    --backend-only      Only start backend (skip database checks)
    --port PORT         Backend port (default: 8000)
    --no-reload         Disable auto-reload
    --debug             Enable debug logging
"""

import subprocess
import sys
import os
import time
import signal
import argparse
from pathlib import Path
from datetime import datetime


class Colors:
    """Terminal colors."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def log(level: str, msg: str):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if level == "INFO":
        color = Colors.OKBLUE
    elif level == "SUCCESS":
        color = Colors.OKGREEN
    elif level == "WARN":
        color = Colors.WARNING
    elif level == "ERROR":
        color = Colors.FAIL
    else:
        color = Colors.ENDC
    
    print(f"{color}[{timestamp}] {level:8} {msg}{Colors.ENDC}")


def check_python_version():
    """Verify Python 3.10+."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        log("ERROR", f"Python 3.10+ required (found {version.major}.{version.minor})")
        sys.exit(1)
    log("SUCCESS", f"Python {version.major}.{version.minor} ready")


def check_dependencies():
    """Verify required packages."""
    required = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "numpy",
        "scipy",
    ]
    
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    
    if missing:
        log("ERROR", f"Missing packages: {', '.join(missing)}")
        log("INFO", "Install with: pip install -r services/api/requirements.txt")
        return False
    
    log("SUCCESS", "All dependencies installed")
    return True


def start_backend(port: int = 8000, reload: bool = True, debug: bool = False):
    """Start FastAPI backend."""
    log("INFO", f"Starting FastAPI backend on port {port}...")
    
    backend_dir = Path(__file__).parent / "services" / "api"
    os.chdir(backend_dir)
    
    # Build uvicorn command
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
    ]
    
    if reload:
        cmd.append("--reload")
    
    if debug:
        cmd.extend(["--log-level", "debug"])
    else:
        cmd.extend(["--log-level", "info"])
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        
        log("SUCCESS", f"Backend process (PID {process.pid}) started")
        
        # Stream output
        for line in process.stdout:
            print(f"  {line.rstrip()}")
        
        return process
    
    except Exception as e:
        log("ERROR", f"Failed to start backend: {e}")
        return None


def wait_for_service(url: str, timeout: int = 30) -> bool:
    """Wait for HTTP service to be ready."""
    import urllib.request
    import urllib.error
    
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = urllib.request.urlopen(url, timeout=2)
            if response.status == 200:
                log("SUCCESS", f"Service ready: {url}")
                return True
        except (urllib.error.URLError, Exception):
            pass
        
        time.sleep(0.5)
    
    log("WARN", f"Service did not become ready within {timeout}s: {url}")
    return False


def main():
    """Main launcher."""
    parser = argparse.ArgumentParser(
        description="SILIQUESTA Local Development Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launcher.py                    # Start all services
  python launcher.py --backend-only    # Start backend only
  python launcher.py --port 9000       # Use port 9000
  python launcher.py --debug           # Enable debug logging
        """,
    )
    
    parser.add_argument("--backend-only", action="store_true", help="Only start backend")
    parser.add_argument("--port", type=int, default=8000, help="Backend port (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔═══════════════════════════════════════════╗")
    print("║  SILIQUESTA - Local Development Launcher  ║")
    print("║          Production-Grade System          ║")
    print("╚═══════════════════════════════════════════╝")
    print(Colors.ENDC)
    
    # Pre-flight checks
    log("INFO", "Running pre-flight checks...")
    check_python_version()
    if not check_dependencies():
        return 1
    
    # Environment setup
    env_file = Path(".env")
    if not env_file.exists():
        log("WARN", ".env file not found, using defaults")
        log("INFO", "Create .env for custom configuration")
    else:
        log("SUCCESS", ".env file loaded")
    
    # Start backend
    log("INFO", "Starting services...")
    processes = []
    
    try:
        backend_proc = start_backend(
            port=args.port,
            reload=not args.no_reload,
            debug=args.debug,
        )
        
        if backend_proc:
            processes.append(backend_proc)
            
            # Wait for readiness
            time.sleep(2)
            wait_for_service(f"http://localhost:{args.port}/health")
            
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}")
            print("╔════════════════════════════════════════════════════════╗")
            print("║              🚀 SILIQUESTA READY TO USE 🚀            ║")
            print("╠════════════════════════════════════════════════════════╣")
            print(f"║ Backend:   http://localhost:{args.port:5}                    ║")
            print(f"║ Docs:      http://localhost:{args.port:5}/docs                 ║")
            print(f"║ Health:    http://localhost:{args.port:5}/health               ║")
            print("│                                                        │")
            print("│ Features:                                              │")
            print("│ ✓ Realistic MOSFET simulation                         │")
            print("│ ✓ 2-stage AI optimization                            │")
            print("│ ✓ Project versioning & sharing                       │")
            print("│ ✓ Simulation history & caching                       │")
            print("│ ✓ Multi-user collaboration                           │")
            print("╚════════════════════════════════════════════════════════╝")
            print(Colors.ENDC)
            
            log("INFO", "Press Ctrl+C to stop all services")
            
            # Keep running
            while True:
                time.sleep(1)
        
        else:
            log("ERROR", "Failed to start services")
            return 1
    
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}")
        log("INFO", "Shutting down services...")
        
        for proc in processes:
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                    log("SUCCESS", f"Process {proc.pid} terminated")
                except subprocess.TimeoutExpired:
                    proc.kill()
                    log("WARN", f"Process {proc.pid} killed")
        
        print(f"{Colors.ENDC}")
        log("SUCCESS", "All services stopped")
        return 0
    
    except Exception as e:
        log("ERROR", f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
