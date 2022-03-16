# Setting Up A Fresh Instance
* update all packages
    sudo apt-get update
* install python3 pip
    sudo apt install python3-pip
* install virtualenv
    pip install virutalenv
* update path
    PATH=${PATH}:/home/ubuntu/.local/bin

# Installing and Configuring AWS
* install aws
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo aws/install
* configure aws
    aws configure
