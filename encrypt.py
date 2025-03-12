from IdentifyCollapsedTunnels import *
import getpass

api_pwd = getpass.getpass(prompt= "Enter password for encryption: ")
enc_pwd_tmp = base64.b64encode(api_pwd.encode('utf-8'))
enc_pwd = enc_pwd_tmp.decode('utf-8')
#print("Ecncrypted Password : "+str(enc_pwd))
update_flag = input("The password is Encrypted. Do you update the Ecncrypted Password to config.properties (Y or N) ")

if update_flag == "Y":
    conf.set('epnm','EPNM_PWD',str(enc_pwd))
    fp=open('config.properties','w')
    conf.write(fp)
    print("Ecncrypted Password is updated to config.properties")
    logger.info("Ecncrypted Password is updated to config.properties")
elif update_flag == "N":
    print("Ecncrypted Password is not updated to config.properties\nUpdate it manually")
    print("Ecncrypted Password : "+str(enc_pwd))
    logger.info("Ecncrypted Password is not updated to config.properties\nUpdate it manually")
    logger.info("Ecncrypted Password : "+str(enc_pwd))
else:
    print("You did not enter valid string so we could not update Ecncrypted Password to config.properties\nUpdate it manually")
    logger.info("You did not enter valid string so we could not update Ecncrypted Password to config.properties\nUpdate it manually")
    print("Ecncrypted Password : "+str(enc_pwd))
    logger.info("Ecncrypted Password : "+str(enc_pwd))