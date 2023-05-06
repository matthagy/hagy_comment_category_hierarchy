import * as d3 from "d3";
import {node_data, NodeData} from "./nodes";
import {BaseType} from "d3";
import './main.css';


class Node {
    id: string;
    titles: string[];
    summary: string;
    count: number;
    medianLikes: number;
    avgLikes: number;
    maxLikes: number;
    commentRms: number;
    children: Node[];
    visible: boolean = true;
    childCollapses: boolean = false;
    selected: boolean = false;

    constructor(id: string,
                titles: string[],
                summary: string,
                count: number,
                medianLikes: number,
                avgLikes: number,
                maxLikes: number,
                commentRms: number,
                children: Node[]) {
        this.id = id;
        this.titles = titles;
        this.summary = summary;
        this.count = count;
        this.medianLikes = medianLikes;
        this.avgLikes = avgLikes;
        this.maxLikes = maxLikes;
        this.commentRms = commentRms;
        this.children = children;
    }

    getChildren(): Node[] {
        return this.children;//.filter(c => c.visible);
    }

    toggleChildrenVisible(collapse?: boolean): void {
        if (collapse === undefined) {
            collapse = !this.childCollapses;
            // console.log(`toggleChildrenVisible ${this.title} collapse=${collapse} visible=${this.visible}`);
        }
        this.childCollapses = collapse;
        for (const child of this.children) {
            child.visible = !collapse;
            child.toggleChildrenVisible(collapse);
        }
    }

    visit(visitor: (node: Node) => void): void {
        visitor(this);
        for (const child of this.children) {
            child.visit(visitor);
        }
    }
}

function createNode(data: NodeData): Node {
    return new Node(data.id, data.titles, data.summary,
        data.count, data.medianLikes, data.avgLikes, data.maxLikes, data.commentRms,
        (data.children ?? []).map(createNode));
}

const topLevelNode = createNode(node_data);

const width = 1800;
const height = 800;

const svg = d3
    .select("#tree-container")
    .append("svg")
    //   .attr("width", width)
    .attr("height", height)
    //   .attr("viewBox", [-width / 2, -height / 2, width, height])
    .style("cursor", "crosshair");

const initialZoomTransform = "translate(89.0252, 647.519) scale(0.812252, 0.812252)";
const g = svg.append("g")
    .attr("transform", initialZoomTransform);


const treeLayout = d3.tree<Node>()
    .size([width, height])
    .nodeSize([40, 400])
;

function updateSvgSize() {
    const width = window.innerWidth;
    const curHeight = 0.75 * window.innerHeight;
    svg.attr("width", width);
    svg.attr("height", Math.min(curHeight, height));
    //svg.attr("viewBox", [-width / 2, -height / 2, width, height]);
    // treeLayout.size([width, height]);
}

updateSvgSize();
window.addEventListener("resize", () => {
    updateSvgSize();
    update();
});


let rootNode = d3.hierarchy(topLevelNode, d => d.getChildren());
let layoutNode = treeLayout(rootNode);

type NodeSelectionType = d3.Selection<BaseType, d3.HierarchyPointNode<Node>, SVGGElement, unknown>;
type LinkPathType = d3.Selection<SVGPathElement, d3.HierarchyPointNode<Node>, SVGGElement, unknown>
type NodePathType = d3.Selection<SVGGElement, d3.HierarchyPointNode<Node>, SVGGElement, unknown>
type NodeShapeType = d3.Selection<SVGCircleElement, d3.HierarchyPointNode<Node>, SVGGElement, unknown>
type NodeTextType = d3.Selection<SVGTextElement, d3.HierarchyPointNode<Node>, SVGGElement, unknown>

function selectLinks(): NodeSelectionType {
    return g.selectAll(".link")
        .data(layoutNode.descendants().slice(1));
}

function selectNodes(): NodeSelectionType {
    return g
        .selectAll(".node")
        .data(layoutNode.descendants());
}

function linkAppend(selection: NodeSelectionType): LinkPathType {
    return selection
        .enter()
        .append("path");
}

function nodeAppend(selection: NodeSelectionType): NodePathType {
    return selection
        .enter()
        .append("g");
}

function linkStyle(selection: LinkPathType): LinkPathType {
    return selection
        .style("stroke", "#666")
        .style("stroke-width", 3)
        .attr("fill", "none")
        //.attr("r", 3)
        .attr("class", "link")
        .attr("opacity", d => d.data.visible ? 0.25 : 0)
        .attr("d", d => {
            const parent = d.parent;
            if (!parent) {
                throw new Error("Parent is null");
            }
            return "M" + d.y + "," + d.x
                + "C" + (d.y + parent.y) / 2 + "," + d.x
                + " " + (d.y + parent.y) / 2 + "," + parent.x
                + " " + parent.y + "," + parent.x;
        });
}

function nodeStyle(selection: NodePathType): NodePathType {
    return selection
        .attr("class", "node")
        .attr("transform", d => "translate(" + d.y + "," + d.x + ")");
}

function nodeShapeAppend(selection: NodePathType): NodeShapeType {
    return selection
        .append("circle");
}

function nodeRadius(d: d3.HierarchyPointNode<Node>) {
    return 3 * Math.pow(d.data.count, 0.4);
}


function nodeShapeStyle(selection: NodeShapeType): NodeShapeType {
    return selection
        .attr("r", d => nodeRadius(d))
        .attr("fill", d => d.data.children.length > 0 ? "#00a67d" : "#e9950c")
        .attr("opacity", d => d.data.visible ? 1 : 0)
        .attr("stroke", d => d.data.selected ? "#df3079" : "#666")
        .attr("stroke-width", d => d.data.selected ? 3 : 1)
        .on("click", (e, d) => {
            if (e.ctrlKey) {
                console.log(`Clicked w/ Control ${d.data.titles[0]} ${d.data.visible}}`);
                d.data.toggleChildrenVisible();
                update();
            } else {
                console.log(`Bare clicked ${d.data.titles[0]} ${d.data.visible}}`);
                displayNodeInfo(d.data);
                topLevelNode.visit(node => node.selected = false);
                d.data.selected = true;
                update();
            }
        });
}

function nodeTextAppend(selection: NodePathType): NodeTextType {
    return selection
        .append("text");
}

function nodeTextStyle(selection: NodeTextType): NodeTextType {
    return selection
        .text((d) => {
            return d.data.titles[0];
        })
        .attr("transform", d => `translate(${1.2 * nodeRadius(d)},5)`)
        .attr("opacity", d => d.data.visible ? 1 : 0);
}


let existingLink = linkStyle(linkAppend(selectLinks()));
let existingNode = nodeStyle(nodeAppend(selectNodes()));
let existingNodeShape = nodeShapeStyle(nodeShapeAppend(existingNode));
let existingNodeText = nodeTextStyle(nodeTextAppend(existingNode));

function update() {
    console.log("update");

    rootNode = d3.hierarchy(topLevelNode, d => d.getChildren());
    layoutNode = treeLayout(rootNode);

    const newLinks = linkAppend(selectLinks());
    const mergeLinks = linkStyle(newLinks.merge(existingLink));
    mergeLinks.exit().remove();
    existingLink = mergeLinks;

    const newNode = nodeAppend(selectNodes());
    const mergeNode = nodeStyle(newNode.merge(existingNode));
    mergeNode.exit().remove();
    existingNode = mergeNode;

    const newNodeShape = nodeShapeAppend(newNode);
    const mergeNodeShape = nodeShapeStyle(newNodeShape.merge(existingNodeShape));
    mergeNodeShape.exit().remove();
    existingNodeShape = mergeNodeShape;

    const newNodeText = nodeTextAppend(newNode);
    const mergeNodeText = nodeTextStyle(newNodeText.merge(existingNodeText));
    mergeNodeText.exit().remove();
    existingNodeText = mergeNodeText;
}

const statsList = document.getElementById("node-stats");
const possibleTitlesList = document.getElementById("node-titles");
const nodeSummaryDiv = document.getElementById("node-summary");

function removeChildren(element: HTMLElement) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}

function createLi(text: string): HTMLLIElement {
    const li = document.createElement("li");
    li.innerText = text;
    return li;
}

function displayNodeInfo(node: Node) {
    if (statsList !== null) {
        removeChildren(statsList);
        const percent = 100 * node.count / topLevelNode.count;
        statsList.appendChild(createLi(`${percent.toFixed(1)}% of comments`));
        statsList.appendChild(createLi(`${node.medianLikes} median likes`));
        statsList.appendChild(createLi(`${node.avgLikes} average likes`));
        statsList.appendChild(createLi(`${node.maxLikes} max likes`));
        statsList.appendChild(createLi(`${node.commentRms} semantic breadth`));
    }
    if (possibleTitlesList !== null) {
        removeChildren(possibleTitlesList);
        for (const title of node.titles) {
            const li = document.createElement("li");
            li.innerText = title;
            possibleTitlesList.appendChild(li);
        }
    }
    if (nodeSummaryDiv !== null) {
        removeChildren(nodeSummaryDiv);
        node.summary.split(/\n+/).forEach(paragraph => {
            const p = document.createElement("p");
            p.innerText = paragraph;
            nodeSummaryDiv.appendChild(p);
        });
    }
}

displayNodeInfo(topLevelNode);
topLevelNode.selected = true;
update();


// Add zoom behavior to the svg element
const zoom = d3
    .zoom<SVGSVGElement, unknown>()
    //.scaleExtent([0.5, 5])
    //.translateExtent([[0, 0], [width, height]])
    .on("zoom", e => {
        // console.log(`Zoom: ${e.transform}`);
        g.attr("transform", initialZoomTransform +
            e.transform.toString());
    });
svg.call(zoom);

