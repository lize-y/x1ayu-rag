import click
import sys
from functools import wraps
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from x1ayu_rag_v2.api.ingest_api import IngestAPI
from x1ayu_rag_v2.api.system_api import SystemAPI
from x1ayu_rag_v2.cli.ui import main_config_menu
from x1ayu_rag_v2.cli.decorators import require_init

console = Console()
system_api = SystemAPI()

def _init_env():
    """初始化 RAG 运行环境（创建目录并初始化数据库）"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="正在初始化环境...", total=None)
        
        success, message = system_api.initialize_system()
        
        if success:
            progress.update(task, description="环境已初始化")
        else:
            # 如果初始化失败（例如已存在），通常是正常的，这里我们不打断流程
            pass



@click.group()
def cli():
    """x1ayu RAG v2 CLI"""
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
        __main_config_menu(startup_message="[green]✓ RAG 环境初始化完成。[/green]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="正在保存配置...", total=None)
            
        console.print("[green]✓ 配置保存成功！[/green]")
    else:
        # 非交互模式（使用提供的标志）
        updates = {}
        if any([chat_provider, chat_model, chat_base_url, chat_api_key]):
            updates["chat"] = {
                "provider": chat_provider,
                "model": chat_model,
                "base_url": chat_base_url,
                "api_key": chat_api_key,
            }
        if any([emb_provider, emb_model, emb_base_url, emb_api_key]):
            updates["embedding"] = {
                "provider": emb_provider,
                "model": emb_model,
                "base_url": emb_base_url,
                "api_key": emb_api_key,
            }
        
        system_api.update_configuration(updates)
        console.print("[green]模型配置已保存。[/green]")


@cli.command()
@require_init
def config(ctx):
    """管理系统配置"""
    if ctx.invoked_subcommand is None:
        # 默认行为：进入交互式配置更新
        main_config_menu()


@cli.command()
@click.argument('file_path')
@require_init
def add(file_path):
    """添加文档"""
    api = IngestAPI()
    success, message = api.ingest_document(file_path)
    if success:
        click.echo(click.style(message, fg='green'))
    else:
        click.echo(click.style(message, fg='red'))

