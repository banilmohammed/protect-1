# Running ProTECT

## ProTECT Installation
* clone the ProTECT from the repo

       git clone git@github.com:banilmohammed/protect-1.git
       
* navigate to the protect folder

       cd  protect
    
* create and activate the virtualenv
       
       virutalenv --python=python3 venv
       source venv/bin/activate
       
* install dependencies
       
       make prepare
       
* install bd2k extras (note this will install s3am as well but this will not used)
       
       make special_install
       
* install typing_extensions
       
       pip3 install typing-extensions
       
* install cwltool
       
       pip3 install cwltool==3.1.20211107152837
       
* install proper pyyaml version
       
       pip3 install pyyaml==5.4.1
       
* install ProTECT
       
       make develop
       
## Running ProTECT
* create config yaml

      ProTECT --generate_config
      
* update the config file with the file paths to the sample data files and the file paths to where the human genome reference will be downloaded
* create working dir before the run
* run ProTECT
      
      ProTECT --config path/to/config_file.yaml --workDir path/to/workDir/ path/to/jobStore --disableCaching --cleanWorkDir never --reference
      
* the reference flag downloads the human genome reference to /mnt/neoepitopes/protect_references/, if not specified human genome reference files will not be downloaded, and ProTECT will be run as normal
* by default --reference will download references to /mnt/neoepitopes/protect_references
