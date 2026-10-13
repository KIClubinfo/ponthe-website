import '../styles';
import HomePage from "../components/HomePage";
import React from "react";
import { createRoot } from "react-dom/client";

// The team on display comes with the page (index.html), not from a request.
const data = document.getElementById('team-data');
const team = data ? JSON.parse(data.textContent) : null;

const container = window.react_mount
const root = createRoot(container)
root.render(<HomePage team={team}/>)
