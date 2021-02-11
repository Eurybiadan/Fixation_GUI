import string

try:
    f = open('ports.inf','r+')

    for line in f:
        print(line)
        splitstring=string.split(line, '=')
        if splitstring[0] == "ScreenPort":
            ScreenPort = splitstring[1].rstrip()
            print("Setting screenport to: " + ScreenPort)
        elif splitstring[0] == "OptPort":
            OptPort = splitstring[1].rstrip()
            print("Setting optport to: " + OptPort)
        
except IOError:
    print("No file detected. Running first time settings...")
