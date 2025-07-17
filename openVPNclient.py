import tkinter as tk
import pexpect
import re
import time
import subprocess
from tkinter import filedialog as fd

# Init variables & definitions ##################################################
connected = False                   # Connect-status
lastIn = lastOut = lastTime = None  # traffic calculation kB/s
actConfigPath = None               # sessionpath of active ovpn-config

# Create the main window ########################################################
window = tk.Tk()
window.title("OpenVPN Connect Client")
window.geometry("1600x600")
icon = tk.PhotoImage(file="icon.png")
window.iconphoto(True, icon)

# general Frame Layout - Rows####################################################
window.rowconfigure(0, weight=0)  # Status width fixed
window.rowconfigure(1, weight=0)  # Status width fixed
window.rowconfigure(2, weight=1)  # Console height can expand
window.rowconfigure(3, weight=0)  # Credentials width fixed
window.rowconfigure(4, weight=0)  # Button width fixed
window.columnconfigure(0, weight=1)  # column width can expand

# Status Frame Layout ###########################################################
frameStatus = tk.Frame(window, height=40)
frameStatus.grid(row=0, column=0, padx=10, pady=(10,0), sticky="ew")
frameStatus.columnconfigure(0, weight=0) # column width fixed
frameStatus.columnconfigure(1, weight=1) # column width can expand
frameStatus.columnconfigure(2, weight=0) # column width fixed
# Status Frame Text
labelStatus = tk.Label(frameStatus, text="Status:")
labelStatus.grid(row=0, column=0, sticky="w")
spacer = tk.Label(frameStatus, text="")
spacer.grid(row=0, column=1)
textStatus = tk.Label(frameStatus, text="Disconnected", fg="red")
textStatus.grid(row=0, column=2, sticky="e")

# Traffic Frame Layout ##########################################################
frameTraffic = tk.Frame(window, height=40)
frameTraffic.grid(row=1, column=0, padx=10, pady=(10,0), sticky="ew")
frameTraffic.columnconfigure(0, weight=0) # column width fixed
frameTraffic.columnconfigure(1, weight=1) # column width can expand
frameTraffic.columnconfigure(2, weight=0) # column width fixed
frameTraffic.columnconfigure(3, weight=0) # column width fixed
frameTraffic.columnconfigure(4, weight=0) # column width fixed
labelTraffic = tk.Label(frameTraffic, text="Traffic:")
labelTraffic.grid(row=0, column=0, sticky="w")
spacer = tk.Label(frameTraffic, text="")
spacer.grid(row=0, column=1)
textInBytes = tk.Label(frameTraffic, text="0.0 kB/s ↓")
textInBytes.grid(row=0, column=2, sticky="e")
textSlash = tk.Label(frameTraffic, text="", width=1)
textSlash.grid(row=0, column=3, sticky="ew")
textOutBytes = tk.Label(frameTraffic, text="0.0 kB/s ↑")
textOutBytes.grid(row=0, column=4, sticky="e")

# Console Frame Layout ##########################################################
frameConsole = tk.Frame(window, bg="white")
frameConsole.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
frameConsole.columnconfigure(0, weight=1)  # column width can expand
frameConsole.columnconfigure(1, weight=0)  # Scrollbar width fixed
frameConsole.rowconfigure(0, weight=1) # row height can expand
textConsole = tk.Text(frameConsole)
textConsole.grid(row=0, column=0, sticky="nsew")
textConsole.configure(state="disabled") # Console is readonly

scrollbarConsole=tk.Scrollbar(frameConsole, command=textConsole.yview)
scrollbarConsole.grid(row=0, column=1, sticky="ns")
textConsole.config(yscrollcommand=scrollbarConsole.set)


# Credentials Frame Layout ######################################################
frameCredentials = tk.Frame(window)
frameCredentials.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
frameCredentials.columnconfigure(0, weight=0)
frameCredentials.columnconfigure(1, weight=1)
frameCredentials.columnconfigure(2, weight=0)
frameCredentials.columnconfigure(3, weight=1)
labelUsername = tk.Label(frameCredentials, text="Username:")
labelUsername.grid(row=0, column=0, sticky="w", padx=(0,10))
entryUsername = tk.Entry(frameCredentials)
entryUsername.grid(row=0, column=1, sticky="ew")
labelPassTotp = tk.Label(frameCredentials, text="Pass+TOTP:")
labelPassTotp.grid(row=0, column=2, sticky="w", padx=10)
entryPassTotp = tk.Entry(frameCredentials, show="*")
entryPassTotp.grid(row=0, column=3, sticky="ew")

# Button Frame Layout ###########################################################
frameButton = tk.Frame(window)
frameButton.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
frameButton.columnconfigure(0, weight=1)

# Functions #####################################################################
def consoleWrite(text):
    textConsole.configure(state="normal")
    textConsole.insert(tk.END, strReplaceR(text))
    textConsole.configure(state="disabled")
    textConsole.see(tk.END) # view newest consoleinput

def strReplaceR(inputstr):
    output=inputstr.replace('\r', '')
    return output

# get VPN sessions ##############################################################
def vpnGetSessionPath():
    try:
        configCmd=f"openvpn3 sessions-list"
        child=pexpect.spawn(configCmd)
        child.expect(pexpect.EOF)
        output = child.before.decode("utf-8")
        sessions = re.findall(r'Path:\s*(\S+)', output)
        return sessions
    except Exception as e:
        consoleWrite(f"Error: {e}\n")
        return None

# VPN Traffic Stats #############################################################
def vpnTrafficStats():
    global connected, lastIn, lastOut, lastTime
    actSessionPath=vpnGetSessionPath()
    
    if connected:
        try:
            cmd = ["openvpn3", "session-stats", "--session-path", actSessionPath[0] ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stdout
            numInBytes = re.search(r'BYTES_IN\s*\.*\s*(\d+)', output)
            numOutBytes = re.search(r'BYTES_OUT\s*\.*\s*(\d+)', output)

            if numInBytes and numOutBytes:
                in_val=int(numInBytes.group(1))
                out_val=int(numOutBytes.group(1))
                currentTime = time.time()
                duration = currentTime - lastTime if lastTime else 1
                deltaIn = (in_val - lastIn) / duration if lastIn else 0
                deltaOut = (out_val - lastOut) / duration if lastOut else 0
                textInBytes.config(text=f"{round(deltaIn / 1024, 1)} kB/s ↓")
                textOutBytes.config(text=f"{round(deltaOut / 1024, 1)} kB/s ↑")
                lastIn = in_val
                lastOut = out_val
                lastTime = currentTime
            else:
                consoleWrite("Error: can not read session-stats\n")            

        except Exception as e:
            consoleWrite(f"Error: {e}\n")
            return False

    window.after(1000, vpnTrafficStats)

# VPN Connection ################################################################
def vpnConnect():
    global actConfigPath
    
    consoleWrite(f"Connecting to {actConfigPath} ... ")
    try:
        configCmd=f"openvpn3 session-start --config-path {actConfigPath}"
        child=pexpect.spawn(configCmd)
        child.expect("Auth User name:", timeout=2)
        child.sendline(entryUsername.get())
        child.expect("Auth Password:", timeout=2)
        child.sendline(entryPassTotp.get())
        child.expect(pexpect.EOF)
        output = child.before.decode("utf-8")
        entryUsername.delete(0, tk.END)
        entryPassTotp.delete(0, tk.END)
        if "Connected" in output:
            actSessionPath=vpnGetSessionPath()
            consoleWrite(f"Done\nSession opened {actSessionPath[0]}\n")
            return True
        return False
    except Exception as e:
        consoleWrite(f"Error: {e}\n")
        return False

# VPN Disconnect ################################################################
def vpnDisconnect(sessionPath):
    global actConfigPath
    consoleWrite(f"Close Session {sessionPath} ... ")
    try:
        configCmd=f"openvpn3 session-manage --disconnect --session-path {sessionPath}"
        child=pexpect.spawn(configCmd)
        child.expect(pexpect.EOF)
        output = child.before.decode("utf-8")
        if sessionPath == actConfigPath:
            actConfigPath = None
        consoleWrite("Done\n")
        return
    except Exception as e:
        consoleWrite(f"Error: {e}\n")
        return None

# VPN DisconnectAll #############################################################
def vpnDisconnectAll():
    sessions=vpnGetSessionPath()
    if len(sessions)==0:
        return
        
    for sessionPath in sessions: 
        vpnDisconnect(sessionPath)

# VPN Import Config #############################################################
def vpnImportConfig(configPathFile):
    consoleWrite(f"Importing Config {configPathFile} ... ")
    try:
        configCmd=f"openvpn3 config-import --config {configPathFile} --persistent"
        child=pexpect.spawn(configCmd)
        child.expect(pexpect.EOF)
        output = child.before.decode("utf-8")
        consoleWrite("Done\n")
        return output
    except Exception as e:
        consoleWrite(f"Error: {e}\n")
        return None
    
# VPN Remove Config #############################################################
def vpnRemoveConfig(configPath):
    consoleWrite(f"Removing {configPath} ... ")
    try:
        configCmd=f"openvpn3 config-remove --force --path {configPath}"
        child=pexpect.spawn(configCmd)
        child.expect(pexpect.EOF)
        output = child.before.decode("utf-8")
        consoleWrite("Done\n")
        return output
    except Exception as e:
        consoleWrite(f"Error: {e}\n")
        return None

# VPN Remove All Config #############################################################
def vpnRemoveAllConfig():
    configList=vpnListImportedConfig()
    if len(configList)==0:
        return

    for config in configList:
        vpnRemoveConfig(config)

# VPN List Config #############################################################
def vpnListImportedConfig():
    configList = []
    consoleWrite("List imported Configs: ")    
    try:
        configCmd=f"openvpn3 configs-list -v"
        child=pexpect.spawn(configCmd)
        child.expect(pexpect.EOF)
        output = child.before.decode("utf-8")
        outputlines = output.splitlines()
        for line in outputlines:
            line = line.strip() # clear empty lines or lines with spaces only
            if line.startswith("/net/openvpn/v3/configuration/"):
                configList.append(line)
                consoleWrite(f"{line}\n")
        return configList
    except Exception as e:
        consoleWrite(f"Error: {e}\n")
        return None

# VPN Init Config ###############################################################
def vpnInitConfig():
    global actConfigPath
    consoleWrite("Init Config ... \n")    
    configList = vpnListImportedConfig()
    if len(configList)==0:  # config not yet imported
        consoleWrite("No config loaded yet - please load ovpn-file\n")
        configPathFile = fd.askopenfilename(title='Select Configfile', initialdir='~', filetypes=[("OVPN files", "*.ovpn")])
        vpnImportConfig(configPathFile)
        configList=vpnListImportedConfig()
    
    actConfigPath = configList[0] # take first config - it should be only one :-)  
    consoleWrite(f"Config loaded: {actConfigPath}\n")
    return

# Window Close Action ###########################################################
def on_close():
    vpnDisconnectAll()  
    window.destroy()    
    
# buttonConnect Action ##########################################################
def on_click():
    global actConfigPath
    global connected

    if not connected:
        success=vpnConnect()
        if success:
            buttonConnect.config(text="Disconnect")
            textStatus.config(text="Connected", fg="dark green")
            connected=True
            return
    else:
        vpnDisconnectAll()            
        buttonConnect.config(text="Connect")
        textStatus.config(text="Disconnected", fg="red")
        connected=False

buttonConnect = tk.Button(frameButton, text="Connect", command=on_click)
buttonConnect.grid(row=0, column=0, sticky="ew")


vpnDisconnectAll()  # reset any active or pending connections
vpnInitConfig()     # Import Config if none exists (must be after vpnDisconnectAll)
vpnTrafficStats()   # Trigger Traffic display
window.protocol("WM_DELETE_WINDOW", on_close)
window.mainloop()

