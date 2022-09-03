# Protovac

A serial dumb terminal to display random things for Protospace.

## Setup

```
$ git clone https://github.com/Protospace/protovac.git
$ cd protovac
$ sudo tic -o /lib/terminfo/ mt70
$ sudo apt update
$ sudo apt install python3 python3-dev python3-pip python3-virtualenv
$ virtualenv -p python3 env
$ source env/bin/activate
(env) $ pip install -r requirements.txt
(env) $ python main.py
```


ExecStart=-/sbin/agetty --autologin protospace 9600 %I mt70
sudo systemctl daemon-reload
sudo systemctl restart serial-getty@ttyS0.service

