#!/usr/bin/env python3

import os
import sys
import subprocess
import time
import json
import re
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

# ─────────────────────────────────────────────
# State Constants
# ─────────────────────────────────────────────

IDLE = "idle"
RUNNING = "running"
OK = "ok"
ERROR = "error"

SERVICE_NOT_SEEN = "not_seen"
SERVICE_STARTING = "starting"
SERVICE_HEALTHY = "healthy"
SERVICE_FAILED = "failed"


# ─────────────────────────────────────────────
# Launcher
# ─────────────────────────────────────────────

class DockerComposeLauncher:
    def __init__(self):
        self.app_url = "http://localhost"
        self.enc_file = "./secrets.enc"
        self.loaded_secrets: List[str] = []
        self.debug_mode = False

        self.sections = {
            "deps": IDLE,
            "secrets": IDLE,
            "compose": IDLE,
            "health": IDLE,
            "web": IDLE,
        }

        self.services: List[str] = []
        self.service_state: Dict[str, str] = {}

    # ─────────────────────────────────────────
    # Rendering
    # ─────────────────────────────────────────

    def render(self, error_message: str = None):
        print("\033[H\033[J", end="")

        print("████████████████████████████████████████")
        print("🚀  ARCHIVE APP LAUNCHER")
        if self.debug_mode:
            print("DEBUG MODE: ON")
        print(f"BASE URL: {self.app_url}")
        print("████████████████████████████████████████\n")

        def icon(state):
            return {
                IDLE: "⠿",
                RUNNING: "⟳",
                OK: "✔",
                ERROR: "✖",
            }[state]

        print(f"{icon(self.sections['deps'])} Check Dependencies")
        print(f"{icon(self.sections['secrets'])} Decrypt Secrets")
        print(f"{icon(self.sections['compose'])} Start Compose")

        print(f"{icon(self.sections['health'])} Health Check")
        print(f"{icon(self.sections['web'])} Web App Reachability")
        print("")

        if self.services:
            print("   " + " ".join(self.service_icon(s) for s in self.services), end="", flush=True)

        if error_message:
            print("\n✖ ERROR:")
            print(f"  {error_message}")

    def service_icon(self, svc: str) -> str:
        return {
            SERVICE_NOT_SEEN: "⚪",
            SERVICE_STARTING: "🟡",
            SERVICE_HEALTHY: "🟢",
            SERVICE_FAILED: "🔴",
        }[self.service_state.get(svc, SERVICE_NOT_SEEN)]

    # ─────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────

    def parse_args(self):
        """Parse command line arguments for key"""
        parser = argparse.ArgumentParser(description="Launch Docker environment with secrets")
        parser.add_argument('-k', '--key', help='AGE secret key')
        parser.add_argument('key_positional', nargs='?', help='AGE secret key (positional)')
        
        # Try to parse, but don't exit on error for now
        try:
            args = parser.parse_args()
            
            # Priority: --key flag > positional argument
            if args.key:
                return args.key
            elif args.key_positional:
                return args.key_positional
        except:
            pass
        return None

    def run_command(self, cmd: List[str], timeout=60) -> Tuple[bool, str, str]:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=sys.platform == "win32"
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def run_docker_compose(self, args: List[str]) -> Tuple[bool, str, str]:
        success, out, err = self.run_command(["docker", "compose"] + args)
        if success or "docker compose" in err.lower():
            return success, out, err
        return self.run_command(["docker-compose"] + args)

    # ─────────────────────────────────────────
    # Steps
    # ─────────────────────────────────────────

    def extract_config(self):
        for file in ["compose.yml", "docker-compose.yml"]:
            p = Path(file)
            if not p.exists():
                continue

            text = p.read_text()
            if m := re.search(r"BASE_URL:\s*(.+)", text):
                self.app_url = m.group(1).strip(" '\"")
            if m := re.search(r"DEBUG_STATUS:\s*(true|false)", text, re.I):
                self.debug_mode = m.group(1).lower() == "true"

    def run_external_install_script(self) -> bool:
        """Run the OS-specific dependency installation script."""
        platform = sys.platform
        print("\nMissing dependencies detected. Attempting to run installation script...\n")

        if platform.startswith("linux") or platform == "darwin":
            script_path = Path("./start_deps.sh").resolve()
            if not script_path.exists():
                print(f"Error: Installation script not found at {script_path}")
                return False
            
            # Make executable (try os.chmod, fallback to sudo chmod for elevated requirement)
            try:
                os.chmod(script_path, 0o755)
            except OSError:
                print("Permission denied when setting executable flag. Trying with sudo...")
                subprocess.run(["sudo", "chmod", "+x", str(script_path)])
            
            cmd = ["/bin/bash", str(script_path)]
            # We want to show output directly to user
            try:
                subprocess.check_call(cmd)
                return True
            except subprocess.CalledProcessError:
                return False

        elif platform == "win32":
            script_path = Path("./start_deps.ps1").resolve()
            if not script_path.exists():
                print(f"Error: Installation script not found at {script_path}")
                return False
            
            # Run powershell script
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
            try:
                subprocess.check_call(cmd)
                return True
            except subprocess.CalledProcessError:
                return False

        else:
            print(f"Unsupported platform for auto-install: {platform}")
            return False

    def check_dependencies(self) -> Tuple[bool, list]:
        required = ["docker", "sops", "curl"]
        missing = []

        for cmd in required:
            # use 'where' on windows, 'which' on unix
            check_tool = "where" if sys.platform == "win32" else "which"
            ok, _, _ = self.run_command([check_tool, cmd])
            if not ok:
                missing.append(cmd)

        if missing:
             # Attempt to install
             if self.run_external_install_script():
                 # Re-check
                 return self.check_dependencies_silent()
             else:
                 return False, missing
        
        return True, []

    def check_dependencies_silent(self) -> Tuple[bool, list]:
        """Check dependencies without triggering install."""
        required = ["docker", "sops", "curl"]
        missing = []
        check_tool = "where" if sys.platform == "win32" else "which"
        for cmd in required:
            ok, _, _ = self.run_command([check_tool, cmd])
            if not ok:
                missing.append(cmd)
        return len(missing) == 0, missing

    def load_secrets(self, key: str) -> bool:
        os.environ["SOPS_AGE_KEY"] = key
        ok, out, _ = self.run_command(
            ["sops", "-d", "--input-type", "dotenv", "--output-type", "dotenv", self.enc_file],
            timeout=10
        )
        if not ok:
            return False

        for line in out.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ[k] = v.strip("'\"")
                self.loaded_secrets.append(k)
        return True

    def discover_services(self) -> bool:
        ok, out, _ = self.run_docker_compose(["config", "--services"])
        if not ok:
            return False
        self.services = [s for s in out.splitlines() if s]
        self.service_state = {s: SERVICE_NOT_SEEN for s in self.services}
        return True

    def launch_and_monitor(self) -> bool:
        ok, _, err = self.run_docker_compose(["up", "-d"])
        if not ok:
            return False

        start = time.time()
        timeout = 180

        while time.time() - start < timeout:
            ok, out, _ = self.run_docker_compose(["ps", "--format", "json"])
            if not ok:
                return False

            seen = set()
            for line in out.splitlines():
                svc = json.loads(line)
                name = svc["Service"]
                state = svc["State"].lower()
                health = svc.get("Health", "").lower()

                seen.add(name)

                if state == "running" and health == "healthy":
                    self.service_state[name] = SERVICE_HEALTHY
                elif state == "running":
                    self.service_state[name] = SERVICE_STARTING
                elif state == "exited":
                    self.service_state[name] = SERVICE_FAILED

            for s in self.services:
                if s not in seen:
                    self.service_state[s] = SERVICE_NOT_SEEN

            print("\r   " + " ".join(self.service_icon(s) for s in self.services), end="", flush=True)

            if all(self.service_state[s] == SERVICE_HEALTHY for s in self.services):
                return True

            time.sleep(0.5)

        return False

    def check_web(self) -> bool:
        for _ in range(30):
            try:
                with urllib.request.urlopen(f"{self.app_url}/health/", timeout=2) as r:
                    if r.status == 200:
                        return True
            except:
                time.sleep(1)
        return False

    def cleanup(self):
        for k in self.loaded_secrets:
            os.environ.pop(k, None)
        os.environ.pop("SOPS_AGE_KEY", None)

    # ─────────────────────────────────────────
    # Main Orchestrator
    # ─────────────────────────────────────────

    def run(self):
        try:
            self.extract_config()

            # ✅ Discover services immediately so circles are visible
            if not self.discover_services():
                self.render("Failed to read compose services")
                sys.exit(1)

            self.render()

            # Dependencies
            self.sections["deps"] = RUNNING
            self.render()
            if not self.check_dependencies():
                self.sections["deps"] = ERROR
                self.render("Missing required dependencies")
                sys.exit(1)
            self.sections["deps"] = OK

            # Secrets
            self.sections["secrets"] = RUNNING
            self.render()
            args = self.parse_args()
            key = args or os.environ.get("SOPS_AGE_KEY") or input("Paste AGE key: ").strip()
            if not self.load_secrets(key):
                self.sections["secrets"] = ERROR
                self.render("Failed to decrypt secrets")
                sys.exit(1)
            self.sections["secrets"] = OK

            # Compose
            self.sections["compose"] = RUNNING
            self.render()
            if not self.discover_services():
                self.sections["compose"] = ERROR
                self.render("Failed to read compose services")
                sys.exit(1)

            if not self.launch_and_monitor():
                self.sections["compose"] = ERROR
                self.render("Containers failed to become healthy")
                sys.exit(1)
            self.sections["compose"] = OK
            self.sections["health"] = OK

            # Web
            self.sections["web"] = RUNNING
            self.render()
            if not self.check_web():
                self.sections["web"] = ERROR
                self.render("Web application did not become reachable")
                sys.exit(1)

            self.sections["web"] = OK
            self.render()

            print("\n🎉 Environment ready")

        finally:
            self.cleanup()


def main():
    DockerComposeLauncher().run()


if __name__ == "__main__":
    main()
