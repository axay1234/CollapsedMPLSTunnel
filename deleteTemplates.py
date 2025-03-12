from IdentifyCollapsedTunnels import *

deleteTemplate(templateNameGetTunnel)
fread = open("deviceIDWithTunnel.txt","r")
for deviceID in fread:
    deleteTemplate(str(deviceID.rstrip("\n"))+"_LSP_Template")
os.remove("deviceIDWithTunnel.txt")