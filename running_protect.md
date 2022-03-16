# Running ProTECT

## ProTECT Installation
* clone the ProTECT from the repo
       git clone
* navigate to the protect folder
    cd  protect
* create and activate the virtualenv
    virutalenv --python=python3 venv
    source venv/bin/activate
* install dependencies
    make install
* install bd2k extras (note this will install s3am as well but this will not used)
    make special install
* install ProTECT
    make develop
* install typing_extensions
    pip install typing-extensions
* install cwltool
    pip install cwltool
* install proper pyyaml version
    pip install pyyaml==5.4.1

## Running ProTECT
* create config yaml
    ProTECT --generate_config
* update the config file with the file paths to the sample data files and the file paths to where the human genome reference will be downloaded
* create working dir before the run
* run ProTECT
    ProTECT --config path/to/config_file.yaml --workDir path/to/workDir/ path/to/jobStore --disableCaching --cleanWorkDir never --reference
* the reference flag downloads the human genome reference to /mnt/neoepitopes/protect_references/
