from pprint import pprint

from netmiko import ConnectHandler

def send_show_command(device, commands):
    result = {}
    try:
        with ConnectHandler(**device) as ssh:
            ssh.enable()
            for command in commands:
                output = ssh.send_command(command)
                result[command] = output
        return result
    except :
        print("error")

if __name__ == "__main__":
    device = {
        "device_type": "juniper",
        "ip": "10.85.174.59",
        "username": "labroot",
        "password": "lab123",
        "port":22
    }
    result = send_show_command(device, ["show arp","show route"])
    with open("Output.txt", "w") as out:
        for i in result:
            out.write(device["ip"]+"  "+i+"\n")
            out.write(result[i])
