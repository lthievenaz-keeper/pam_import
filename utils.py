## RICH Console styling - can be removed if rich was not imported ##
from rich.console import Console
from rich.markdown import Markdown
## RICH Console styling ##

USE_RICH = False

try:
    console = Console()
    USE_RICH = True
except:
    pass

from json import dump,dumps,loads

def display(text,style=None):
    if USE_RICH:
        console.print(Markdown(text),style=style)
    else:
        print(text)
        
        
def list_items(items,style='italic yellow'):
    for item in items:
        display(f'- {item}',style)
        
        
def handle_prompt(valid_inputs,prompt='Input: '):
    response = input(prompt)
    if response.lower() in valid_inputs:
        return valid_inputs[response]
    display('Invalid input')
    return handle_prompt(valid_inputs,prompt=prompt) 


def validate_file_upload(format,filename=None):
    if not filename:
        filename = input('File path: ')
    try:
        with open(filename,'r') as file:
            if format=='csv':
                from csv import DictReader
                return list(DictReader(file))
            elif format=='json':
                from json import load
                return load(file)
            elif format=='yaml':
                from yaml import safe_load
                return safe_load(file)
                
    except Exception as e:
        display(f'Error: Exception {e} raised','bold red')
        return validate_file_upload(format)


def debug(text,DEBUG):
    if DEBUG:
        print(f'>>DEBUG: {text}')