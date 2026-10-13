import React from 'react';
import { render, screen } from '@testing-library/react';
import HomePage from './HomePage';

jest.mock('./Navbar', () => () => <div data-testid="mock-navbar" />);

describe('HomePage', () => {
  test('renders the title once, as the heading of the page', () => {
    render(<HomePage />);
    expect(screen.getByRole('heading', { level: 1, name: 'Ponthé' })).toHaveClass('poster-title');
  });

  test('the group picture is an image of the page, not a background', () => {
    // The stylesheet lays it behind the text on a wide screen and above it,
    // whole, on a phone: that takes an element.
    render(<HomePage />);
    const photo = screen.getByAltText("L'équipe du Ponthé 028");
    expect(photo).toHaveClass('hero-photo');
    expect(photo.closest('.hero-section')).toBeInTheDocument();
    expect(document.querySelectorAll('img').length).toBe(1);
  });

  test('renders the yellow 028 badge', () => {
    render(<HomePage />);
    expect(screen.getByText('028')).toHaveClass('badge-hero-yellow');
  });

  test('renders the subtitle about the club', () => {
    render(<HomePage />);
    expect(
      screen.getByText("Club photo & vidéo de l'École des Ponts")
    ).toBeInTheDocument();
  });

  test('renders the two hero pills with correct hrefs', () => {
    render(<HomePage />);
    const galeries = screen.getByRole('link', { name: /Accéder aux galeries/i });
    expect(galeries).toHaveAttribute('href', '/galleries');
    expect(galeries).toHaveClass('pill-yellow');
    const yt = screen.getByRole('link', { name: /Chaîne Youtube/i });
    expect(yt.getAttribute('href')).toContain('youtube.com');
    expect(yt).toHaveClass('pill-white');
  });

  test('renders the animated scroll chevron as an accessible link', () => {
    render(<HomePage />);
    const chevron = screen.getByRole('link', { name: "Voir l'équipe" });
    expect(chevron).toHaveAttribute('href', '#team');
    expect(chevron).toHaveClass('scroll-chevron');
  });

  test('renders the team section with roster cards', () => {
    render(<HomePage />);
    expect(screen.getByText(/l'équipe/i)).toBeInTheDocument();
    expect(screen.getByText('Le Bureau')).toBeInTheDocument();
    expect(screen.getByText('Responsables')).toBeInTheDocument();
    expect(screen.getByText('Pôle Création')).toBeInTheDocument();
    expect(screen.getByText(/Présidente/)).toBeInTheDocument();
    expect(document.querySelectorAll('.roster-card-item').length).toBe(3);
    // Where the "Équipe" link of the menu and the arrow of the hero land.
    expect(document.getElementById('team')).toHaveClass('team-section');
  });

  test('renders the footer', () => {
    render(<HomePage />);
    expect(
      screen.getByText(/Club Ponthé — École nationale des ponts et chaussées/i)
    ).toBeInTheDocument();
  });

  test('App.css keeps the hero above the fold (subtracts the navbar height)', () => {
    const fs = require('fs');
    const path = require('path');
    const css = fs.readFileSync(path.join(__dirname, '..', 'App.css'), 'utf8');
    expect(css).toMatch(/\.hero-section\s*\{[^}]*calc\(100vh - 64px\)/);
    expect(css).toMatch(/\.hero-section\s*\{[^}]*calc\(100svh - 64px\)/);
  });

  test('App.css stacks the hero on upright screens, tablets included', () => {
    const fs = require('fs');
    const path = require('path');
    const css = fs.readFileSync(path.join(__dirname, '..', 'App.css'), 'utf8');
    expect(css).toMatch(
      /@media[^{]*max-width:\s*767px[^{]*orientation:\s*portrait[^{]*\{\s*\.hero-section\s*\{[^}]*min-height:\s*0/
    );
  });
});
