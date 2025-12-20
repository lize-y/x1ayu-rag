import click
import sys
from functools import wraps
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from x1ayu_rag.api.ingest_api import IngestAPI
from x1ayu_rag.api.system_api import SystemAPI
from x1ayu_rag.cli.ui import main_config_menu
from x1ayu_rag.cli.decorators import require_init, require_chat_config, require_embedding_config

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
    """x1ayu RAG"""
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
        main_config_menu(startup_message="[green]✓ RAG 环境初始化完成。[/green]")
        
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
def config():
    """管理系统配置"""
    # 默认行为：进入交互式配置更新
    main_config_menu()


@cli.command()
@click.argument('file_path')
@require_init
@require_embedding_config
def add(file_path):
    """添加文档"""
    api = IngestAPI()
    success, message, results = api.ingest_document(file_path)
    if success:
        if results:
            for action, path, detail in results:
                # 使用转义防止rich解析路径中的方括号等
                from rich.markup import escape
                
                # 必须转义 action，因为 [added] 会被 rich 误认为是样式标签
                safe_action = escape(action)
                safe_path = escape(path)
                
                if action == "[error]":
                    console.print(f"[red]{safe_action}[/red] {safe_path} {detail}")
                else:
                    color = "green"
                    if "deleted" in action: color = "red"
                    elif "updated" in action: color = "yellow"
                    elif "skipped" in action: color = "dim blue"
                    
                    console.print(f"[{color}]{safe_action}[/{color}] {safe_path} {detail}")
        else:
            click.echo(click.style(message, fg='green'))
    else:
        click.echo(message)

@cli.command()
@require_init
def show():
    """列出所有已摄取的文档"""
    api = IngestAPI()
    docs = api.list_documents()
    
    if not docs:
        console.print("[yellow]暂无已摄取文档。使用 'rag add <file/dir>' 添加文档。[/yellow]")
        return

    table = Table(title="文档", box=box.ROUNDED)
    table.add_column("Filename", style="cyan")
    table.add_column("Path", style="dim")
    table.add_column("UUID", style="green")
    table.add_column("Hash", style="dim")
    
    for doc in docs:
        table.add_row(
            doc.name,
            doc.path or ".",
            doc.uuid,
            doc.hash[:8] + "..." if doc.hash else "N/A"
        )
        
    console.print(table)
    console.print(f"\n[dim]Total: {len(docs)} documents[/dim]")


@cli.command()
@click.argument('query')
@click.option('-k', default=2, help="相似结果数量")
@require_init
@require_embedding_config
def select(query, k):
    """查询相关分块"""
    from x1ayu_rag.api.query_api import QueryAPI
    api = QueryAPI()
    results = api.search_chunks(query, k)
    
    if not results:
        console.print("[yellow]未找到相关分块。[/yellow]")
        return

    for i, res in enumerate(results, 1):
        content = res["content"]
        meta = res["metadata"]
        
        file_name = meta.get("file_name", "Unknown")
        dir_path = meta.get("dir_path", "")
        mk_struct = meta.get("mk_struct", "")
        
        path_info = f"{dir_path}/{file_name}" if dir_path else file_name
        
        console.print(f"\n[bold cyan]Result #{i}[/bold cyan]")
        console.print(f"[green]File:[/green] {path_info}")
        if mk_struct:
             console.print(f"[blue]Structure:[/blue] {mk_struct}")
        console.print("-" * 40)
        console.print(content)
        console.print("-" * 40)


@cli.command()
@click.argument('query')
@click.option('-m', '--mode', type=click.Choice(["debug"]), help="RAG 链模式")
@click.option('-k', default=2, help="前 K 个相似块")
@require_init
@require_embedding_config
@require_chat_config
def chain(query, mode, k):
    """使用查询运行 RAG 链。"""
    try:
        from x1ayu_rag.chain.rag_chain import RAGChain
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="思考中...", total=None)
            
            rag = RAGChain()
            chain_instance = rag.get_chain(mode=mode, k=k)
            result = chain_instance.invoke({"question": query, "k": k})
            
        console.print("\n[bold green]================ 链执行结果 ================[/bold green]")
        console.print(result)
        
    except Exception as e:
        # 其他未预料的错误
        console.print(f"[red]Error executing chain:[/red] {str(e)}")

