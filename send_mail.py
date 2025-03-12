import subprocess
from subprocess import PIPE

p1 = subprocess.run(['echo',"mail_subject"], stdout=PIPE, universal_newlines=True)
p2 = subprocess.run(['mail','-s',"mail_body", "axpatel@cisco.com"], universal_newlines=True, input=p1.stdout)
print(p2.stdout)