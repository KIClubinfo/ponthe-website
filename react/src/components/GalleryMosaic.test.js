import React from 'react';
import { render, screen } from '@testing-library/react';
import GalleryMosaic from './GalleryMosaic';

const galleries = [
  { name: 'Croisière', slug: 'croisiere', sticker_url: '/media/croisiere/t.jpg', year: '2025-2026' },
  { name: 'Gala', slug: 'gala', sticker_url: '/media/gala/t.jpg', year: '2024-2025' },
  { name: 'WEI', slug: 'wei', sticker_url: '/media/wei/t.jpg', year: '2025-2026' },
];

describe('GalleryMosaic', () => {
  test('shows the galleries of the year, each linked to its page', () => {
    render(<GalleryMosaic result={galleries} year="2025-2026" />);
    expect(screen.getByText('Croisière').closest('a')).toHaveAttribute('href', '/gallery/croisiere');
    expect(screen.getByText('WEI')).toBeInTheDocument();
    expect(screen.queryByText('Gala')).not.toBeInTheDocument();
  });

  test('follows the year when it changes', () => {
    const { rerender } = render(<GalleryMosaic result={galleries} year="2025-2026" />);
    rerender(<GalleryMosaic result={galleries} year="2024-2025" />);
    expect(screen.getByText('Gala')).toBeInTheDocument();
    expect(screen.queryByText('Croisière')).not.toBeInTheDocument();
  });

  test('says so when the year has no gallery, rather than leaving a blank page', () => {
    render(<GalleryMosaic result={galleries} year="2019-2020" />);
    expect(screen.getByText('Aucune galerie pour cette année.')).toBeInTheDocument();
  });
});
