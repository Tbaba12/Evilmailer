import easygui
import glob
from collections import deque


def grab_proxy(proxy_type: str, path: str) -> list:
    """
    Loads proxies in format 'ip:port' from given file-path and returns a list of proxy-dictionarys
    :param srt proxy_type: proxy type (http / socks4 / socks5)
    :param str path: file-path for proxy text file
    :return: list, dictionaries of proxy e.g.:[{'https': type://ip:port},]
    """
    with open(path) as file:
        proxies = [{"https": f"{proxy_type}://{proxy.strip()}"} for proxy in file.readlines() if proxy.strip() != ""]
    return proxies
    

def get_sender_credentials(path: str) -> list:
    """
    Loads credentials in format 'email:password' from given file-path and returns a list
    :param str path: file-path for credential text file
    :return: list, credentials (email:password)
    """
    with open(path) as file:
        credentials = [cred.strip() for cred in file.readlines() if cred.strip() != ""]
    return credentials


def get_recipient_emails(path: str) -> deque:
    """
    Loads emails from given file-path and returns a list
    :param str path: file-path for recipient emails text file
    :return: list, recipient emails
    """
    with open(path) as file:
        recipients = deque([rec.strip().split(":")[0] for rec in file.readlines() if rec.strip() != ""])
    return recipients
    
    
def get_files(directory: str, title: str) -> str | None:
    """
    Creates a user-friendly vision to load files
    :param str directory: directory of target file
    :param str title: title of GUI filemanager
    :return: str|None, target file path
    """
    if "files" not in directory:
        filetype = "*.txt"
    else:
        filetype = "*.*"
    try:
        path = easygui.fileopenbox(title=title, filetypes=filetype)
        return path
    except:
        files = glob.glob(f"{directory}{filetype}")
        if len(files) == 0:
            return None
        for num in range(len(files)):
            print(f"[{num}] - {files[num]}")
        try:
            users_choice = int(input("Type the number for the file: "))
            path = f"{files[users_choice]}"
            return path
        except:
            return None
