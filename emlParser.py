from email.parser import BytesParser
from email import policy
from email.message import EmailMessage
from email.header import decode_header
import ctypes
import os
import email
import re
import simplejson
import time
import datetime

# Direct .eml file or directory path
EML_PATH_DIR = './emlBox'
RESULT_DIR = './parsedData' 

# Message Box for checking
def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


###############################################
# @@@ Input @@@
# date (parsed Date data)
# @@@ Function @@@
# Writes status report 
################################################ 
def Result_report(result):
    with open('Status_Report.txt','a',encoding='utf-8') as f:
        f.writelines(f"{result}\n")


###############################################
# @@@ Input @@@
# msg: EmailMessgae (msg of eml)
# @@@ Function @@@
# Get file name of Attachments
################################################ 
def get_part_filename(msg: EmailMessage):
    try:
        filename =  msg.get_filename()
    
        if decode_header(filename)[0][1] is not None:
            filename = decode_header(filename)[0][0].decode(decode_header(filename)[0][1])
            
        return filename    
    
    except:
        return 'File Error'   


################################################
# @@@ Input @@@
# date (parsed Date data)
# @@@ Function @@@
# Convert date 
################################################ 
def convert_date(date):
    total = []
    
    con_date = date.split(' ')
    
    Month_list = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sept','Oct','Nov','Dec']
    
    for i,month in enumerate(Month_list):        
        if con_date[2] == month:
            
            Con_month = str(i+1)   
            temp = f"{con_date[3]}-{Con_month}-{con_date[1]} {con_date[4]}"
            return temp        
  

################################################
# @@@ Input @@@
# data (body of eml)
# @@@ Function @@@
# Delete something useless except contents fo email
################################################ 
def HtmltoText(data):
    data = re.sub(r'&nbsp;','',data)
    data = re.sub(r'</.*?>','\n',data)
    data = re.sub(r'<.*?>', '', data)
    data = re.sub(r'&lt;', '<', data)
    data = re.sub(r'&gt;', '>', data)
    return data


################################################
# @@@ Input @@@
# target_eml (name of target eml file)
# @@@ Function @@@
# Extracts url from body
################################################
def extractURL(ms, data):
    urlList = []
    httpURL = re.findall('(https?://[\w\/\$\-\_\.\+\!\*\'\(\)]+[/A-Za-z0-9- =+~\?&;:_%\.#\*@!\(\)]+)', data)
    urlList = httpURL
    return urlList


################################################
# @@@ Input @@@
# target_eml (name of target eml file)
# @@@ Function @@@
# Extracts core information from eml
################################################
def extract_info(target_eml):
    with open(target_eml, 'rb') as fp:
        urlList = []
        try:
            ms = email.message_from_file(open(target_eml,encoding='utf-8'))
        except UnicodeDecodeError:
            ms = email.message_from_file(open(target_eml,encoding='euc-kr'))
        msg = BytesParser(policy=policy.default).parse(fp)

        # URL = [x for x in URL if x]
        # Data['URLS'] = URL
        RECEIVER = str(msg['To']).split(',')
        RECEIVER = [x for x in RECEIVER if x]
        SENDER = str(msg['From'])
        SUBJECT = str(msg['Subject'])
        DATE = str(msg['Date'])

        if msg['Date'] is not None:
            DATE = convert_date(DATE)

        Data = {
        "Title": [SUBJECT],
        "Date": [DATE],
        "Receiver": [RECEIVER],
        "Sender": [SENDER]
        }

        if msg['X-Original-SENDERIP'] is not None:
            SENDER_IP = str(msg['X-Original-SENDERIP'])
            Data['X-Original-SendIP'] = [SENDER_IP]
        

        if msg['X-Originating-IP'] is not None:
            SENDER_IP2 = str(msg['X-Originating-IP'])
            Data['X-Originating-IP'] = [SENDER_IP2]          
                     
        
        if msg['X-Original-SENDERCOUNTRY'] is not None:
            SENDER_COUNTRY = str(msg['X-Original-SENDERCOUNTRY'])
            Data['X-Original-SendCOUNTRY'] = [SENDER_COUNTRY]  
           
        try:
            # walks through message
            for part in msg.walk():                            
                type = part.get_content_type()
                if type == 'text/html':
                    EML_BODY = str(msg.get_body(preferencelist=('html')).get_content())                    
                    URL = extractURL(ms, EML_BODY)
                    # EML_BODY = str(msg.get_body(preferencelist=('html')).get_content())
                    EML_BODY = HtmltoText(EML_BODY)
                elif type == 'text/plain':
                    EML_BODY = str(msg.get_body(preferencelist=('plain')).get_content())
                    
        except Exception as Error:
            Mbox("ERROR REPORTED!", str(Error), 0)
            # print(Error)
            pass

        URL = [x for x in URL if x]
        Data['URLS'] = URL
        Data['Contents'] = [EML_BODY]
        
    return Data 

################################################
# @@@ Input @@@
# Path (Path where u want to drop files)  |  target_eml (name of target eml file)
# @@@ Function @@@
# Extract files from eml and write
################################################
def extract_attachments(Path,target_eml):
    try:
        msg = email.message_from_file(open(target_eml,encoding='utf-8'))
    except UnicodeDecodeError:
        msg = email.message_from_file(open(target_eml,encoding='euc-kr'))      
    attachments=msg.get_payload() 
    
    # FileName List
    fnam_list = []      
    
    if msg.is_multipart() is True:
        for attachment in attachments[1:]:
            if get_part_filename(attachment) == 'File Error':
                return 'File Error'
            else:
                fnam = get_part_filename(attachment)
                
                fnam_list.append(fnam)
                attach_file = f"{Path}\{fnam}"
                
                # Take payload and Write File 
                with open(attach_file, 'wb') as f:
                    f.write(attachment.get_payload(decode=True))
                    Result_report(f"Success! File successfully extracted from {target_eml}")
                    Result_report(f"Success! Extracted attachment : {fnam}")
    elif msg.is_multipart() is False:
        return 'No File'       
    else:
        return 'File Error'

    return fnam_list


###############################################
# @@@ Function @@@
# Total parser 
################################################ 
def parse_eml():
    for root, dir, files in os.walk(EML_PATH_DIR):
        for file in files:
            emlName = file.split(".")[0]
            parsed_path = RESULT_DIR + "\\ '" + emlName + "'"
            try:
                os.makedirs(parsed_path)
            except Exception as err:
                Mbox("ERROR REPORTED!", str(err), 0)               
                exit(1)
            list_info = {}
            list_Second = {}
            if '_info.json' not in file:
                target = f"{root}\{file}"
                fnm_json = f"{parsed_path}\\{emlName}_info.json" 
                list_Second = extract_info(target)
                list_info['emlName'] = [file]

                try:
                    fnm_name = extract_attachments(parsed_path,target)
                    if fnm_name == 'No File':
                        list_info['Attachment'] = [' ']
                        Result_report(f"{file}  : No such File exists")
                    elif fnm_name == 'File Error':
                        list_info['Attachment'] = ['FILE_FORMAT_ERROR']   
                        Result_report(f"{file}  :   File Format Error")
                    else:
                        fnm_name = [x for x in fnm_name if x]   # init fnm_name
                        list_info['Attachment'] = fnm_name
        
                except Exception as err:
                    Mbox("ERROR REPORTED!", str(err), 0)
                    Result_report(f"Error reported in {root} : {err} ")                
                    pass
                list_info.update(list_Second)
                
                json = simplejson.dumps(list_info, ensure_ascii=False)
                try:
                    o = open(fnm_json, "w", encoding='utf-8')
                except UnicodeEncodeError:
                    o = open(fnm_json, "w", encoding='euc-kr')
                o.write(json)
                o.close()
                Result_report(f"Success! created json file : {file}_info.json")
                Result_report("---------------------------------------")           

            else:
                Result_report(f"Same File Exists! : {fnm_json}")


def main():
    start = time.time()
    parse_eml()
    sec = time.time() - start
    times = str(datetime.timedelta(seconds=sec)).split(".")
    times = times[0]

    Mbox("Parsing Completed!", "Running time : "+times, 0)

if __name__ == "__main__":
    main()