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
from x1ayu_rag.exceptions import NotInitializedError, ConfigurationError, ModelConnectionError, DatabaseError
from x1ayu_rag.config.constants import SQLITE_DB_PATH, DEFAULT_CONFIG_DIR

import sys
from functools import wraps

console = Console()

def check_initialized(f):
    """装饰器：检查 RAG 环境是否已初始化"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not os.path.exists(SQLITE_DB_PATH):
            raise NotInitializedError("RAG 环境未初始化。")
        return f(*args, **kwargs)
    return wrapper

def handle_errors(f):
    """装饰器：处理 RAG 特定的异常"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except NotInitializedError:
            console.print("fatal: RAG environment not initialized. Please run 'rag init' first.")
            sys.exit(1)
        except ConfigurationError as e:
            console.print(f"[red]配置错误: {e.message}[/red]")
            console.print("请运行 [bold]rag config update[/bold] 修复配置。")
            sys.exit(1)
        except ModelConnectionError as e:
            console.print(f"[red]模型连接错误: {e.message}[/red]")
            console.print("[yellow]提示: 请检查您的模型服务（如 Ollama）是否正在运行并可访问。[/yellow]")
            if click.confirm("是否现在配置模型？", default=True):
                 _main_config_menu()
            sys.exit(1)
        except DatabaseError as e:
            console.print(f"[red]数据库错误: {e.message}[/red]")
            if e.original_error:
                 console.print(f"[dim]详细信息: {e.original_error}[/dim]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]未预期的错误: {e}[/red]")
            sys.exit(1)
    return wrapper

def _init_env():
    """初始化 RAG 运行环境（创建目录并初始化数据库）
    
    该函数执行以下操作：
    1. 创建配置目录（如果不存在）。
    2. 检查 SQLite 数据库是否存在。
    3. 如果不存在，则执行数据库初始化脚本 (db.sql)。
    4. 显示初始化进度的 Spinner。
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="正在初始化环境...", total=None)
        
        os.makedirs(DEFAULT_CONFIG_DIR, exist_ok=True)
        
        if os.path.exists(SQLITE_DB_PATH):
            time.sleep(0.5)  # 模拟工作以提升用户体验
            progress.update(task, description="环境已初始化")
        else:
            initialize_db()
            time.sleep(0.5)  # 模拟工作

def _main_config_menu(startup_message: str = None):
    """主配置菜单循环"""
    first_run = True
    while True:
        click.clear()  # 清屏
        if first_run and startup_message:
            console.print(startup_message)
            first_run = False

        questions = [
            inquirer.List('choice',
                          message="",  # 移除提示文本
                          choices=['Chat', 'Embedding', 'Exit'],
                          ),
        ]
        answers = inquirer.prompt(questions)
        choice = answers['choice']
        
        if choice == 'Exit':
            break
            
        _model_config_menu(choice)

def _model_config_menu(model_type: str):
    """模型配置菜单循环"""
    while True:
        click.clear()  # 清屏
        current_config = load_config()
        model_key = model_type.lower()
        config_data = current_config.get(model_key, {})
        
        console.print(f"Current {model_type} Configuration", style="bold magenta")
        from rich.table import Table
        # 创建一个无边框或极简边框的表格，以匹配用户期望的简洁样式
        # box=None 去除所有边框，或者使用简单的 ASCII 边框
        from rich import box
        table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Key", style="green")
        table.add_column("Value", style="yellow")
        
        for k, v in config_data.items():
            val_str = str(v)
            if "api_key" in k and v:
                val_str = v[:3] + "****" + v[-4:] if len(v) > 8 else "****"
            table.add_row(k, val_str)
            
        # 如果是 Chat 模型，额外显示 System Prompt
        if model_type == "Chat":
            prompt_config = current_config.get("chat", {})
            sys_prompt = prompt_config.get("sys_prompt", "")
            # 为了在表格中区分，可以使用不同的颜色或前缀，或者直接列出
            # 这里将其视为 Chat 配置的一部分展示
            table.add_row("System Prompt", str(sys_prompt))

        console.print(table)
        console.print() # 空行

        # 选项列表
        choices = ["Provider", "Model", "Base URL", "API Key"]
        if model_type == "Chat":
            choices.append("System Prompt")
        choices.append("Back")
        
        questions = [
            inquirer.List('field',
                          message=f"选择要修改的配置项 ({model_type})",
                          choices=choices,
                          ),
        ]
        answers = inquirer.prompt(questions)
        field = answers['field']
        
        if field == "Back":
            break
            
        if field == "System Prompt":
            prompt_config = current_config.get("chat", {})
            default_val = prompt_config.get("sys_prompt", "")
            new_val = click.prompt("Enter new system prompt", default=default_val)
            update_config({"chat": {"sys_prompt": new_val}})
            console.print(f"[green]Updated System Prompt successfully.[/green]")
            time.sleep(1)
            continue
            
        key_map = {
            "Provider": "provider",
            "Model": "model",
            "Base URL": "base_url",
            "API Key": "api_key"
        }
        
        key = key_map[field]
        
        if key == "provider":
            q_prov = [
                inquirer.List('provider',
                              message=f"Select {model_type} provider",
                              choices=['ollama', 'openai'],
                              default=config_data.get("provider", "ollama")
                              ),
            ]
            ans_prov = inquirer.prompt(q_prov)
            new_val = ans_prov['provider']
        else:
            default_val = config_data.get(key, "")
            if key == "api_key":
                 new_val = click.prompt(f"Enter new {field}", default=default_val, hide_input=True)
            else:
                 new_val = click.prompt(f"Enter new {field}", default=default_val)
        
        # 更新配置
        updates = {model_key: {key: new_val}}
        update_config(updates)
        console.print(f"[green]Updated {field} successfully.[/green]")
        time.sleep(1) # 短暂暂停以显示成功消息，然后清屏刷新

@click.group()
def cli():
    """My Note RAG Tool - 用于管理和查询个人知识库的 CLI 工具。"""
    pass

@cli.command()
@click.option('--chat-provider', type=click.Choice(["ollama", "openai"]), help="聊天模型提供商")
@click.option('--chat-model', help="聊天模型名称")
@click.option('--chat-base-url', help="聊天模型基础 URL")
@click.option('--chat-api-key', help="聊天模型 API 密钥")
@click.option('--emb-provider', type=click.Choice(["ollama", "openai"]), help="Embedding 模型提供商")
@click.option('--emb-model', help="Embedding 模型名称")
@click.option('--emb-base-url', help="Embedding 模型基础 URL")
@click.option('--emb-api-key', help="Embedding 模型 API 密钥")
@handle_errors
def init(chat_provider, chat_model, chat_base_url, chat_api_key, 
         emb_provider, emb_model, emb_base_url, emb_api_key):
    """初始化 RAG 环境并配置模型。"""
    _init_env()
    
    # 如果提供了任何标志，则对这些部分使用非交互模式
    # 否则，进入交互模式
    is_interactive = not any([chat_provider, chat_model, chat_base_url, chat_api_key,
                            emb_provider, emb_model, emb_base_url, emb_api_key])
    
    if is_interactive:
        # 直接进入配置菜单，不再询问
        _main_config_menu(startup_message="[green]✓ RAG 环境初始化完成。[/green]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="正在保存配置...", total=None)
            time.sleep(0.5)
            
        console.print("[green]✓ 配置保存成功！[/green]")
    else:
        # 非交互模式（使用提供的标志）
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
        console.print("[green]模型配置已保存。[/green]")

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@handle_errors
@check_initialized
def add(path):
    """添加文件或目录到 RAG 系统。"""
    target = Path(path)
    if target.is_dir():
        _add_path_recursive(target.absolute())
    else:
        _add_file(str(target))

def _add_file(file_path: str):
    """新增或更新单个文件到系统"""
    service = IngestService()
    # 错误现在由装饰器处理或抛出给装饰器
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
            task = progress.add_task(description=f"正在处理 {len(md_files)} 个文件...", total=None)
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
        console.print("目录下未找到 Markdown 文件；正在检查删除...")
    
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

@cli.command()
@click.argument('query')
@click.option('-k', default=2, help="相似结果数量")
@handle_errors
@check_initialized
def select(query, k):
    """查询相似数据。"""
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
        
        console.print(f"\n[bold]文件:[/bold] {left} | [bold]结构:[/bold] {right} | [bold]分数:[/bold] {sim}")
        console.print("-" * 80)
        console.print(doc.page_content)
        console.print("-" * 80)

@cli.command()
@click.argument('query')
@click.option('-m', '--mode', type=click.Choice(["debug"]), help="RAG 链模式")
@click.option('-k', default=2, help="前 K 个相似块")
@handle_errors
@check_initialized
def chain(query, mode, k):
    """使用查询运行 RAG 链。"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="思考中...", total=None)
        # 传递 k 参数给 get_chain
        chain_obj = get_chain(mode, k=k)
        # invoke 时传递 k 参数，确保运行时动态生效（虽然 get_chain 已经处理了，双重保险）
        result = chain_obj.invoke({"question": query, "k": k})
        
    console.print("\n[bold green]================ 链执行结果 ================[/bold green]")
    console.print(result)

@cli.command()
@handle_errors
@check_initialized
def show():
    """打印文档表格。"""
    repo = DocumentRepository()
    rows = repo.list_all_with_details()
    
    if not rows:
        console.print("文档列表为空。")
        return
        
    # 使用 Rich Table 进行更好的格式化
    from rich.table import Table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("名称")
    table.add_column("路径")
    table.add_column("创建时间")
    table.add_column("更新时间")
    
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
@handle_errors
def config(ctx):
    """管理配置。"""
    if ctx.invoked_subcommand is None:
        # 默认行为：进入交互式配置更新（与 update 逻辑一致）
        
        # 检查初始化状态
        if not os.path.exists(SQLITE_DB_PATH):
            raise NotInitializedError("RAG 环境未初始化。")
            
        _main_config_menu()

@config.command()
@handle_errors
@check_initialized
def show():
    """显示当前配置。"""
    cfg = load_config()
    from rich.table import Table
    
    table = Table(title="当前配置", show_header=True, header_style="bold magenta")
    table.add_column("部分", style="cyan")
    table.add_column("键", style="green")
    table.add_column("值", style="yellow")
    
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
        
    # Prompt Config - Legacy or if we want to display it?
    # User moved sys_prompt to chat, so we might not need this section unless there are other prompt settings.
    # But for backward compatibility or clarity, let's just check if it exists and is not empty.
    prompt_cfg = cfg.get("prompt", {})
    if prompt_cfg:
        for k, v in prompt_cfg.items():
            table.add_row("Prompt (Legacy)", k, str(v))
        
    console.print(table)

@config.command()
@click.option('--chat-provider', type=click.Choice(["ollama", "openai"]), help="聊天模型提供商")
@click.option('--chat-model', help="聊天模型名称")
@click.option('--chat-base-url', help="聊天模型基础 URL")
@click.option('--chat-api-key', help="聊天模型 API 密钥")
@click.option('--emb-provider', type=click.Choice(["ollama", "openai"]), help="Embedding 模型提供商")
@click.option('--emb-model', help="Embedding 模型名称")
@click.option('--emb-base-url', help="Embedding 模型基础 URL")
@click.option('--emb-api-key', help="Embedding 模型 API 密钥")
@click.option('--sys-prompt', help="RAG 链的自定义系统提示词")
@handle_errors
@check_initialized
def update(chat_provider, chat_model, chat_base_url, chat_api_key, 
           emb_provider, emb_model, emb_base_url, emb_api_key, sys_prompt):
    """更新配置。"""
    # 检查是否提供了任何标志
    has_flags = any([chat_provider, chat_model, chat_base_url, chat_api_key,
                     emb_provider, emb_model, emb_base_url, emb_api_key, sys_prompt])
    
    if not has_flags:
        _main_config_menu()
    else:
        # 非交互模式
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
            updates["chat"] = updates.get("chat", {})
            updates["chat"]["sys_prompt"] = sys_prompt
            
        update_config(updates)
        console.print("[green]配置已更新。[/green]")

if __name__ == "__main__":
    cli()
