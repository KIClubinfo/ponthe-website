import React from 'react';
import { render, screen } from '@testing-library/react';
import CustomNavbar from './Navbar';

// En production, header.html définit les globales is_authenticated / is_staff /
// is_superuser avant le chargement du bundle React.
describe('CustomNavbar', () => {
  afterEach(() => {
    delete global.is_authenticated;
    delete global.is_staff;
    delete global.is_superuser;
    window.history.pushState({}, '', '/');
  });

  test('la page en cours est marquée dans le menu', () => {
    global.is_authenticated = true;
    global.is_staff = true;
    global.is_superuser = false;
    const active = () =>
      Array.from(document.querySelectorAll('.nav-text.active')).map(a => a.textContent);

    const pages = {
      '/': [],
      '/galleries/': ['Galeries'],
      '/gallery/gala': ['Galeries'],
      '/expositions/': ['Expositions'],
      '/material/': ['Matériel'],
      '/gestion/gallery/gala': ['Gestion'],
    };
    for (const [path, expected] of Object.entries(pages)) {
      window.history.pushState({}, '', path);
      const { unmount } = render(<CustomNavbar />);
      expect(active()).toEqual(expected);
      unmount();
    }
  });

  test('visiteur anonyme : lien Connexion, pas de lien Déconnexion', () => {
    global.is_authenticated = false;
    global.is_staff = false;
    global.is_superuser = false;
    render(<CustomNavbar />);
    expect(screen.getByText('Connexion').closest('a')).toHaveAttribute('href', '/login');
    expect(screen.queryByText('Déconnexion')).not.toBeInTheDocument();
  });

  test('utilisateur connecté : lien Déconnexion (avec accent) vers /logout', () => {
    global.is_authenticated = true;
    global.is_staff = false;
    global.is_superuser = false;
    render(<CustomNavbar />);
    expect(screen.getByText('Déconnexion').closest('a')).toHaveAttribute('href', '/logout');
    expect(screen.queryByText('Connexion')).not.toBeInTheDocument();
  });

  test('staff : lien Gestion ; superuser : lien Admin', () => {
    global.is_authenticated = true;
    global.is_staff = true;
    global.is_superuser = true;
    render(<CustomNavbar />);
    expect(screen.getByText('Gestion').closest('a')).toHaveAttribute('href', '/gestion');
    expect(screen.getByText('Admin').closest('a')).toHaveAttribute('href', '/admin');
  });

  test('les liens publics sont Galeries, Expositions, Équipe et Matériel', () => {
    global.is_authenticated = false;
    global.is_staff = false;
    global.is_superuser = false;
    render(<CustomNavbar />);
    expect(screen.getByText('Galeries').closest('a')).toHaveAttribute('href', '/galleries');
    expect(screen.getByText('Expositions').closest('a')).toHaveAttribute('href', '/expositions');
    expect(screen.getByText('Équipe').closest('a')).toHaveAttribute('href', '/#team');
    expect(screen.getByText('Matériel').closest('a')).toHaveAttribute('href', '/material');
  });
});
