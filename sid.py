import argparse
import sys
import json
from rich import print 
from termcolor import colored
from apiConnection import authenticate, getAgentinfo 
import re 
from export import exportToExcel
import threading 
import time 
import emoji
from rich.console import Console 

console = Console() 


PATTERN =  r"^all$|^\d+-\d+$|^\d+(,\d+)*$"

def validate_agent(value):
    if not re.match(PATTERN, value):
        raise argparse.ArgumentTypeError(
            f"Invalid value '{value}' for --agent. "
            "It must be 'all', a range like '1-5', or a comma-separated list of numbers like '1,2,3'."
        )
    return value

def load_defaults(config_file="config.json"):

        with open(config_file, 'r') as f:
             config = json.load(f)

        return config 

def create_parser(status):

    parser = argparse.ArgumentParser(description="AMT - Asset management tool")
    parser.add_argument("--username", help="--> wazuh api username")
    parser.add_argument("--password", type=str, help="--> Wazuh api password")
    parser.add_argument("--host", type=str, help="--> IP address and port of host that run wazuh server: eg. https://Wazuh-host:55000")
    parser.add_argument("--agent", type=validate_agent, help=" --> Specify 'all', a range like '1-5', or a list of numbers like '1,2,3'.")
    parser.add_argument("--filename",type=str, help="--> The name of the file to which agent's data exported to")
    
    status['stop'] = True 

    return parser.parse_args() 
   
def spinner_animation(status):
     spinner = ["|","/","-","\\"]

     while not status['stop']:
          for symbol in spinner:
               sys.stdout.write(colored(f"\r{status['status']} {symbol}","blue")) 
               sys.stdout.flush()  
               time.sleep(0.3) 

def main(status_event,defaults):
    asset_data = {}
    args = create_parser(status_event)
    username = args.username or defaults['username']
    password = args.password or defaults['password']

    host = args.host or f"https://{defaults['host']}:{defaults['port']}" 
    
    agents = args.agent
    fname = args.filename or defaults['filename'] 
    
    status_event['status'] = emoji.emojize("Authenticating... :key:") 
    token = authenticate(username,password,host)

    if token is None:
         status_event['status'] = "Authentication Failed"
         status_event['stop'] = True
         sys.exit(1)

    else:
         if agents is not None:
              agent_args = agents.split(",")

              if agents == "all":
                   status_event['status'] = emoji.emojize("Getting Agents' data ...")
                   agents_data = getAgentinfo(token,host,['all'])

                   try:
                         status_event['status'] = emoji.emojize("Exporting data ... :file_folder:")
                         file_path = exportToExcel(agents_data,fname)
                         console.print(f"[bold green]Agents' data successfully exported to excel and saved here!{emoji.emojize(" :point_right:")} {file_path} [/bold green]")
                   except PermissionError as e:
                         status_event['status'] = "Error exporting to excel file..."
                         print(f"\n{fname} already exist and opened!!. you should close it or provide different filename")
                   except Exception:
                         pass 
                   
                   status_event['stop'] = True 

              else:
                   if "-" in agents:
                        agents_args = [] 
                        try:
                            for index,num in enumerate(agents.split('-')):
                              #   if index != 0:
                                   # agent_args.append(int(num)) 
                              agent_args.append(int(num))
                                

                        except ValueError:
                             print("Value Error")

                        agent_ids = [id for id in range(agent_args[1], agent_args[2]+1)]
                        status_event['status'] = emoji.emojize("Getting Agents' data ...:")
                        agents_data = getAgentinfo(token,host,agent_ids)

                        try:
                             status_event['status'] = emoji.emojize("Exporting data ... :file_folder:")
                             file_path = exportToExcel(agents_data,fname)
                             console.print(f"[bold green]Agents' data successfully exported to excel and saved here!{emoji.emojize(" :point_right:")} {file_path} [/bold green]")
                        except PermissionError as e:
                            status_event['status'] = "Error exporting to excel file..."
                            print(f"\n{fname} already exist and opened!!. you should close it or provide different filename")
                            sys.exit()

                        except Exception:
                              pass 
                             
                   elif "," in agents:
                         agents_arg = [] 

                         try:
                              for index,num in enumerate(agents.split(',')):
                                   agents_arg.append(int(num))
                                   
                         except ValueError:
                              print("Value Error")

                         status_event['status'] = emoji.emojize("Getting Agents' data ... :")
                         agents_data = getAgentinfo(token,host,agents_arg)
                         
                         try:
                             status_event['status'] = emoji.emojize("Exporting data ... :file_folder:")
                             file_path = exportToExcel(agents_data,fname)
                             console.print(f"[bold green]Agents' data successfully exported to excel and saved here!{emoji.emojize(" :point_right:")} {file_path} [/bold green]")

                         except PermissionError as e:
                              status_event['status'] = "Error exporting to excel file..."
                              print(f"\n{fname} already exist and opened!!. you should close it or provide different filename")
                              sys.exit() 

                         except Exception:
                              pass 
                   else:
                        agent_ids = [agents]
                        status_event['status'] = emoji.emojize("Getting Agents' data ... :")
                        agents_data = getAgentinfo(token,host,agent_ids)
                        try:
                             status_event['status'] = emoji.emojize("Exporting data ... :file_folder:")
                             file_path = exportToExcel(agents_data,fname)
                             console.print(f"[bold green]Agents' data successfully exported to excel and saved here!{emoji.emojize(" :point_right:")} {file_path} [/bold green]")

                        except PermissionError as e:
                             status_event['status'] = "Error exporting to excel file..."
                             print(f"\n{fname} already exist and opened!!. you should close it or provide different filename")
                             sys.exit() 

                        except Exception:
                              pass  

         else:
             pass  
         
         status_event['status'] = emoji.emojize("Task completed! :rocket:") 
         
if __name__== "__main__":
   
   defaults = load_defaults()
   status_event = {'status':None,'stop':False} 
#    spinner_thread = threading.Thread(target=spinner_animation,args=(status_event,)) 
   print()
#    spinner_thread.start() 

   main(status_event,defaults)
   
#    spinner_thread.join()
   print() 
   



