# trycycler_ibnugroho

## Pre-requisite
1. Install miniforge:

2. Set up trycycler snakemake wrapper

```bash
git clone git@github.com:matinnuhamunada/trycycler_snakemake_wrapper.git
```

3. Clone this repo
```bash
git@github.com:lab-biotek-bio-ugm/trycycler_ibnugroho.git
cd trycycler_ibnugroho
ln -s ../trycycler_snakemake_wrapper/workflow/ workflow
```

## Download Raw FASTQ

1. Create credentials, follow this step: https://developers.google.com/workspace/drive/api/quickstart/python

2. Create the conda environment: `mamba env create -f env.yaml`

3. Download the credentials to secrets, and run the script:

```bash
python scripts/gdrive_downloader.py \
  --root-folder-id 1gWIvlaRacTt_N-fORAmvl7B-_atNEFdp \
  --token-path secrets/token.json \
  --output-directory ./data/raw \
  --credentials-path secrets/credentials.json
```