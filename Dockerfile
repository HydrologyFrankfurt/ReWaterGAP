# Use an official mamba/conda image as a base image
FROM condaforge/mambaforge:23.3.1-1
# FROM mambaorg/micromamba:2.0.5

# Set the working directory inside the container
WORKDIR /app

# Clone the ReWaterGAP repository (depth=1 only loads the latest commit) into the working directory
RUN git clone --depth=1 https://github.com/HydrologyFrankfurt/ReWaterGAP.git /app

# Install dependencies
RUN mamba install --yes --file /app/requirements.txt -c conda-forge \
    && mamba clean --all

# Make port 80 available to the world outside this container
EXPOSE 80

# Run app.py when the container launches
CMD ["python3", "run_watergap.py", "mounted_dir/Config_ReWaterGAP.json"]