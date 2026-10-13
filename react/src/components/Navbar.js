import React from 'react';
import './../App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';

// The page being read is underlined in the menu. The team has no page of
// its own: it is a section of the home page, never "the current one".
const linkClass = (...paths) => {
    const here = window.location.pathname;
    const current = paths.some(path => here === path || here.startsWith(path + '/'));
    return 'nav-text' + (current ? ' active' : '');
};

const CustomNavbar = ({props}) => {
    return (
        <Navbar collapseOnSelect expand="lg" data-bs-theme="dark" className='c-nav'>
          <Container>
            <Navbar.Brand href="/">
                <img src="/static/assets/img/logo-ponthe.png" alt="Ponthé" height="40"/>
            </Navbar.Brand>
            <Navbar.Toggle aria-controls="responsive-navbar-nav" />
            <Navbar.Collapse id="responsive-navbar-nav">
              <Nav className="me-auto align-items-lg-center">
                <a className={linkClass('/galleries', '/gallery')} href="/galleries">Galeries</a>
                <a className={linkClass('/expositions')} href="/expositions">Expositions</a>
                <a className="nav-text" href="/#team">Équipe</a>
                <a className={linkClass('/material')} href="/material">Matériel</a>
                {is_staff && (<a className={linkClass('/gestion')} href="/gestion">Gestion</a> )}
                {is_superuser && (<a className="nav-text" href="/admin">Admin</a> )}
              </Nav>
              <Nav className="align-items-lg-center">
                {!is_authenticated && (<a className="nav-text nav-cta" href="/login">Connexion</a> )}
                {is_authenticated && (<a className="nav-text nav-cta" href="/logout">Déconnexion</a> )}
              </Nav>
            </Navbar.Collapse>
          </Container>
        </Navbar>
      );
    }
export default CustomNavbar;
