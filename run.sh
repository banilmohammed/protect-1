source venv/bin/activate
ProTECT --config mustard_config.yaml --workDir /home/dranion/workDir /home/dranion/jobStore --restart|& tee errors/$(date '+%Y-%m-%d-%H-%M-%S').txt

