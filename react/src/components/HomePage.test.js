import React from 'react';
import { render, screen, within } from '@testing-library/react';
import HomePage from './HomePage';

jest.mock('./Navbar', () => () => <div data-testid="mock-navbar" />);

// What index.html hands over: the team the admin has on display.
const team = {
  name: '029',
  photo: '/media/.equipe/029.jpg',
  sections: [
    {
      title: 'Le Bureau',
      roles: [
        { title: 'Présidente', people: ['Ada Lovelace'] },
        { title: 'Trez', people: ['Jean-Baptiste de La Salle'] },
      ],
    },
    {
      title: 'Pôle Création',
      roles: [
        { title: 'Photographes', people: ['Nadar', 'Vivian Maier', 'Robert Doisneau'] },
        { title: 'Respo Matos', people: ['Émile Reynaud'] },
      ],
    },
  ],
};

describe('HomePage', () => {
  test('renders the title once, as the heading of the page', () => {
    render(<HomePage team={team} />);
    expect(screen.getByRole('heading', { level: 1, name: 'Ponthé' })).toHaveClass('poster-title');
  });

  test('the group picture is an image of the page, not a background', () => {
    // The stylesheet lays it behind the text on a wide screen and above it,
    // whole, on a phone: that takes an element.
    render(<HomePage team={team} />);
    const photo = screen.getByAltText("L'équipe du Ponthé 029");
    expect(photo).toHaveClass('hero-photo');
    expect(photo).toHaveAttribute('src', '/media/.equipe/029.jpg');
    expect(photo.closest('.hero-section')).not.toHaveClass('hero-plain');
    expect(document.querySelectorAll('img').length).toBe(1);
  });

  test('the promotion comes from the team, in the hero and in the title of the credits', () => {
    render(<HomePage team={team} />);
    const hero = document.querySelector('.hero-section');
    expect(within(hero).getByText('029')).toHaveClass('badge-hero-yellow');
    expect(screen.getByRole('heading', { level: 2, name: "L'équipe 029" })).toHaveClass('team-section-title');
  });

  test('renders the subtitle about the club', () => {
    render(<HomePage team={team} />);
    expect(
      screen.getByText("Club photo & vidéo de l'École des Ponts")
    ).toBeInTheDocument();
  });

  test('renders the two hero pills with correct hrefs', () => {
    render(<HomePage team={team} />);
    const galeries = screen.getByRole('link', { name: /Accéder aux galeries/i });
    expect(galeries).toHaveAttribute('href', '/galleries');
    expect(galeries).toHaveClass('pill-yellow');
    const yt = screen.getByRole('link', { name: /Chaîne Youtube/i });
    expect(yt.getAttribute('href')).toContain('youtube.com');
    expect(yt).toHaveClass('pill-white');
  });

  test('renders the animated scroll chevron as an accessible link', () => {
    render(<HomePage team={team} />);
    const chevron = screen.getByRole('link', { name: "Voir l'équipe" });
    expect(chevron).toHaveAttribute('href', '#team');
    expect(chevron).toHaveClass('scroll-chevron');
    // Where it lands, and the "Équipe" link of the menu with it.
    expect(document.getElementById('team')).toHaveClass('team-section');
  });

  test('the team is set as end credits: a role, then whoever holds it', () => {
    render(<HomePage team={team} />);
    const bureau = screen.getByRole('heading', { name: 'Le Bureau' }).closest('.credits-group');
    const lines = bureau.querySelectorAll('.credits-line');
    expect(lines.length).toBe(2);
    expect(lines[0].querySelector('dt')).toHaveTextContent('Présidente');
    expect(lines[0].querySelector('dd')).toHaveTextContent('Ada Lovelace');
    expect(lines[1].querySelector('dt')).toHaveTextContent('Trez');
    expect(lines[1].querySelector('dd')).toHaveTextContent('Jean-Baptiste de La Salle');
    // Departments come in the order the admin gives them.
    expect(
      Array.from(document.querySelectorAll('.credits-group-title')).map(title => title.textContent)
    ).toEqual(['Le Bureau', 'Pôle Création']);
  });

  test('a role shared by several lists them one under the other', () => {
    render(<HomePage team={team} />);
    const group = screen.getByRole('heading', { name: 'Pôle Création' }).closest('.credits-group');
    const [crew, alone] = group.querySelectorAll('.credits-line');
    expect(crew.querySelector('dt')).toHaveTextContent('Photographes');
    expect(Array.from(crew.querySelectorAll('dd span')).map(name => name.textContent)).toEqual([
      'Nadar', 'Vivian Maier', 'Robert Doisneau',
    ]);
    expect(alone.querySelectorAll('dd span').length).toBe(1);
  });

  test('a role nobody holds yet is left out', () => {
    const vacant = {
      ...team,
      sections: [{ title: 'Le Bureau', roles: [
        { title: 'Présidente', people: ['Ada Lovelace'] },
        { title: 'Trez', people: [] },
      ] }],
    };
    render(<HomePage team={vacant} />);
    expect(document.querySelectorAll('.credits-line').length).toBe(1);
    expect(screen.queryByText('Trez')).not.toBeInTheDocument();
  });

  test('a team without a picture yet still has its page', () => {
    render(<HomePage team={{ ...team, photo: null }} />);
    expect(document.querySelector('img')).not.toBeInTheDocument();
    expect(document.querySelector('.hero-section')).toHaveClass('hero-plain');
    expect(screen.getAllByText('029').length).toBe(2);
    expect(screen.getByText('Ada Lovelace')).toBeInTheDocument();
  });

  test('no team on display: the page stands without one', () => {
    render(<HomePage team={null} />);
    expect(screen.getByRole('heading', { level: 1, name: 'Ponthé' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Accéder aux galeries/i })).toBeInTheDocument();
    expect(document.querySelector('.hero-section')).toHaveClass('hero-plain');
    expect(document.getElementById('team')).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: "Voir l'équipe" })).not.toBeInTheDocument();
    expect(document.querySelector('.hero-eyebrow')).not.toBeInTheDocument();
    // No credits to close: the footer keeps its usual look.
    expect(document.querySelector('.site-footer')).not.toHaveClass('site-footer-dark');
  });

  test('the footer closes the credits, dated from the current year', () => {
    render(<HomePage team={team} />);
    const line = screen.getByText(
      new RegExp('© ' + new Date().getFullYear() + ' Club Ponthé — École nationale des ponts et chaussées')
    );
    expect(line.closest('.site-footer')).toHaveClass('site-footer-dark');
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
