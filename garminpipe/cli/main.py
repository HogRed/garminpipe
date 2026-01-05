from __future__ import annotations

from getpass import getpass

import typer
from rich import print

from garminpipe.api import GarminPipe

app = typer.Typer(add_completion=False)
auth_app = typer.Typer()
app.add_typer(auth_app, name="auth")

# --- commands ---
@auth_app.command("login")
def auth_login(email: str = typer.Option(..., help="Garmin account email")):
    """
    Creates/refreshes a garth session and saves it locally.
    MFA is supported; garth may prompt in terminal unless you override prompt_mfa. :contentReference[oaicite:5]{index=5}
    """
    password = getpass("Garmin password: ")
    pipe = GarminPipe()
    pipe.login(email=email, password=password, prompt_mfa=lambda: input("MFA code (if prompted): ").strip())
    print(f"[green]Session saved to[/green] {pipe.config.session_dir}")

@app.command("sync")
def sync_cmd():
    pipe = GarminPipe()

    # resume if possible; if not, user should run auth login
    if not pipe.resume():
        print("[yellow]No session found. Run: garminpipe auth login --email you@example.com[/yellow]")
        raise typer.Exit(code=1)

    df_new = pipe.sync()
    print(f"[green]Synced.[/green] New/updated rows: {len(df_new)}")
    print(f"Data dir: {pipe.config.data_dir}")


@app.command("summary")
def summary_cmd():
    pipe = GarminPipe()
    df = pipe.clean()
    wk = pipe.weekly(df)
    print(wk.tail(10).to_string(index=False))