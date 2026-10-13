import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Galleries from './Galleries';

jest.mock('js-cookie', () => ({
  get: jest.fn(() => 'fake-csrf-token'),
}));

jest.mock('./Navbar', () => () => <div data-testid="mock-navbar" />);

jest.mock('./GalleryMosaic', () => {
  return function MockGalleryMosaic(props) {
    return <div data-testid="gallery-mosaic" data-year={props.year} />;
  };
});

const mockGalleries = [
  { name: 'Croisière', slug: 'croisiere', sticker_url: '/media/croisiere/t.jpg', year: '2025-2026' },
  { name: 'Gala', slug: 'gala', sticker_url: '/media/gala/t.jpg', year: '2024-2025' },
];
const mockYears = [{ name: '2025-2026' }, { name: '2024-2025' }, { name: '2023-2024' }];

function mockFetch() {
  global.fetch = jest.fn((url) => {
    if (url.includes('/api/get_view')) {
      return Promise.resolve({ json: () => Promise.resolve(mockGalleries) });
    }
    if (url.includes('/api/years')) {
      return Promise.resolve({ json: () => Promise.resolve(mockYears) });
    }
    return Promise.resolve({ json: () => Promise.resolve([]) });
  });
}

describe('Galleries (page liste des galeries)', () => {
  beforeEach(() => {
    mockFetch();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders the pervenche banner with the title and the count of the year', async () => {
    render(<Galleries view="galerie" />);
    await waitFor(() =>
      expect(screen.getByText('1 galerie en 2025-2026')).toBeInTheDocument()
    );
    const title = screen.getByRole('heading', { level: 1, name: 'Galeries' });
    expect(title.closest('.hero-banner')).toBeInTheDocument();
  });

  test('the count follows the year picked', async () => {
    render(<Galleries view="galerie" />);
    await waitFor(() =>
      expect(screen.getByText('1 galerie en 2025-2026')).toBeInTheDocument()
    );
    fireEvent.click(screen.getByRole('button', { name: '2023-2024' }));
    expect(screen.getByText('0 galerie en 2023-2024')).toBeInTheDocument();
  });

  test('renders one pill per year, the first one active', async () => {
    render(<Galleries view="galerie" />);
    await waitFor(() =>
      expect(screen.getByRole('button', { name: '2025-2026' })).toBeInTheDocument()
    );
    expect(screen.getByRole('button', { name: '2025-2026' })).toHaveClass('active');
    expect(screen.getByRole('button', { name: '2024-2025' })).not.toHaveClass('active');
    expect(screen.getByRole('button', { name: '2023-2024' })).not.toHaveClass('active');
  });

  test('clicking a year pill updates the year passed to the mosaic', async () => {
    render(<Galleries view="galerie" />);
    await waitFor(() =>
      expect(screen.getByTestId('gallery-mosaic')).toBeInTheDocument()
    );
    expect(screen.getByTestId('gallery-mosaic').getAttribute('data-year')).toBe('2025-2026');
    fireEvent.click(screen.getByRole('button', { name: '2024-2025' }));
    await waitFor(() =>
      expect(screen.getByTestId('gallery-mosaic').getAttribute('data-year')).toBe('2024-2025')
    );
    expect(screen.getByRole('button', { name: '2024-2025' })).toHaveClass('active');
    expect(screen.getByRole('button', { name: '2025-2026' })).not.toHaveClass('active');
  });

  test('exposition view titles the banner Expositions', async () => {
    render(<Galleries view="exposition" />);
    await waitFor(() =>
      expect(screen.getByText('1 exposition en 2025-2026')).toBeInTheDocument()
    );
    expect(screen.getByRole('heading', { level: 1, name: 'Expositions' })).toBeInTheDocument();
  });

  test('no years available renders no pill and no mosaic (no crash)', async () => {
    global.fetch = jest.fn((url) => {
      if (url.includes('/api/get_view')) {
        return Promise.resolve({ json: () => Promise.resolve(mockGalleries) });
      }
      if (url.includes('/api/years')) {
        return Promise.resolve({ json: () => Promise.resolve([]) });
      }
      return Promise.resolve({ json: () => Promise.resolve([]) });
    });
    render(<Galleries view="galerie" />);
    // Laisse le fetch /api/years se résoudre (retour vide)
    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/years'),
        expect.anything()
      )
    );
    expect(screen.getByRole('heading', { level: 1, name: 'Galeries' })).toBeInTheDocument();
    expect(screen.queryByText(/galerie en/)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '2025-2026' })).not.toBeInTheDocument();
    expect(screen.queryByTestId('gallery-mosaic')).not.toBeInTheDocument();
  });

  test('App.css defines a visible focus style for year pills', () => {
    const fs = require('fs');
    const path = require('path');
    const css = fs.readFileSync(path.join(__dirname, '..', 'App.css'), 'utf8');
    expect(css).toMatch(/\.year-pill:focus-visible\s*\{/);
  });
});
