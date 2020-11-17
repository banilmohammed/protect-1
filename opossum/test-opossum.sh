# YAY INSTALLS 
#yay -S pip samtools htslib


# check for RNA Tumor bam 

DATA=https://xfer.genome.wustl.edu/gxfer1/project/gms/testdata/bams/hcc1395_1tenth_percent
RNA_TUMOR=gerald_C1TD1ACXX_8_ACAGTG.bam
RNA_NORMAL=gerald_C2DBEACXX_3.bam
RNA_FASTQ=gerald_C2DBEACXX_3.fai
if [ -f "$RNA_TUMOR" ]; then
      echo "$RNA_TUMOR exists."
    else 
      # get the smallest one
      wget ${DATA}/${RNA_TUMOR}
fi
if [ -f "${RNA_TUMOR}.bai" ]; then
      echo "${RNA_TUMOR}.bai exists."
    else 
      samtools index -b $RNA_TUMOR 
fi
if [ -f "$RNA_FASTQ" ]; then
    echo "$RNA_FASTQ exists."
  else
   #wget ${DATA}/${RNA_NORMAL}
   picard SamToFastq I=${RNA_NORMAL} FASTQ=${RNA_FASTQ}
fi 
PROCESSED=opossum_C1TD1ACXX_8_ACAGTG.bam
OPOSSUM=Opossum.py
if [ -f "$OPOSSUM" ]; then 
    echo "$OPOSSUM exists."
  else
    wget -O $OPOSSUM https://raw.githubusercontent.com/BSGOxford/Opossum/master/Opossum.py
    2to3 -w $OPOSSUM 
fi
# pip dependencies for opossum 
pip install pysam 

#woot 
python $OPOSSUM --BamFile=$RNA_TUMOR --OutFile=$PROCESSED

PLATYPUS_DIR=platypus
PLATYPUS=${PLATYPUS_DIR}/bin/Platypus.py
if [ -f "$PLATYPUS"]; then
    echo "$PLATYPUS exists."
  else
    git clone --depth=1 --branch=master https://github.com/andyrimmer/Platypus.git ${PLATYPUS_DIR}
    rm -rf ./${PLATYPUS_DIR}/.git
   # 2to3 -w ${PLATYPUS_DIR}/
    cd ${PLATYPUS_DIR}
    make 
fi 
cd ..
python2 ${PLATYPUS} callVariants --bamFiles=${PROCESSED} --refFile=${RNA_FASTQ} --output=variants.vcf

