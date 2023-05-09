const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin")
const CopyWebpackPlugin = require('copy-webpack-plugin');


module.exports = {
    mode: "development",
    entry: "./index.ts",
    devtool: "inline-source-map",
    devServer: {
        contentBase: "./dist",
    },
    module: {
        rules: [
            {
                test: /\.tsx?$/,
                use: "ts-loader",
                exclude: /node_modules/,
            },
            {
                test: /\.css$/,
                use: [MiniCssExtractPlugin.loader, 'css-loader']
            }
        ],
    },
    resolve: {
        extensions: [".tsx", ".ts", ".js"],
    },
    output: {
        filename: "bundle.js",
        path: path.resolve(__dirname, "dist"),
    },
    plugins: [
        // new CleanWebpackPlugin(),
        new HtmlWebpackPlugin({
            template: "./index.html",
            filename: "index.html",
        }),
        new MiniCssExtractPlugin({
            filename: '[name].css',
            chunkFilename: '[id].css',
        }),
        // Add the CopyWebpackPlugin to copy static files
        new CopyWebpackPlugin({
            patterns: [
                {
                    from: path.resolve(__dirname, 'static'), // Source directory
                    to: path.resolve(__dirname, 'dist', 'static'), // Destination directory
                },
            ],
        }),
    ],
};
