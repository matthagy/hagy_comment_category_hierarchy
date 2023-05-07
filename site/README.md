# Interactive view of hierarchical clusters
This is a small static webpage for visualizing the clusters of comments.
It is developed in TypeScript, uses D3.js for visualization, and Webpack for bundling.

You can build the webpage by running the following commands in this directory.
```bash
npm install
npx webpack --mode=development --devtool=eval-source-map
```

The site can then be viewed by opening `dist/index.html` in a browser.

Additionally, it can be deployed to a GitHub Pages site by running the following command.
Note you'll have to change the `repository.url` field in `package.json` to match your repository.

```bash
npm run deploy
```