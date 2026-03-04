#!/usr/bin/env python
"""
SAS Translator - Professional Administration Tool
Python frontend that calls PowerShell scripts for local dev and cloud deployment.
"""
import subprocess
import sys
import os
from pathlib import Path
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path("C:/projects/sas_translator")
SCRIPTS_DIR = PROJECT_ROOT / "admin-tool" / "powershell"

# Try to import rich for beautiful output (optional)
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich import print as rprint
    from rich.progress import Progress, SpinnerColumn, TextColumn
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback to simple prints
    console = type('obj', (object,), {'print': print})


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def run_powershell(script_name, *args, show_output=True):
    """
    Run a PowerShell script and return the result.
    
    Args:
        script_name: Name of the .ps1 file (e.g., 'start-local.ps1')
        *args: Additional arguments to pass to the script
        show_output: If True, print output in real-time
    
    Returns:
        Tuple of (success, output)
    """
    script_path = SCRIPTS_DIR / script_name
    
    if not script_path.exists():
        console.print(f"[bold red]❌ Script not found: {script_path}[/bold red]")
        return False, ""
    
    # Build command
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)] + list(args)
    
    if show_output:
        # Run and show output in real-time
        console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
        result = subprocess.run(cmd)
        return result.returncode == 0, ""
    else:
        # Run silently and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


# ============================================================================
# ADMIN FUNCTIONS
# ============================================================================

def start_local():
    """Start local development environment."""
    clear_screen()
    console.print(Panel.fit(
        "[bold cyan]🚀 START LOCAL DEVELOPMENT[/bold cyan]",
        border_style="green"
    ))
    
    success, _ = run_powershell("start-local.ps1", show_output=True)
    
    if success:
        console.print("\n[bold green]✅ Services started successfully![/bold green]")
        console.print("[cyan]   Backend:  http://localhost:8000[/cyan]")
        console.print("[cyan]   Frontend: http://localhost:8050[/cyan]")
    else:
        console.print("\n[bold red]❌ Failed to start services[/bold red]")
    
    input("\nPress Enter to continue...")


def stop_local():
    """Stop local development environment."""
    clear_screen()
    console.print(Panel.fit(
        "[bold yellow]🛑 STOP LOCAL SERVICES[/bold yellow]",
        border_style="yellow"
    ))
    
    console.print("[yellow]Stopping all Python processes...[/yellow]")
    success, _ = run_powershell("stop-local.ps1", show_output=True)
    
    if success:
        console.print("[bold green]✅ Services stopped[/bold green]")
    else:
        console.print("[bold red]❌ Failed to stop services[/bold red]")
    
    input("\nPress Enter to continue...")


def deploy():
    """Deploy to Hetzner cloud."""
    clear_screen()
    console.print(Panel.fit(
        "[bold magenta]☁️ DEPLOY TO HETZNER[/bold magenta]",
        border_style="magenta"
    ))
    
    # Show current git status reminder
    console.print("[yellow]⚠️  Remember to commit and push to Codeberg first![/yellow]")
    
    # Confirm deployment
    if not Confirm.ask("\nDeploy to production?"):
        console.print("[yellow]Deployment cancelled.[/yellow]")
        input("\nPress Enter to continue...")
        return
    
    # Run deployment with progress spinner
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Deploying to Hetzner...", total=None)
        success, output = run_powershell("deploy.ps1", show_output=True)
    
    if success:
        console.print("\n[bold green]✅ Deployment complete![/bold green]")
        console.print("[cyan]   Site: https://sas-translator.com[/cyan]")
    else:
        console.print("\n[bold red]❌ Deployment failed[/bold red]")
    
    input("\nPress Enter to continue...")


def run_tests():
    """Run test suite."""
    clear_screen()
    console.print(Panel.fit(
        "[bold blue]🧪 RUN TESTS[/bold blue]",
        border_style="blue"
    ))
    
    # Optional: specify test directory
    test_dir = Prompt.ask(
        "Test directory",
        default="C:/projects/sas_translator/tests/data"
    )
    
    success, output = run_powershell("test.ps1", test_dir, show_output=True)
    
    if success:
        console.print("\n[bold green]✅ Tests completed[/bold green]")
    else:
        console.print("\n[bold red]❌ Tests failed[/bold red]")
    
    input("\nPress Enter to continue...")


def open_vscode():
    """Open project in VS Code."""
    clear_screen()
    console.print("[green]📝 Opening project in VS Code...[/green]")
    
    try:
        subprocess.run(["code", str(PROJECT_ROOT)])
        console.print("[bold green]✅ VS Code launched[/bold green]")
    except FileNotFoundError:
        console.print("[bold red]❌ VS Code not found in PATH[/bold red]")
    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")
    
    input("\nPress Enter to continue...")


# ============================================================================
# MENU SYSTEM
# ============================================================================

def show_menu():
    """Display the main menu."""
    clear_screen()
    
    if RICH_AVAILABLE:
        # Beautiful Rich menu
        table = Table(title="\n🚀 SAS TRANSLATOR - COMMAND CENTER", 
                      title_style="bold cyan",
                      border_style="green",
                      show_header=False,
                      box=None)
        
        table.add_row("[1] 🚀  Start Local Development", style="white")
        table.add_row("[2] 🛑  Stop Local Services", style="white")
        table.add_row("[3] ☁️  Deploy to Hetzner", style="white")
        table.add_row("[4] 🧪  Run Tests", style="white")
        table.add_row("[5] 📝  Open in VS Code", style="white")
        table.add_row("[6] ❌  Exit", style="white")
        
        console.print(table)
    else:
        # Simple fallback menu
        console.print("\n" + "="*50)
        console.print("SAS TRANSLATOR - COMMAND CENTER".center(50))
        console.print("="*50)
        console.print("\n1. Start Local Development")
        console.print("2. Stop Local Services")
        console.print("3. Deploy to Hetzner")
        console.print("4. Run Tests")
        console.print("5. Open in VS Code")
        console.print("6. Exit")
        console.print("="*50)


def main():
    """Main entry point."""
    # Check if scripts directory exists
    if not SCRIPTS_DIR.exists():
        console.print(f"[bold red]❌ Scripts directory not found: {SCRIPTS_DIR}[/bold red]")
        console.print("[yellow]Please create the directory and add your PowerShell scripts.[/yellow]")
        sys.exit(1)
    
    while True:
        show_menu()
        
        if RICH_AVAILABLE:
            choice = Prompt.ask("\nEnter your choice", choices=["1", "2", "3", "4", "5", "6"])
        else:
            choice = input("\nEnter your choice: ").strip()
        
        if choice == "1":
            start_local()
        elif choice == "2":
            stop_local()
        elif choice == "3":
            deploy()
        elif choice == "4":
            run_tests()
        elif choice == "5":
            open_vscode()
        elif choice == "6":
            console.print("\n[bold cyan]Goodbye! 👋[/bold cyan]")
            break
        else:
            console.print("[bold red]Invalid choice. Press Enter to continue...[/bold red]")
            input()


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[bold cyan]Goodbye! 👋[/bold cyan]")
        sys.exit(0)