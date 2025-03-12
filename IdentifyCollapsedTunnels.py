import configparser
import datetime
import json
import os
import logging
import pprint
import http.client
import ssl
import subprocess
import base64
import sys
import time

from subprocess import PIPE
from base64 import b64encode
from datetime import datetime

ssl._create_default_https_context = ssl._create_unverified_context

#creating logger object
now = datetime.now()
dt_string = now.strftime("%d%m%Y_%H%M%S")
logging.basicConfig(filename="logs/logger"+dt_string+".log",format='%(asctime)s %(message)s',filemode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

#creating object for reading properties from config file
conf = configparser.ConfigParser()
conf.read('config.properties')

ipAddr=conf.get('epnm','ipAddr')
user_EPNM=conf.get('epnm','EPNM_UserName')
enc_passwd_EPNM=conf.get('epnm','EPNM_PWD')
temp_dec_pwd = enc_passwd_EPNM.encode('utf-8')
passwd_EPNM = base64.b64decode(temp_dec_pwd).decode('utf-8')
uploadTemplateAPI=conf.get('template','upload')
deployTemplateAPI=conf.get('template','deploy')
deleteTemplateAPI=conf.get('template','delete')
templateNameGetTunnel="getTunnelName"
deviceInfoDict = {}

def basic_auth(username, password):
    token = b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
    return f'Basic {token}'

header_EPNM1 ={ 'Accept': 'application/json','Content-Type': 'application/json','Authorization': basic_auth(user_EPNM,passwd_EPNM)}

def sendEmail(deviceID,ipAddr,devName,tunnelInfo,primaryLsp,protectLsp,mail_type):

    toAddr = conf.get('mail','toAddr')
    if mail_type == "error":
        mail_subject= "Collapsed Tunnels detected on "+tunnelInfo.strip("'\"")+" in "+ipAddr+" device"
        mail_body = "Device Name="+devName+"\n\ndeviceID = "+str(deviceID)+"\nWorking LSP = "+primaryLsp+"\nProtect LSP = "+protectLsp+"\n\n[CLI to clear and verify collapsed tunnel]\n(1) Clear collapsed tunnel:\nFirst log in to "+ipAddr+", then copy-and-paste the following CLI\n\nconfigure terminal\ninterface "+tunnelInfo.strip("'\"")+"\nno tunnel mpls traffic-eng path-option protect 10 diverse non-revertive lockdown\ntunnel mpls traffic-eng path-option protect 10 diverse non-revertive lockdown\n\n(2) Verify tunnel working and protect LSP:\n\nshow mpls traffic-eng tunnels "+tunnelInfo.strip("'\"")+" protection"
        mail_body = mail_body.replace("'",'')
    elif mail_type == "normal":
        mail_body = "No Collapsed Tunnels detected on "+ipAddr+" EPNM server"
        mail_subject = ""
    p1 = subprocess.run(['echo',mail_subject], stdout=PIPE, universal_newlines=True)
    p2 = subprocess.run(['mail','-s',mail_body, toAddr], universal_newlines=True, input=p1.stdout)
    print("mail sent to "+ toAddr+ " receptions")
   

def getAPI(method,API_info,payload,):
    r_code = 0
    #header_EPNM1 ={ 'Accept': 'application/json','Content-Type': 'application/json','Authorization': basic_auth(user_EPNM,passwd_EPNM)}
    try:
        conn = http.client.HTTPSConnection(ipAddr)
        conn.request(method, API_info,payload,header_EPNM1)
        response_get = conn.getresponse()
        r_code = response_get.status
        temp_data = response_get.read()
        data = json.loads(temp_data.decode("utf-8"))

        return r_code,data
    except Exception as e:
        print("There was some issue while connecting to server or getting devices please try again\nResponse code = "+str(r_code)+"\n"+str(e))
        logger.error("There was some issue while connecting to server or getting devices please try again\n"+str(e))
        sys.exit(1)
def delete_old_logs():
    log_path = "logs"
    now = time.time()
    dys = conf.get('logs','log_delete_days')
    for f in os.listdir(log_path):
        f = os.path.join(log_path, f)
        if os.stat(f).st_mtime < now - int(dys) * 86400:
            if os.path.isfile(f):
                os.remove(os.path.join(log_path, f))
                print(str(f)+" Log file is deleted as it is "+dys+" older")
                logger.info(str(f)+" Log file is deleted as it is "+dys+" older")

def deleteTemplate(templateName):
    #header_EPNM1 ={ 'Accept': 'application/json','Content-Type': 'application/json','Authorization': basic_auth(user_EPNM,passwd_EPNM)}
    try:
        url = "https://"+ipAddr+deleteTemplateAPI+templateName
        status_code,APIreponse=getAPI("DELETE",deleteTemplateAPI+templateName,"")
        logger.info("Delete Response Code: "+str(status_code))
        logger.debug("Delete Response: "+str(APIreponse))
        return APIreponse
    except Exception as e:
        print("Error while deleting template"+str(e))

def deployJson(API_info,deviceId,templateName):
    #header_EPNM1 ={ 'Accept': 'application/json','Content-Type': 'application/json','Authorization': basic_auth(user_EPNM,passwd_EPNM)}
    try:
        with open("playloads/deploy.json", "r+") as jsonFile:
            data = json.load(jsonFile)
            data["cliTemplateCommand"]["targetDevices"]["targetDevice"][0]["targetDeviceID"] = deviceId       
            data["cliTemplateCommand"]["templateName"] = templateName
        playload = json.dumps(data)
        
        url = "https://"+ipAddr+API_info
        logger.info("RequestUrl: "+url)
        logger.info("RequestHeaders: "+str(header_EPNM1))
        logger.info("RequestPlayload: "+str(playload))
        print("RequestUrl: "+url)
        print("RequestHeaders: "+str(header_EPNM1))
        print("RequestPlayload: "+str(playload))
        status_code,APIreponse=getAPI("PUT",API_info,playload)
        statusCode = status_code
        data = APIreponse
        print("Response Code: "+str(status_code) )
        print("Response: "+str(APIreponse))
        logger.info("Response Code: "+str(status_code) )
        logger.debug("Response: "+str(APIreponse))
        return statusCode,data
    except Exception as e:
        print("Error while deploying template"+str(e))

def uploadJson(API_info,templateName,commands):
    #header_EPNM1 ={ 'Accept': 'application/json','Content-Type': 'application/json','Authorization': basic_auth(user_EPNM,passwd_EPNM)}
    try:
        with open("playloads/upload.json", "r+") as jsonFile:
            data = json.load(jsonFile)
            data["cliTemplate"]["name"] = templateName
            data["cliTemplate"]["content"] = commands
            playload = json.dumps(data)
        url = "https://"+ipAddr+API_info
        logger.info("RequestUrl: "+url)
        logger.info("RequestHeaders: "+str(header_EPNM1))
        logger.info("RequestPlayload: "+str(playload))
        print("RequestUrl: "+url)
        print("RequestHeaders: "+str(header_EPNM1))
        print("RequestPlayload: "+str(playload))
        status_code,APIreponse=getAPI("POST",API_info,playload)
        print("Response Code: "+str(status_code) )
        print("Response: "+str(APIreponse))
        logger.info("Response Code: "+str(status_code) )
        logger.info("Response: "+str(APIreponse))
    except Exception as e:
        print("Error while uploading template"+str(e))

def processDeviceID():
    try:
        getDeviceUrlData = conf.get('epnm','getDevices')
        deviceInfo=conf.get('epnm','device')
        filteredDeviceIDList =[]
        devices_thisPage = 1
        total_devices = 3
        first_device = 0
        conn = http.client.HTTPSConnection(ipAddr)
        logger.info("Hitting get devices API\nEPNM server IP :"+ipAddr)
        print("Hitting get devices API\nEPNM server IP :"+ipAddr)
        while devices_thisPage+1 < total_devices:
            conn.request("GET", getDeviceUrlData+".json?reachability=REACHABLE&.case_sensitive=false&.full=true&.firstResult="+str(first_device)+"&deviceType=contains(%22Cisco%20NCS%2042%22)", "", header_EPNM1)
            response_get = conn.getresponse()
            r_code = response_get.status
            if r_code == 200:
                temp_data = response_get.read()
                data = json.loads(temp_data.decode("utf-8"))
                l = len(data["queryResponse"]["entity"])
                total_devices = data["queryResponse"]["@count"]
                devices_thisPage = data["queryResponse"]["@last"]
                first_device = devices_thisPage
                for i in range(l):
                    deviceId = data["queryResponse"]["entity"][i]["devicesDTO"]["@id"]
                    filteredDeviceIDList.append(deviceId)
                    deviceIP = data["queryResponse"]["entity"][i]["devicesDTO"]["ipAddress"]
                    deviceName = data["queryResponse"]["entity"][i]["devicesDTO"]["deviceName"]
                    deviceInfoDict[deviceId] ={}
                    deviceInfoDict[deviceId]['deviceIP']=deviceIP
                    deviceInfoDict[deviceId]['deviceName']=deviceName
            print("Filtered device ID list from get devices API is "+str(filteredDeviceIDList))
            logger.info("Filtered device ID list from get devices API is "+str(filteredDeviceIDList))
            return filteredDeviceIDList

    except Exception as e:
        print("Error while Processing device ID"+str(e))
        logger.error("Error while Processing device ID"+str(e))
        sys.exit(1)

def uploadTemGetTunnelInfo():

    getTunnelNameCmd="do sh ip int brief | s Tunnel"
    print("*************creating template for getting tunnel numbers*************\nEPNM server IP :"+ipAddr)
    logger.info("*************creating template for getting tunnel numbers*************\nEPNM server IP :"+ipAddr)
    uploadJson(uploadTemplateAPI,templateNameGetTunnel,getTunnelNameCmd)

def processTunnelInfo(deviceIDList): # In this method code is written for processing tunnel info uploading template to detect collapsed tunnels

    try:
        tunnelNumber = []
        deviceIDWithTunnel = []
        fwrite = open("deviceIDWithTunnel.txt","a")
        for deviceID in deviceIDList:
            logger.info("\n*************Deploying template for getting tunnel numbers idevice ID: "+str(deviceID)+"*****************")
            print("\n*************Deploying template for getting tunnel numbers idevice ID: "+str(deviceID)+"*****************")
            responsecode, data = deployJson(deployTemplateAPI,deviceID,templateNameGetTunnel)
            if responsecode == 200:
                with open('temptunnelNum.txt', 'a') as f: 
                    f.write(data["mgmtResponse"]["cliTemplateCommandResult"][0]["results"]["result"][0]["message"])
                fread = open("temptunnelNum.txt","r")
                for x in fread:
                    if x.startswith("Tunnel"):
                        temp = x.split(" ")
                        tunnelNumber.append(temp[0])    
                print("tunnel Interfaces present in "+str(deviceID)+" is "+str(tunnelNumber))
                logger.info("tunnel Interfaces present in "+str(deviceID)+" is "+str(tunnelNumber))
                deviceInfoDict[deviceID]['Tunnel']=str(tunnelNumber)
                if not tunnelNumber:
                    print("As there are no Tunnel interfaces present not uploading template for "+str(deviceID))
                else:
                    deviceIDWithTunnel.append(deviceID)
                    fwrite.write(str(deviceID)+"\n")
                    #uploading template to  check primary and protect lsp
                    commandLSP_1="do sh mpls traffic-eng tunnels "
                    commandLSP_2=" protection | s Primary lsp\n"
                    commandLSP_3=" protection | s Protect lsp\n"
                    command_final=""
                    for i in tunnelNumber:
                        command_final=command_final+commandLSP_1+str(i)+commandLSP_2+commandLSP_1+str(i)+commandLSP_3
                    print("Commands to be executed:\n"+command_final)
                    logger.info("Commands to be executed:\n"+command_final)
                    print("*************Uploading template for checking collapsed Tunnelsfor device ID: "+str(deviceID)+"*************")
                    logger.info("*************Uploading template for checking collapsed Tunnelsfor device ID: "+str(deviceID)+"*************")
                    uploadJson(uploadTemplateAPI,str(deviceID)+"_LSP_Template",command_final)
                    tunnelNumber.clear()
                os.remove("temptunnelNum.txt")
            fwrite.close
        print("Templates created for devices with tunnel and thoose device ID's are"+str(deviceIDWithTunnel))
        print("Complete device data\n"+str(deviceInfoDict))
        with open('completeDeviceData.json', 'w') as cdd:
            json.dump(deviceInfoDict, cdd)
        deviceInfoDict.clear()
        return deviceIDWithTunnel
    except Exception as e:
        print("Error while processing tunnel info"+str(e))

def checkCollapsedTunnel():
    try:
        m_type_error = ""
        fread_deviceID = open("deviceIDWithTunnel.txt","r")
        with open("completeDeviceData.json", "r+") as cdd1:
            cdData1 = json.load(cdd1)
        for deviceID in fread_deviceID:
            logger.info("\n*************Deploying template for checking collapsed tunnels in device: "+str(deviceID).rstrip("\n")+"*************")
            print("\n*************Deploying template for checking collapsed tunnels in device: "+str(deviceID).rstrip("\n")+"*************")
            tunnel_deviceID = str(deviceID).rstrip("\n")
            template_name = str(deviceID).rstrip("\n")+"_LSP_Template"
            statuscode,data = deployJson(deployTemplateAPI,tunnel_deviceID,template_name)
            with open('temp_LSP.txt', 'w') as f: 
                f.write(data["mgmtResponse"]["cliTemplateCommandResult"][0]["results"]["result"][0]["message"])        
            fread = open("temp_LSP.txt","r")
            protectLspPath=""
            primaryLspPath=""
            tunnelValue = cdData1[tunnel_deviceID]['Tunnel']
            mail_ipAddress = cdData1[tunnel_deviceID]['deviceIP']
            mail_deviceName = cdData1[tunnel_deviceID]['deviceName']
            tunnelValue = tunnelValue.lstrip("[")
            tunnelValue = tunnelValue.rstrip("]")
            tunnelValue = tunnelValue.split(",")
            j=0
            for x in fread:          
                if "Protect lsp path:" in x or "Primary lsp path:" in x:
                    if "Primary" in x: 
                        temp = x.split(":")
                        primaryLspPath=temp[1]
                        primaryLspPath=primaryLspPath.strip('\n')
                        primaryLspPath=primaryLspPath.lstrip(" ")
                        print(primaryLspPath)
                    elif "Protect" in x:
                        temp = x.split(":")
                        protectLspPath=temp[1]
                        protectLspPath=protectLspPath.strip('\n')
                        protectLspPath=protectLspPath.lstrip(" ")
                        print(protectLspPath)
                        if protectLspPath != primaryLspPath or (protectLspPath == "" and primaryLspPath == ""):
                            print("protectLspPath and primaryLspPath of"+tunnelValue[j]+"  are not same")
                            logger.info("protectLspPath and primaryLspPath of"+tunnelValue[j]+"  are not same")
                            tunnelKey = tunnelValue[j].strip(" ")
                            tunnelKey = tunnelKey.strip("\'")
                            cdData1[tunnel_deviceID][tunnelKey] = "Pass"
                            j=j+1
                        else:
                            print("protectLspPath and primaryLspPath of"+tunnelValue[j]+"  are same")
                            logger.info("protectLspPath and primaryLspPath of"+tunnelValue[j]+"  are same")
                            tunnelKey = tunnelValue[j].strip(" ")
                            tunnelKey = tunnelKey.strip("\'")
                            cdData1[tunnel_deviceID][tunnelKey] = "Fail"
                            cdData1[tunnel_deviceID][tunnelKey+'_Description'] = data["mgmtResponse"]["cliTemplateCommandResult"][0]["results"]["result"][0]["message"]
                            m_type_error = "error"
                            sendEmail(tunnel_deviceID,mail_ipAddress,mail_deviceName,tunnelValue[j].strip("'\""),primaryLspPath,protectLspPath,"error")
                            j=j+1
            os.remove("temp_LSP.txt")
        with open('completeDeviceData.json', 'w') as cdd:
            json.dump(cdData1, cdd)
            print("\n****************************************Summary****************************************")
            logger.info("\n****************************************Summary****************************************")
            print(json.dumps(cdData1, indent=2))   
            logger.info(json.dumps(cdData1, indent=2))
            if m_type_error != "error":
                sendEmail(tunnel_deviceID,ipAddr,mail_deviceName,0,"","","normal") 
    except Exception as e:
        print("Error while checkcking collapsed tunnels"+str(e))
def main():

    skipTunnelCreation=conf.get('epnm','skipTemplateCreation')
    deleteTemplates=conf.get('epnm','deleteTemplates')
    try:
        print("###############################Started Execution #############################")
        #Get device ID by hitting get devices API and filter devices if its not expected device type and unreachable
        if skipTunnelCreation == "no":
            deviceIDList = processDeviceID()
            ##upload template for getting tunnel numbers
            uploadTemGetTunnelInfo()
            ##Deploy template for getting tunnel numbers
            processTunnelInfo(deviceIDList)
            # deploying template to  check primary and protect lsp
            checkCollapsedTunnel()
            if deleteTemplates == "yes":
                deleteTemplate(templateNameGetTunnel)
                fread = open("deviceIDWithTunnel.txt","r")
                for deviceID in fread:
                    deleteTemplate(str(deviceID.rstrip("\n"))+"_LSP_Template")
                os.remove("deviceIDWithTunnel.txt")
            
        elif skipTunnelCreation == "yes":
            print("Skipping Tunnel creation and proceeding to check colapssed Tunnels")
            # deploying template to  check primary and protect lsp
            checkCollapsedTunnel()
        print("For complete logs refer /logs path")
        print("############################### Completed Execution #############################")
    except Exception as e:
        print("Error"+str(e))            
if __name__ == "__main__":
    main()
