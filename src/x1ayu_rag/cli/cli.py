import click
import os
import time
import inquirer
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from x1ayu_rag.db.sqlite import initialize_db, get_conn
from x1ayu_rag.chain.chain import get_chain
from x1ayu_rag.service.ingest_service import IngestService
from x1ayu_rag.service.search_service import SearchService
from x1ayu_rag.repository.document_repository import DocumentRepository
from datetime import datetime, timezone
from x1ayu_rag.config.app_config import update_config, load_config

import sys
from functools import wraps

console = Console()

def check_initialized(f):
    """Decorator to check if RAG environment is initialized."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        db_file = os.path.join(".x1ayu_rag", "sqlite.db")
        if not os.path.exists(db_file):
            console.print("[red]Error: RAG environment not initialized.[/red]")
            console.print("Please run [bold]rag init[/bold] first.")
            sys.exit(1)
        return f(*args, **kwargs)
    return wrapper

def _init_env():
    """初始化 RAG 运行环境（创建目录并初始化数据库）"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="Initializing environment...", total=None)
        
        os.makedirs(".x1ayu_rag", exist_ok=True)
        db_file = os.path.join(".x1ayu_rag", "sqlite.db")
        
        if os.path.exists(db_file):
            time.sleep(0.5)  # Simulate work for better UX
            progress.update(task, description="Environment already initialized")
        else:
            initialize_db()
            time.sleep(0.5)  # Simulate work
            
    console.print("[green]✓ RAG environment initialized.[/green]")

def _configure_model(model_type: str, current_config: dict = None):
    """交互式配置模型"""
    current_config = current_config or {}
    
    console.print(f"\n[bold blue]Configure {model_type} Model[/bold blue]")
    
    # Provider selection with inquirer
    questions = [
        inquirer.List('provider',
                      message=f"Select {model_type} provider",
                      choices=['ollama', 'openai'],
                      default=current_config.get("provider", "ollama")
                      ),
    ]
    answers = inquirer.prompt(questions)
    provider = answers['provider']
    
    # Model name
    default_model = current_config.get("model")
    if not default_model:
        default_model = "llama3" if provider == "ollama" else "gpt-3.5-turbo"
        
    model = click.prompt(
        f"Enter {model_type} model name",
        default=default_model
    )
    
    # Base URL
    default_base_url = current_config.get("base_url")
    if not default_base_url:
        default_base_url = "http://localhost:11434" if provider == "ollama" else "https://api.openai.com/v1"
        
    base_url = click.prompt(
        f"Enter {model_type} base URL",
        default=default_base_url
    )
    
    # API Key
    api_key = current_config.get("api_key")
    if provider == "openai":
        api_key = click.prompt(
            f"Enter {model_type} API key",
            hide_input=True,
            default=api_key or ""
        )
    else:
        # No API key needed for Ollama, but we'll allow updating it if someone really wants to
        # According to requirements: "当选择ollama时，不需要用户填写api_key"
        # We will set it to empty string or keep existing if not prompting
        api_key = ""

    return {
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "api_key": api_key
    }

@click.group()
def cli():
    """My Note RAG Tool - A CLI for managing and querying your personal knowledge base."""
    pass

@cli.command()
@click.option('--chat-provider', type=click.Choice(["ollama", "openai"]), help="Chat provider")
@click.option('--chat-model', help="Chat model")
@click.option('--chat-base-url', help="Chat base URL")
@click.option('--chat-api-key', help="Chat API key")
@click.option('--emb-provider', type=click.Choice(["ollama", "openai"]), help="Embedding provider")
@click.option('--emb-model', help="Embedding model")
@click.option('--emb-base-url', help="Embedding base URL")
@click.option('--emb-api-key', help="Embedding API key")
def init(chat_provider, chat_model, chat_base_url, chat_api_key, 
         emb_provider, emb_model, emb_base_url, emb_api_key):
    """Initialize RAG environment and configure models."""
    _init_env()
    
    # If any flags are provided, use non-interactive mode for those parts
    # Otherwise, enter interactive mode
    is_interactive = not any([chat_provider, chat_model, chat_base_url, chat_api_key,
                            emb_provider, emb_model, emb_base_url, emb_api_key])
    
    if is_interactive:
        if click.confirm("\nWould you like to configure models now?", default=True):
            chat_config = _configure_model("Chat")
            emb_config = _configure_model("Embedding")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task(description="Saving configuration...", total=None)
                update_config({
                    "chat": chat_config,
                    "embedding": emb_config
                })
                time.sleep(0.5)
                
            console.print("[green]✓ Configuration saved successfully![/green]")
    else:
        # Non-interactive mode (use provided flags)
        update_config({
            "chat": {
                "provider": chat_provider,
                "model": chat_model,
                "base_url": chat_base_url,
                "api_key": chat_api_key,
            },
            "embedding": {
                "provider": emb_provider,
                "model": emb_model,
                "base_url": emb_base_url,
                "api_key": emb_api_key,
            },
        })
        console.print("[green]Model configuration saved.[/green]")

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@check_initialized
def add(path):
    """Add files or directory to RAG."""
    target = Path(path)
    if target.is_dir():
        _add_path_recursive(target.absolute())
    else:
        _add_file(str(target))

def _add_file(file_path: str):
    """新增或更新单个文件到系统"""
    service = IngestService()
    action, uuid = service.add_or_update(file_path)
    # 移除 Rich 标记语法，确保 [action] 能正常显示
    console.print(f"\\[{action}] {os.path.basename(file_path)} uuid={uuid}")

def _add_path_recursive(p: Path):
    """递归处理目录下所有 .md 文件，判断新增/更新"""
    md_files = [str(fp) for fp in p.rglob("*.md")]
    
    service = IngestService()
    if md_files:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description=f"Processing {len(md_files)} files...", total=None)
            successes, failures = service.add_or_update_many(md_files)
        
        cwd = os.getcwd()
        for fp, action, uuid in successes:
            rel = os.path.relpath(fp, cwd)
            # 移除 Rich 标记语法，确保 [action] 能正常显示
            console.print(f"\\[{action}] {rel} uuid={uuid}")
        for fp, err in failures:
            rel = os.path.relpath(fp, cwd)
            console.print(f"[red][error] {rel}: {err}[/red]")
    else:
        console.print("No markdown files found under directory; checking deletions...")
    
    # 删除文件系统中已缺失的文档
    _remove_missing_under_path(str(p.resolve()))

def _remove_missing_under_path(root: str):
    """检测数据库中文档在文件系统是否已删除，补偿删除记录与索引"""
    repo = DocumentRepository()
    abs_root = os.path.abspath(root)
    rel_root = os.path.relpath(abs_root, os.getcwd())
    docs = repo.list_all() if rel_root in (".", "") else repo.list_by_path_prefix(rel_root)
    service = IngestService(repo)
    removed = 0
    
    for doc in docs:
        if rel_root in (".", ""):
            fs_path = os.path.join(abs_root, doc.path, doc.name)
        else:
            if not (doc.path == rel_root or doc.path.startswith(f"{rel_root}/")):
                continue
            rel_suffix = os.path.relpath(doc.path, rel_root)
            fs_path = os.path.join(abs_root, "" if rel_suffix == "." else rel_suffix, doc.name)
        
        if not os.path.exists(fs_path):
            service.repo.delete_by_uuid(doc.uuid)
            removed += 1
            rel_path = os.path.relpath(fs_path, abs_root)
            console.print(f"[yellow][deleted] {rel_path} uuid={doc.uuid}[/yellow]")
            
    if removed == 0:
        console.print("No deletions detected.")

@cli.command()
@click.argument('query')
@click.option('-k', default=2, help="Number of similar results")
@check_initialized
def select(query, k):
    """Query similar data."""
    service = SearchService()
    results = service.search(query, k)
    
    for doc, score in results:
        meta = doc.metadata or {}
        dir_path = meta.get("dir_path", "")
        file_name = meta.get("file_name", "")
        mk_struct = meta.get("mk_struct", "")
        sim = f"{score:3f}"
        left = f"{dir_path}/{file_name}" if dir_path else file_name
        right = f"{mk_struct}"
        
        console.print(f"\n[bold]File:[/bold] {left} | [bold]Structure:[/bold] {right} | [bold]Score:[/bold] {sim}")
        console.print("-" * 80)
        console.print(doc.page_content)
        console.print("-" * 80)

@cli.command()
@click.argument('query')
@click.option('-m', '--mode', type=click.Choice(["debug"]), help="Mode for RAG chain")
@click.option('-k', default=2, help="Top-K similar chunks")
@check_initialized
def chain(query, mode, k):
    """Run RAG chain with query."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="Thinking...", total=None)
        chain_obj = get_chain(mode)
        result = chain_obj.invoke({"question": query})
        
    console.print("\n[bold green]================ Chain Result ================[/bold green]")
    console.print(result)

@cli.command()
@check_initialized
def show():
    """Print documents table."""
    cursor = get_conn().cursor()
    cursor.execute("SELECT name, path, created_at, updated_at FROM documents ORDER BY path, name")
    rows = cursor.fetchall()
    cursor.close()
    
    if not rows:
        console.print("documents is empty.")
        return
        
    # Using Rich Table for better formatting
    from rich.table import Table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("NAME")
    table.add_column("PATH")
    table.add_column("CREATED")
    table.add_column("UPDATED")
    
    def fmt_dt(v: str) -> str:
        if not v:
            return "-"
        vs = str(v).strip()
        if vs.isdigit():
            try:
                dt_utc = datetime.utcfromtimestamp(int(vs)).replace(tzinfo=timezone.utc)
                return dt_utc.astimezone().strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return vs
        try:
            try:
                dt_naive = datetime.strptime(vs, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                dt_naive = datetime.fromisoformat(vs)
            dt_utc = dt_naive.replace(tzinfo=timezone.utc) if dt_naive.tzinfo is None else dt_naive.astimezone(timezone.utc)
            return dt_utc.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return vs

    for r in rows:
        table.add_row(
            r['name'],
            r['path'],
            fmt_dt(r['created_at']),
            fmt_dt(r['updated_at'])
        )
        
    console.print(table)

@cli.group(invoke_without_command=True)
@click.pass_context
def config(ctx):
    """Manage configuration."""
    if ctx.invoked_subcommand is None:
        # 默认行为：进入交互式配置更新（与 update 逻辑一致）
        # 这里我们引导用户使用 'rag config update' 或 'rag config show'
        # 或者为了兼容性，保留原来的交互式配置逻辑，但作为默认行为
        
        # 检查初始化状态
        db_file = os.path.join(".x1ayu_rag", "sqlite.db")
        if not os.path.exists(db_file):
            console.print("[red]Error: RAG environment not initialized.[/red]")
            console.print("Please run [bold]rag init[/bold] first.")
            sys.exit(1)
            
        update_interactive()

@config.command()
@check_initialized
def show():
    """Show current configuration."""
    cfg = load_config()
    from rich.table import Table
    
    table = Table(title="Current Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Section", style="cyan")
    table.add_column("Key", style="green")
    table.add_column("Value", style="yellow")
    
    def mask_key(k, v):
        if "api_key" in k and v:
            return v[:3] + "****" + v[-4:] if len(v) > 8 else "****"
        return str(v)

    # Chat Config
    chat_cfg = cfg.get("chat", {})
    for k, v in chat_cfg.items():
        table.add_row("Chat", k, mask_key(k, v))
        
    # Embedding Config
    emb_cfg = cfg.get("embedding", {})
    for k, v in emb_cfg.items():
        table.add_row("Embedding", k, mask_key(k, v))
        
    # Prompt Config
    prompt_cfg = cfg.get("prompt", {})
    for k, v in prompt_cfg.items():
        table.add_row("Prompt", k, str(v))
        
    console.print(table)

@config.command()
@click.option('--chat-provider', type=click.Choice(["ollama", "openai"]), help="Chat provider")
@click.option('--chat-model', help="Chat model")
@click.option('--chat-base-url', help="Chat base URL")
@click.option('--chat-api-key', help="Chat API key")
@click.option('--emb-provider', type=click.Choice(["ollama", "openai"]), help="Embedding provider")
@click.option('--emb-model', help="Embedding model")
@click.option('--emb-base-url', help="Embedding base URL")
@click.option('--emb-api-key', help="Embedding API key")
@click.option('--sys-prompt', help="Custom system prompt for the RAG chain")
@check_initialized
def update(chat_provider, chat_model, chat_base_url, chat_api_key, 
           emb_provider, emb_model, emb_base_url, emb_api_key, sys_prompt):
    """Update configuration."""
    # Check if any flags are provided
    has_flags = any([chat_provider, chat_model, chat_base_url, chat_api_key,
                     emb_provider, emb_model, emb_base_url, emb_api_key, sys_prompt])
    
    if not has_flags:
        update_interactive()
    else:
        # Non-interactive mode
        updates = {}
        if any([chat_provider, chat_model, chat_base_url, chat_api_key]):
            updates["chat"] = {
                "provider": chat_provider,
                "model": chat_model,
                "base_url": chat_base_url,
                "api_key": chat_api_key
            }
        
        if any([emb_provider, emb_model, emb_base_url, emb_api_key]):
            updates["embedding"] = {
                "provider": emb_provider,
                "model": emb_model,
                "base_url": emb_base_url,
                "api_key": emb_api_key
            }
            
        if sys_prompt:
            updates["prompt"] = {"sys_prompt": sys_prompt}
            
        update_config(updates)
        console.print("[green]Configuration updated.[/green]")

def update_interactive():
    """Interactive configuration update helper."""
    current_config = load_config()
    
    updates = {}
    
    if click.confirm("Configure Chat Model?", default=True):
        updates["chat"] = _configure_model("Chat", current_config.get("chat"))
        
    if click.confirm("Configure Embedding Model?", default=True):
        updates["embedding"] = _configure_model("Embedding", current_config.get("embedding"))
        
    if click.confirm("Configure System Prompt?", default=False):
        default_prompt = current_config.get("prompt", {}).get("sys_prompt", "")
        new_prompt = click.prompt("Enter system prompt", default=default_prompt)
        updates["prompt"] = {"sys_prompt": new_prompt}
        
    if updates:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="Updating configuration...", total=None)
            update_config(updates)
            time.sleep(0.5)
        console.print("[green]Configuration updated successfully.[/green]")
    else:
        console.print("No changes made.")

if __name__ == "__main__":
    cli()
