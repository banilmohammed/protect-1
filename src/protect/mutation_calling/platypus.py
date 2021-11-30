#!/usr/bin/env python3
# Copyright 2016 UCSC Computational Genomics Lab
# Original contributor: Arjun Arkal Rao
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import defaultdict
from math import ceil

from protect.common import (docker_path,
                            docker_call,
                            export_results,
                            get_files_from_filestore,
                            untargz)
from protect.mutation_calling.common import sample_chromosomes, merge_perchrom_vcfs
from toil.job import PromisedRequirement

import os
import sys


# disk for platypus
def platypus_disk(rna_bam, fasta):
    return int(ceil(rna_bam.size) +
               5 * ceil(fasta.size))


def run_platypus_with_merge(job, rna_bam, univ_options, opossum_options, platypus_options):
    """
    A wrapper for the entire platypus run

    :param dict rna_bam: Dict dicts of bam and bai for tumor RNA-Seq obtained by running STAR within
           ProTECT.
    :param dict univ_options: Dict of universal options used by almost all tools
    :param dict platypus_options: Options specific to Platypus
    :return: fsID to the merged Platypus calls
    :rtype: toil.fileStore.FileID
    """
    preprocess = job.wrapJobFn(run_opossum, rna_bam['rna_genome'], univ_options, opossum_options, disk='100M',
                          memory='100M').encapsulate()
    spawn = job.wrapJobFn(run_platypus, rna_bam['rna_genome'], univ_options, platypus_options, disk='100M',
                          memory='100M').encapsulate()
    merge = job.wrapJobFn(merge_perchrom_vcfs, spawn.rv(), univ_options, disk='100M', memory='100M')
    job.addChild(preprocess)
    preprocess.addChild(spawn)
    spawn.addChild(merge)
    return merge.rv()

def run_opossum(job, rna_bam, univ_options, opossum_options):
    """
    Spawn a opossum job for the entire rna_bam

    :param dict rna_bam: Dict of bam and bai for tumor DNA-Seq.  It can be one of two formats
           rna_bam:   # Just the genomic bam and bai
                |- 'rna_genome_sorted.bam': fsID
                +- 'rna_genome_sorted.bam.bai': fsID
           OR
           rna_bam:   # The output from run_star
               |- 'rna_transcriptome.bam': fsID
               |- 'rna_genome':     # Only this part will be used
                       |- 'rna_genome_sorted.bam': fsID
                       +- 'rna_genome_sorted.bam.bai': fsID
    :param dict univ_options: Dict of universal options used by almost all tools
    :param dict opossum_options: Options specific to opossum
    :return: Dict of results mirroring rna_bam but pre-processed
    :rtype: dict
    """
    if 'rna_genome' in list(rna_bam.keys()):
        rna_bam = rna_bam['rna_genome']
    elif set(rna_bam.keys()) == {'rna_genome_sorted.bam', 'rna_genome_sorted.bam.bai'}:
        pass
    else:
        raise RuntimeError('An improperly formatted dict was passed to rna_bam.')

    bams = {'tumor_rna': rna_bam['rna_genome_sorted.bam'],
            'tumor_rnai': rna_bam['rna_genome_sorted.bam.bai']}

    work_dir = os.getcwd()
    input_files = {
        'rna.bam': bams['tumor_rna'],
        'rna.bam.bai': bams['tumor_rnai']}

    input_files = get_files_from_filestore(job, input_files, work_dir, docker=False)
    input_files = {key: docker_path(path) for key, path in list(input_files.items())}

    opossum_output = ''.join([work_dir, '/opossum_rna_genome.bam'])
    opossum_log = ''.join([work_dir, '/opossum.log'])
    parameters = [univ_options['patient'],  # shortID
                  chrom,
                  '--BamFile', input_files['rna.bam'],
                  '--OutFile', docker_path(opossum_output),
                  '-g', docker_path(opossum_log)]
    docker_call(tool='opossum', tool_parameters=parameters,
                work_dir=work_dir, dockerhub=univ_options['dockerhub'],
                tool_version=opossum_options['version'])
    output_file = job.fileStore.writeGlobalFile(opossum_output)
    job.fileStore.logToMaster('Ran opossum on %s successfully' % (univ_options['patient']))
    return output_file

def run_platypus(job, rna_bam, univ_options, platypus_options):
    """
    Spawn a platypus job for each chromosome on the input bam trios.

    :param dict rna_bam: Dict of bam and bai for tumor DNA-Seq.  It can be one of two formats
           rna_bam:   # Just the genomic bam and bai
                |- 'rna_genome_sorted.bam': fsID
                +- 'rna_genome_sorted.bam.bai': fsID
           OR
           rna_bam:   # The output from run_star
               |- 'rna_transcriptome.bam': fsID
               |- 'rna_genome':     # Only this part will be used
                       |- 'rna_genome_sorted.bam': fsID
                       +- 'rna_genome_sorted.bam.bai': fsID
    :param dict univ_options: Dict of universal options used by almost all tools
    :param dict platypus_options: Options specific to platypus
    :return: Dict of results from running platypus on every chromosome
             perchrom_platypus:
                 |- 'chr1': fsID
                 |- 'chr2' fsID
                 |
                 |-...
                 |
                 +- 'chrM': fsID
    :rtype: dict
    """
    if 'rna_genome' in list(rna_bam.keys()):
        rna_bam = rna_bam['rna_genome']
    elif set(rna_bam.keys()) == {'rna_genome_sorted.bam', 'rna_genome_sorted.bam.bai'}:
        pass
    else:
        raise RuntimeError('An improperly formatted dict was passed to rna_bam.')

    bams = {'tumor_rna': rna_bam['rna_genome_sorted.bam'],
            'tumor_rnai': rna_bam['rna_genome_sorted.bam.bai']}
    # Get a list of chromosomes to process
    if platypus_options['chromosomes']:
        chromosomes = platypus_options['chromosomes']
    else:
        chromosomes = sample_chromosomes(job, platypus_options['genome_fai'])
    perchrom_platypus = defaultdict()
    for chrom in chromosomes:
        platypus = job.addChildJobFn(run_platypus_perchrom, bams, univ_options, platypus_options, chrom,
                                  memory='6G',
                                  disk=PromisedRequirement(
                                      platypus_disk, tumor_bam['tumor_dna_fix_pg_sorted.bam'],
                                      normal_bam['normal_dna_fix_pg_sorted.bam'],
                                      rna_bam['rna_genome_sorted.bam'],
                                      platypus_options['genome_fasta']))
        filter_platypus = platypus.addChildJobFn(run_filter_platypus, bams, platypus.rv(), univ_options,
                                           platypus_options, chrom, memory='6G',
                                           disk=PromisedRequirement(
                                               platypus_disk, tumor_bam['tumor_dna_fix_pg_sorted.bam'],
                                               normal_bam['normal_dna_fix_pg_sorted.bam'],
                                               rna_bam['rna_genome_sorted.bam'],
                                               platypus_options['genome_fasta']))
        perchrom_platypus[chrom] = filter_platypus.rv()
    job.fileStore.logToMaster('Ran spawn_platypus on %s successfully' % univ_options['patient'])
    return perchrom_platypus


def run_platypus_perchrom(job, bams, univ_options, platypus_options, chrom):
    """
    Run platypus call on a single chromosome in the input bams.

    :param dict bams: Dict of bam and bai for tumor DNA-Seq, normal DNA-Seq and tumor RNA-Seq
    :param dict univ_options: Dict of universal options used by almost all tools
    :param dict platypus_options: Options specific to platypus
    :param str chrom: Chromosome to process
    :return: fsID for the chromsome vcf
    :rtype: toil.fileStore.FileID
    """
    work_dir = os.getcwd()
    input_files = {
        'rna.bam': bams['tumor_rna'],
        'rna.bam.bai': bams['tumor_rnai'],
        'genome.fa.tar.gz': platypus_options['genome_fasta'],
        'genome.fa.fai.tar.gz': platypus_options['genome_fai']}
    input_files = get_files_from_filestore(job, input_files, work_dir, docker=False)

    for key in ('genome.fa', 'genome.fa.fai'):
        input_files[key] = untargz(input_files[key + '.tar.gz'], work_dir)
    input_files = {key: docker_path(path) for key, path in list(input_files.items())}

    platypus_output = ''.join([work_dir, '/platypus_', chrom, '.vcf'])
    platypus_log = ''.join([work_dir, '/platypus_', chrom, '_platypus.log'])
    parameters = [univ_options['patient'],  # shortID
                  chrom,
                  '--bamFiles=', input_files['rna.bam'],
                  '-refFile', input_files['genome.fa'],
                  '-o', docker_path(platypus_output),
                  '-g', docker_path(platypus_log)]
    docker_call(tool='platypus', tool_parameters=parameters,
                work_dir=work_dir, dockerhub=univ_options['dockerhub'],
                tool_version=platypus_options['version'])
    output_file = job.fileStore.writeGlobalFile(platypus_output)
    job.fileStore.logToMaster('Ran platypus on %s:%s successfully' % (univ_options['patient'], chrom))
    return output_file
