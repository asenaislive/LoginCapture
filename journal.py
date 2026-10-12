"""

Login Capture

Author:  AsenaisLive        GitHub: github.com/asenaislive
Co-Author: Jyoshnavi        GitHub: github.com/jyoshnavi2416

Created: October 2026
License: MIT
Tested:  Fedora (GNOME)

Note: Intended for use on personal devices only.

Feel free to modify and report any issues.
"""

import subprocess as sp
import cv2 as cv
import time
from pathlib import Path

cmd = ["journalctl", "-n", "0", "-f"]
flag = False
photo_dir_path=Path("/home/asenaislive/Pictures/Login Capture")
String_fail=["pam_unix(gdm-password:auth): authentication failure"]
String_success=["pam_unix(gdm-password:session): session opened"]
String_lockscreen_unlock=["gkr-pam: unlocked login keyring"]

# Checks if the mentioned path exists and creates if it doesn't. Using if here raises a race condition
photo_dir_path.mkdir(parents=True, exist_ok=True)

# Loop exists when flag is false
while not flag:
    try:
        with sp.Popen(cmd,
                        stdout=sp.PIPE,
                        stderr=sp.DEVNULL,
                        text=True, 
                        bufsize=1) as process:

            for line in process.stdout:
                line=line.lower().strip() # Converts the line to lowercase and removes all whitespaces

                if(all(check in line for check in String_fail)):
                    cam=cv.VideoCapture(0)
                    current_time=time.strftime("%d-%m-%Y_%H-%M-%S")
                    print("Incorrect password entered")
                    

                    try:
                        for j in range(25): # Captures 25 frames to adjust to lighting conditions
                            ret, img=cam.read()
                            
                            # Returns a boolean value which can be used as a status code
                            image_status=cv.imwrite(f"{photo_dir_path}/image_{current_time}.jpg", img)
        
                            if (image_status != 1):
                                raise Exception("Image capture failed")
                           
                    # Handles all CV2, my image capture exception and Keyboard Interrupt
                    except Exception as e:
                        print(f"\nError: {e}")

                # Exits everything if password is correctWait
                elif(all(check in line for check in String_success)or all(check2 in line for check2 in String_lockscreen_unlock)):
                    print("\n\nImage captured successfully to Pictures/Login Capture\n\n")
                    cam.release()
                    flag=True
                    break


    except Exception as e:
        print(f"\nError: {e}")
        cam.release() # Frees up the camera resource
