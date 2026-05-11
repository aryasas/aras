import click
from arasCore.lib.core.extensions import db

def register_auth_commands(aras):
    @aras.command("csu", help="Create a user with Admin role on database")
    @click.option("--username", prompt="User name")
    @click.option("--email", prompt="User email")
    @click.option(
        "--password",
        prompt="User password",
        hide_input="True",
        confirmation_prompt=True,
    )
    def csu(username, email, password):
        """Install a default admin user."""
        from arasCore.auth import User, create_user
        if User.query.filter_by(email=email).first():
            click.echo("Email already exists.")
            return
        u = create_user(username, email, password, is_admin=True)
        click.echo(f"Created admin user: {u.username}")

    @aras.command("reset", help="Reset Password")
    @click.option("--username", prompt="User name")
    @click.option(
        "--password",
        prompt="New password",
        hide_input="True",
    )
    def reset(username, password):
        """Reset a user password"""
        from arasCore.auth import User
        try:
            user = User.query.filter_by(username=username).first()
            if not user:
                click.echo("User not found.")
                return
            user.set_password(password)
            db.session.commit()
            click.echo("Password reset successfully.")
        except Exception as e:
            click.echo(f"Error: {e}")
