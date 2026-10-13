import React from 'react';
import './../App.css';

export default function Footer() {
    return (
        <footer className="site-footer">
            <p>© {new Date().getFullYear()} Club Ponthé — École nationale des ponts et chaussées</p>
        </footer>
    );
}
