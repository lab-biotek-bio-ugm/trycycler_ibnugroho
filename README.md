# trycycler_ibnugroho

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