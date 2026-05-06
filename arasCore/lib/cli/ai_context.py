# -*- coding: utf-8 -*-
import os
import click
import re

def compress_code(code: str) -> str:
    # Remove single line comments
    code = re.sub(r'#.*', '', code)
    # Remove multi-line comments
    code = re.sub(r'"""[\s\S]*?"""', '', code)
    code = re.sub(r"'''[\s\S]*?'''", '', code)
    # Remove extra whitespace
    lines = [line.strip() for line in code.splitlines() if line.strip()]
    return "\n".join(lines)

@click.group()
def ai_context():
    """AI Token Optimization commands."""
    pass

@ai_context.command()
@click.option("--output", "-o", help="Output file path")
def optimize(output):
    """Generate a compressed context string for LLMs."""
    context = []
    project_root = os.getcwd()
    
    # Files to include
    include_dirs = ['arasCore', 'app', 'templates']
    include_files = ['run.py', 'config.py', 'requirements.txt', 'GEMINI.md']
    exclude_extensions = ['.pyc', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.woff', '.woff2', '.ttf', '.eot']

    click.echo("Gathering and optimizing context...")

    for item in include_files:
        path = os.path.join(project_root, item)
        if os.path.exists(path):
            with open(path, 'r', errors='ignore') as f:
                content = f.read()
                context.append(f"--- FILE: {item} ---\n{compress_code(content)}")

    for d in include_dirs:
        for root, _, files in os.walk(os.path.join(project_root, d)):
            if '__pycache__' in root: continue
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in exclude_extensions: continue
                
                rel_path = os.path.relpath(os.path.join(root, file), project_root)
                with open(os.path.join(root, file), 'r', errors='ignore') as f:
                    content = f.read()
                    context.append(f"--- FILE: {rel_path} ---\n{compress_code(content)}")

    final_string = "\n\n".join(context)
    
    if output:
        with open(output, 'w') as f:
            f.write(final_string)
        click.echo(f"Optimized context saved to {output} ({len(final_string)} chars)")
    else:
        # Just print stats and a preview
        click.echo(f"Total optimized context size: {len(final_string)} chars")
        click.echo("Use -o <file> to save to a file.")

def register_ai_commands(cli):
    cli.add_command(ai_context)
