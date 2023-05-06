# Clustering Code

Computes comment embeddings and performs agglomerative clustering.
This is accomplished with the following scripts:

* `compute_embeddings.py`: Computes comment embeddings using OpenAI's `text-embedding-ada-002` model
* `cluster.py`: Performs agglomerative clustering on the embeddings and collapse select nodes
* `generate_titles.py`: Use ChatGPT API to generate 5 titles for each cluster
* `generate_summaries.py`: Use ChatGPT API to generate a summary for each cluster
* `export.py`: Export the clusters to a JSON file for visualization in the site

## Usage

Run the following commands to set up the environment:

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Then run the above Python scripts in the given order to generate the associated files.
The repository already contains the generated files, so you needn't run all the scripts
unless you want to reproduce the results from scratch or if you want to modify anything.

Running the scripts that use OpenAI's API requires an API key.
You can set this in the environmental variable `OPENAI_API_KEY`
or in a file named `~/.openai-api-key`.