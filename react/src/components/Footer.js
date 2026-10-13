import React from 'react';
import './../App.css';

// `dark`: after the credits of the home page, which it closes.
export default function Footer({dark}) {
    return (
        <footer className={'site-footer' + (dark ? ' site-footer-dark' : '')}>
            <p>© {new Date().getFullYear()} Club Ponthé — École nationale des ponts et chaussées</p>
        </footer>
    );
}
