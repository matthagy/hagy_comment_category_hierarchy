const express = require('express');
const morgan = require('morgan');
const app = express();
const port = process.env.PORT || 3000;

// Serve static files from the 'public' folder
app.use(express.static('../site/dist'));

// Use morgan to log every request
app.use(morgan('combined'));

// Start the server
app.listen(port, () => {
    console.log(`Server is listening on port ${port}`);
});
