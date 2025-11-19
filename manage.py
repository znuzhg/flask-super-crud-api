from __future__ import annotations

import click
from flask.cli import with_appcontext

from app import create_app
from services.user_service import register_user


app = create_app()


@app.cli.command("create-admin")
@click.option("--name", required=True)
@click.option("--email", required=True)
@click.option("--password", required=True)
@with_appcontext
def create_admin(name: str, email: str, password: str) -> None:
    user = register_user(name=name, email=email, password=password, role="admin")
    click.echo(f"Admin created: {user.id} {user.email}")


@app.cli.command("seed-demo-data")
@with_appcontext
def seed_demo_data() -> None:
    users = [
        ("Alice", "alice@example.com"),
        ("Bob", "bob@example.com"),
        ("Carol", "carol@example.com"),
    ]
    for n, e in users:
        try:
            register_user(name=n, email=e, password="passw0rd", role="user")
        except Exception:
            pass
    click.echo("Seeded demo users")

