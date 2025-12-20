import click
import inquirer
from rich.console import Console
from rich.table import Table
from rich import box
from x1ayu_rag_v2.api.system_api import SystemAPI

console = Console()
system_api = SystemAPI()

def main_config_menu(startup_message: str = None):
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
        if not answers:
            break
            
        choice = answers['choice']
        
        if choice == 'Exit':
            break
            
        model_config_menu(choice)

def model_config_menu(model_type: str):
    """模型配置菜单循环"""
    while True:
        click.clear()  # 清屏
        current_config = system_api.get_config()
        model_key = model_type.lower()
        config_data = current_config.get(model_key, {})
        
        console.print(f"Current {model_type} Configuration", style="bold magenta")
        
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
        if not answers:
            break
            
        field = answers['field']
        
        if field == "Back":
            break
            
        if field == "System Prompt":
            prompt_config = current_config.get("chat", {})
            default_val = prompt_config.get("sys_prompt", "")
            new_val = click.prompt("Enter new system prompt", default=default_val)
            system_api.update_configuration({"chat": {"sys_prompt": new_val}})
            console.print(f"[green]Updated System Prompt successfully.[/green]")
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
            if not ans_prov:
                continue
            new_val = ans_prov['provider']
        else:
            default_val = config_data.get(key, "")
            if key == "api_key":
                 new_val = click.prompt(f"Enter new {field}", default=default_val, hide_input=True)
            else:
                 new_val = click.prompt(f"Enter new {field}", default=default_val)
        
        # 更新配置
        updates = {model_key: {key: new_val}}
        system_api.update_configuration(updates)
        console.print(f"[green]Updated {field} successfully.[/green]")
