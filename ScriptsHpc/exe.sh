#!/bin/bash
#SBATCH --job-name=gemma4_31b
#SBATCH --partition=gpu-4-a100        
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --cpus-per-task=16            
#SBATCH --mem=100G                    
#SBATCH --time=04:00:00
#SBATCH --output=resposta_final.out
#SBATCH --error=diagnostico_sistema.err
#SBATCH --mail-user=andre.soares.moreira18@gmail.com
#SBATCH --mail-type=ALL

module load singularity
module load compilers/nvidia/cuda/12.6

# Silencia o vLLM
export VLLM_LOGGING_LEVEL=ERROR

singularity exec --nv \
    --bind /mnt/beegfs/scratch/asgmoreira/gemma4-31b-weights:/mnt/modelo \
    vllm-custom.sif \
    python3 -u 02MicroClassification.py
