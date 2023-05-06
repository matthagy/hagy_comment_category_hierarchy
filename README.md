# Hierarchical clustering of substack comments

Compute hierarchical clustering using OpenAPI and visualize them in an interactive, static webpage.
You can view the clusters at [matthagy.github.io/hagy_comment_category_hierarchy](https://matthagy.github.io/hagy_comment_category_hierarchy/).

This projects provides the full data and code for generating these clusters.
It only considers my (Matt Hagy's) Substack comments so that all comments can be shared.
Comments are fetched using [substack_client](https://github.com/matthagy/substack_client) as described in,
[Developing a Substack client to fetch posts and comments](https://matthagy.substack.com/p/developing-a-custom-substack-front).

## Directory structure
* `data/`: Contains the comments and artifacts computed from them.
* `cluster/`: Contains the code for computing the clusters and for generating titles and summaries using ChatGPT.
* `site/`: Contains the static webpage for visualizing the clusters.