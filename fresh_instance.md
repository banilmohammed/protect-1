# Setting Up A Fresh Instance
* update all packages
      
      sudo apt-get update
   
* install python3 pip
      
      sudo apt install python3-pip
      
* install virtualenv
      
      pip install --upgrade virtualenv 
 
* install dependencies

      sudo apt install libcurl4-openssl-dev libssl-dev
      
* install docker following instructions from: [https://docs.docker.com/engine/install/ubuntu/]

* give admin privileges to docker

      sudo usermod -aG docker username
      
* update path
      
      PATH=${PATH}:/home/ubuntu/.local/bin

# Installing and Configuring AWS
* install aws
      
      curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
      unzip awscliv2.zip
      sudo aws/install
      
* configure aws
      
      aws configure
         enter AWS Access Key ID
         enter AWS Secret Key 
         default region name: us-west-1
         default output format: none
      
 * to check if aws is configured properly run: 
            
       aws s3 ls --request-payer requester protect-data/hg38_references/
