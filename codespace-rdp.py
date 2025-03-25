import os
import subprocess
import sys

# Default credentials
USERNAME = "user"
PASSWORD = "root"
PIN = 123456
AUTOSTART = True
CRP = ""  # Will need to be provided by user when running

def create_user():
    try:
        print("Creating User and Setting it up")
        os.system(f"useradd -m {USERNAME}")
        os.system(f"usermod -aG sudo {USERNAME}")
        os.system(f"echo '{USERNAME}:{PASSWORD}' | chpasswd")
        os.system("sed -i 's/\/bin\/sh/\/bin\/bash/g' /etc/passwd")
        print(f"User created with username '{USERNAME}' and password '{PASSWORD}'")
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

class CRD:
    def __init__(self, user, crp, pin, autostart):
        self.user = user
        self.crp = crp
        self.pin = pin
        self.autostart = autostart
        
        # Check if running as root
        if os.geteuid() != 0:
            print("This script needs to be run with sudo privileges")
            sys.exit(1)
            
        self.update_system()
        self.install_crd()
        self.install_desktop_environment()
        self.install_google_chrome()
        self.finalize()

    def update_system(self):
        print("Updating system packages")
        subprocess.run(["apt", "update"], check=True)

    def install_crd(self):
        print("Installing Chrome Remote Desktop")
        try:
            subprocess.run(['wget', '-q', 'https://dl.google.com/linux/direct/chrome-remote-desktop_current_amd64.deb'])
            subprocess.run(['dpkg', '--install', 'chrome-remote-desktop_current_amd64.deb'])
            subprocess.run(['apt', 'install', '--assume-yes', '--fix-broken'])
        except subprocess.CalledProcessError as e:
            print(f"Error installing CRD: {e}")
            sys.exit(1)

    def install_desktop_environment(self):
        print("Installing Desktop Environment")
        try:
            os.environ["DEBIAN_FRONTEND"] = "noninteractive"
            subprocess.run(["apt", "install", "--assume-yes", "xfce4", "desktop-base", "xfce4-terminal"])
            with open("/etc/chrome-remote-desktop-session", "w") as f:
                f.write("exec /etc/X11/Xsession /usr/bin/xfce4-session")
            subprocess.run(["apt", "remove", "--assume-yes", "gnome-terminal"])
            subprocess.run(["apt", "install", "--assume-yes", "xscreensaver"])
            subprocess.run(["systemctl", "disable", "lightdm.service"])
        except Exception as e:
            print(f"Error installing desktop environment: {e}")
            sys.exit(1)

    def install_google_chrome(self):
        print("Installing Google Chrome")
        try:
            subprocess.run(["wget", "-q", "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"])
            subprocess.run(["dpkg", "--install", "google-chrome-stable_current_amd64.deb"])
            subprocess.run(['apt', 'install', '--assume-yes', '--fix-broken'])
        except subprocess.CalledProcessError as e:
            print(f"Error installing Chrome: {e}")
            sys.exit(1)

    def finalize(self):
        print("Finalizing setup")
        try:
            if self.autostart:
                os.makedirs(f"/home/{self.user}/.config/autostart", exist_ok=True)
                link = "www.youtube.com/@epic_miner"
                colab_autostart = f"""[Desktop Entry]
Type=Application
Name=Colab
Exec=sh -c "google-chrome {link}"
Icon=
Comment=Open a predefined page at session start
X-GNOME-Autostart-enabled=true"""
                with open(f"/home/{self.user}/.config/autostart/colab.desktop", "w") as f:
                    f.write(colab_autostart)
                os.system(f"chmod +x /home/{self.user}/.config/autostart/colab.desktop")
                os.system(f"chown -R {self.user}:{self.user} /home/{self.user}/.config")

            subprocess.run(["adduser", self.user, "chrome-remote-desktop"])
            command = f"{self.crp} --pin={self.pin}"
            subprocess.run(["su", "-", self.user, "-c", command])
            subprocess.run(["service", "chrome-remote-desktop", "start"])
            
            print("\nRDP setup completed successfully!")
            print("Visit https://remotedesktop.google.com/access to connect")
        except Exception as e:
            print(f"Error in finalization: {e}")
            sys.exit(1)

def main():
    # Get CRP from user input
    crp_input = input("Enter the auth code from http://remotedesktop.google.com/headless: ").strip()
    
    if not crp_input:
        print("Authentication code is required")
        sys.exit(1)
    
    if len(str(PIN)) < 6:
        print("Pin must be 6 digits or more")
        sys.exit(1)

    if create_user():
        try:
            CRD(USERNAME, crp_input, PIN, AUTOSTART)
        except Exception as e:
            print(f"Setup failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
