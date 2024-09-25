from base64 import b64encode
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from rich.console import Console 
import time 
import urllib3
console = Console() 
import pytz 
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sys 

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



def authenticate(username,password,host):
        """Authenticate with Wazuh API and return the JWT token."""  
        url = f"{host}/security/user/authenticate"  
        basic_auth = f"{username}:{password}".encode() 
   
        login_headers = {
                       'Content-Type': "Application/json",
                        'Authorization': f'Basic {b64encode(basic_auth).decode()}'
                 }  
        # wait_animation = animation.wait()
        try:
            # wait_animation.start()
            
            # the program will wait 10 second waiting for response from the server else aborted
            response = requests.post(url, headers=login_headers,verify=False,timeout=10)  
            # Raise an HTTPError for bad response (4xx and 5xx codes) 
            response.raise_for_status

            # check for specific HTTP status codes 

            if response.status_code == 200:  
                token = response.json()['data']['token']  
                return token
            
            elif response.status_code == "401":
                console.print("[bold red] Invalid username or password.[/bold red]") 

            else:  
                console.print(f"[bold red]Unexpected status code received: {response.status_code}[/bold red]")

        except HTTPError as http_err:
            # handle HTTP errors (e.g., 4xx or 5xx)
            if response.status_code == 401:
                console.print("[bold red] Authentication failed: Invalid username or password.[/bold red]")

            elif response.status_code == 403:
                console.print("[bold red]Forbidden: You don't have permission to access this resource[/bold red]") 

            elif response.status_code == 404:
                console.print("[bold red]Not Found: The requested resource does not exist[/bold red]")

            else:

                console.print(f"[bold red]HTTP error occured: {http_err}[/bold red]") 

        # catch errors when the server is down or unreachable 
        except ConnectionError:
            console.print(f"[bold red]Failed to connect to wazuh server: {host}. The server might be down.[/bold red]") 

        # handles when the server is to slow or not responding
        except Timeout:
            console.print("[bold red]Request to Wazuh server timed out. The server might be too slow or not responding[/bold red]")

        # catche any other request-related errors 
        except RequestException as err:
            console.print(f"[bold red]An unexpected error occured: {err}[/bold red]")

        except Exception as e:
            console.print(f"[bold red]An error occured: {response}[/bold red]") 

        return None 

def getAgentinfo(token,host,agents_id):
        agents = {}

        headers = {  
                'Authorization': f'Bearer {token}',  
                 'Content-Type': 'application/json'  
                }  
        url = f"{host}/agents/?pretty=true"
    
        try:
        
            response = requests.get(url, headers=headers,verify=False)  
            # check for specific HTTP status codes 

            if response.status_code == 200:  
                agents_data = response.json()['data']['affected_items']
               
                if len(agents_id) == 1 and agents_id[0] == "all":
                    for agent in agents_data:
                        agent_data = parseAgent(host,agent,token)
                        agents[f'{agent_data['id']}'] = agent_data 

                else:
                   for id in agents_id:
                       id = f"00{id}"
                       for agent in agents_data:
                           if agent['id'] == id:
                               agent_data = parseAgent(host,agent,token) 
                              
                               agents[f"{agent_data['id']}"] = agent_data
                       
        except Exception as e:
            console.print(f"[bold red]An error occured: {e}[/bold red]") 

        return agents 


def getHardware(host,token, agent_id):

    hardware_info = {
             "processor":None,
             "memory":None,
             'serial_number':None,
             'scan_time':None
    }

    headers = {  
                'Authorization': f'Bearer {token}',  
                 'Content-Type': 'application/json'  
                }  
    
    url = f"{host}/syscollector/{agent_id}/hardware/?pretty=true" 

    response = requests.get(url, headers=headers,verify=False) 
    if response.status_code == 200:  
        data = response.json()['data']['affected_items'][0]  

        if 'board_serial' in data:
            hardware_info['serial_number'] = data['board_serial'] 

        if 'cpu' in data:
            hardware_info['processor'] =  f"{data['cpu']['name']}, cores: {data['cpu']['cores']}"

        if 'ram' in data:
            hardware_info['memory'] =  f"{data['ram']['free'] / (1024):.2f} MB / {data['ram']['total'] / (1024):.2f} MB"

        if 'scan' in data:
            hardware_info['scan_time'] = print_time_ago(datetime.strptime(data['scan']['time'],"%Y-%m-%dT%H:%M:%S+00:00").replace(tzinfo=pytz.utc)) or None 
            
    return hardware_info

def parseAgent(host,data,token):
    headers = {  
                'Authorization': f'Bearer {token}',  
                 'Content-Type': 'application/json'  
                }  
    
    agent = {
        "id":None,
        "username": None,
        "department":None,
        "processor":None,
        "memory": None,
        "serial_number":None,
        "hardware_model":None,
        "hardware_vendor":None,
        "hostname": None,
        "local_disk":None,
        "platform": None, 
        "scan_time":None,
        "status": None,
        "lastKeepAlive": None,
        "joined_date": None 

    }

    agent['id'] = data.get('id',None)
    agent['username'] = data.get('name',None) 
    agent['hostname'] =  data['os']['name'] if 'os' in data else None   
    agent['platform'] = data['os']['platform'] if 'os' in data else None
    agent['status'] = data.get('status',None) 
    agent['lastKeepAlive'] = print_time_ago(datetime.strptime(data['lastKeepAlive'],"%Y-%m-%dT%H:%M:%S+00:00").replace(tzinfo=pytz.utc)) if 'lastKeepAlive' in data else None 
    agent['joined_date'] = print_time_ago(datetime.strptime(data['dateAdd'],"%Y-%m-%dT%H:%M:%S+00:00").replace(tzinfo=pytz.utc)) if 'dateAdd' in data else None 
    agent['department'] = data['group'][0] if 'group' in data else None 
    hw_info = getHardware(host,token,agent['id']) 
    agent['memory'] = hw_info.get('memory', None) 
    agent['processor'] = hw_info.get('processor', None) 
    agent['scan_time'] = hw_info.get('scan_time', None) 
    agent['serial_number'] = hw_info.get('serial_number', None)  

    return agent


def print_time_ago(date_time_obj):
    
    if date_time_obj is None:
       return None 
    
    now = datetime.now(pytz.utc)
    
    # Calculate the difference between now and the provided datetime
    delta = relativedelta(now, date_time_obj)
    
    # Print years, months, and days ago
    if delta.years > 0:
        return f"{delta.years} year{'s' if delta.years > 1 else ''} ago."
    elif delta.months > 0:
        return f"{delta.months} month{'s' if delta.months > 1 else ''} ago."
    elif delta.days > 0:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago."
    elif delta.hours > 0:
        return f"{delta.hours} hour{'s' if delta.hours > 1 else ''} ago."
    elif delta.minutes > 0:
        return f"{delta.minutes} minute{'s' if delta.minutes > 1 else ''} ago."
    
    elif delta.seconds > 0:
        return f"{delta.seconds} second{'s' if delta.seconds > 1 else ''} ago."
    


     
     

    
       
