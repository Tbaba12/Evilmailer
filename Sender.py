import requests
import urllib
import string
import uuid
from requests_toolbelt import MultipartEncoder
import random
import ntpath


def generate_signature() -> str:
    """
    generates the MD5-Post-Signature needed for the API-Requests
    :return: str, generated signature
    """
    chars = string.ascii_lowercase + string.digits + string.digits
    signature = ""
    for _ in range(32):
        signature += random.choice(chars)
    return signature


def generate_message_id() -> str:
    """
    generates the Message-ID needed for the API-Requests
    :return: str, generated Message-ID
    """
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    message_id = ""
    for _ in range(32):
        message_id += random.choice(chars)
    return message_id


class Sender:
    def __init__(self, credentials: str, proxy: str = None):
        """
        gives control over a mailaccess-account
        :param str credentials: credentials for mailaccess account in format "email:password"
        :param str proxy: Proxy in format "ip:port"
        """
        # Url-encoding Email and Password
        self.email = urllib.parse.quote_plus(credentials.split(":")[0])
        self.password = urllib.parse.quote_plus(credentials.split(":")[1])
        self.email_attaches = list()
        self.email_attach_url = None
        self.proxy = proxy
        self.token = ""
        # generating Signature and message_id
        self.md5_post_signature = generate_signature()
        self.message_id = generate_message_id()
        # set the Headers
        self.headers = {
            "User-Agent": "mobmail android 14.14.0.35934 com.my.mail",
            "X-Mobile-App": "e552fda2e6c711eaadc10242ac120002",
            "Host": "aj-https.my.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }
        # creating a session
        self.session = requests.Session()

    def login(self) -> str:
        """
        Function executes a login request with the given credentials
        :return: str,
        "Fail" : Login failed,
        "Success": Login was successful,
        "Banned": Proxy ban/connection error or the API requested a Captcha-Solution
        """

        login_url = "https://aj-https.my.com/cgi-bin/auth"
        payload = f"Password={self.password}&oauth2=0&Login={self.email}&mobile=1&mob_json=1&simple=1&useragent=android&md5_post_signature={self.md5_post_signature}"
        try:
            response = self.session.post(login_url, data=payload, headers=self.headers, proxies=self.proxy)
            if "captcha" in response.text:
                return "Banned"
            elif "Ok=0" in response.text:
                return "Fail"
            elif "Ok=1" in response.text:
                return "Success"
        except:
            return "Banned"

    def get_token(self) -> bool:
        """
        Function to get the access_token, needed for further account-access/functionality
        :return: bool
        """
        token_url = f"https://aj-https.my.com/api/v1/tokens?email={self.email}&mp=android&mmp=mail&md5_signature={self.md5_post_signature}"
        try:
            response = self.session.get(token_url, proxies=self.proxy)
            self.token = response.json()["body"]["token"]
            return True
        except:
            return False
            
    def prepare_file(self, file_path: str) -> str:
        """
        Uploads a file to the email attachments
        :param str file_path: file path from the file to attach
        :return: str,
        "Fail" : Uploading failed,
        "Success": Uploading was successful,
        "Banned": Proxy ban or other connection/account errors
        """
        file_name = ntpath.basename(file_path)
        with open(file_path, "rb") as f:
            file_raw = f.read()
        #print(file_raw)

        multipart_form_data = {
            "message_id": (None, self.message_id, None, {"Content-Length": "32"}),
            "file": (file_name, file_raw, "multipart/form-data", {"Content-Length": str(len(file_raw))}),
        }
        multipart_data = MultipartEncoder(multipart_form_data, boundary=uuid.uuid4())
        # print(multipart_data.read())
        
        headers = {
            "Content-Type": multipart_data.content_type,
            "User-Agent": "mobmail android 14.24.0.36801 com.my.mail",
            "Content-Length": str(len(file_raw) + 372),
            "Host": "aj-https.my.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }

        url = f"https://aj-https.my.com/api/v1/messages/attaches/add?htmlencoded=false&email={self.email}&mp=android&mmp=mail&DeviceID=a53804ef7ccccd946684f23eb61a4576&client=mobile&udid=1903d21fd838fc6c3bfa9e17d27a585033038376782d8144d504eab7c26cb624&playservices=221514022&connectid=5458ddfd38e3d8bd01d4db5519a004ec&os=Android&os_version=7.1.2&ver=com.my.mail14.22.0.36574&appbuild=36574&vendor=samsung&model=SM-G935F&device_type=Smartphone&country=DE&language=de_DE&timezone=GMT%2B02%3A00&device_name=samsung%20SM-G935F&instanceid=erHfOyxHRNaeVG373nNeF_&idfa=d3f3f8ba-d933-4b3e-be9b-ea102eafbd7b&device_year=2014&connection_class=UNKNOWN&current=google&first=google&behaviorName=default%2Bstickers&appsflyerid=1654447063241-8746396706785193826&reqmode=fg&ExperimentID=Experiment_simple_signin&isExperiment=false&token={self.token}&md5_signature={self.md5_post_signature}"
        
        try:
            response = self.session.post(url, headers=headers, data=multipart_data.to_string(), proxies=self.proxy)
        except:
            return "Banned"
        if response.status_code == 200:
            self.email_attaches.append({"id": response.json()["body"]["attach"]["id"], "type": "attach"})
            self.email_attach_url = response.json()["body"]["attach"]["thumbnails"]["image"]["original"]
            return "Success"
        else:
            return "Fail"

    def send_email(self, to_adress: list, subject: str, email_body: str, html_body: bool = False) -> str:
        """
        Function to send emails with raw text or HTML-template
        :param list to_adress: receipt email adresses
        :param str subject: email subject
        :param str email_body: email text/body
        :param bool html_body: Set to true if email body is html
        :return: str,
        "Fail" : Sending failed,
        "Success": Sending was successful,
        "Banned": Proxy ban or other connection/account errors
        """

        send_email_url = f"https://aj-https.my.com/api/v1/messages/send?htmlencoded=false&email={self.email}&mp=android&mmp=mail&DeviceID=a53804ef7ccccd946684f23eb61a4576&client=mobile&udid=1903d21fd838fc6c3bfa9e17d27a585033038376782d8144d504eab7c26cb624&playservices=221514022&connectid=5458ddfd38e3d8bd01d4db5519a004ec&os=Android&os_version=7.1.2&ver=com.my.mail14.22.0.36574&appbuild=36574&vendor=samsung&model=SM-G935F&device_type=Smartphone&country=DE&language=de_DE&timezone=GMT%2B02%3A00&device_name=samsung%20SM-G935F&instanceid=erHfOyxHRNaeVG373nNeF_&idfa=d3f3f8ba-d933-4b3e-be9b-ea102eafbd7b&device_year=2014&connection_class=UNKNOWN&current=google&first=google&behaviorName=default%2Bstickers&appsflyerid=1654447063241-8746396706785193826&reqmode=fg&ExperimentID=Experiment_simple_signin&isExperiment=false&token={self.token}&md5_signature={self.md5_post_signature}"
        if html_body:
            html = urllib.parse.quote(email_body.replace('"', r'\"')).replace("/", "%2F")
            text = ""
        else:
            html = ""
            text = urllib.parse.quote(email_body.replace('"', r'\"').replace("/", "%2F"))
        addr = "<" + ">,<".join(to_adress) + ">"
        email_data_raw = {
            "attaches": {"list": self.email_attaches},
            "body": {
                "html": html,
                "text": text
            },
            "correspondents": {"bcc": "", "cc": "", "to": addr},
            "id": self.message_id,
            "priority": "3",
            "send_date": "0",
            "source": {},
            "subject": urllib.parse.quote(subject),
            "md5_post_signature": self.md5_post_signature
        }
        encoded_email_data = urllib.parse.urlencode(email_data_raw).replace("%27", "%22").replace("%25", "%").replace(
            "%5C%5C", "%5C").replace("%0A", "%5Cn")
        try:
            response = self.session.post(send_email_url, data=encoded_email_data, proxies=self.proxy)
            #print(response.json())
            if response.json()["status"] == 200:
                return "Success"
            else:
                # print(response.json())
                return "Fail"
        except:
            return "Banned"

