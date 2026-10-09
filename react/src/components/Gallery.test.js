import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Gallery from './Gallery';

jest.mock('js-cookie', () => ({
  get: jest.fn(() => 'fake-csrf-token'),
}));

jest.mock('./Navbar', () => () => <div data-testid="mock-navbar" />);

// Capture les props passées à PictureMosaic
let mosaicProps;
jest.mock('./PictureMosaic', () => {
  return function MockPictureMosaic(props) {
    mosaicProps = props;
    return <div data-testid="picture-mosaic" />;
  };
});

global.gallery_slug = 'test-gallery';

const mockPicsResponse = [
  {
    id: 1,
    file_name: 'photo1',
    file_extension: 'jpg',
    file_full_name: 'photo1.jpg',
    gallery: 1,
    link: '/media/test-gallery',
  },
  {
    id: 2,
    file_name: 'photo2',
    file_extension: 'jpg',
    file_full_name: 'photo2.jpg',
    gallery: 1,
    link: '/media/test-gallery',
  },
];

const mockGalleryResponse = {
  name: 'Ma Galerie Test',
};

function mockFetch(withDownload = false) {
  global.fetch = jest.fn((url) => {
    if (withDownload && url.includes('/api/gallery/pics/download/')) {
      return Promise.resolve({
        ok: true,
        blob: () => Promise.resolve(new Blob(['zip'])),
      });
    }
    if (url.includes('/api/gallery/pics/')) {
      return Promise.resolve({ json: () => Promise.resolve(mockPicsResponse) });
    }
    return Promise.resolve({ json: () => Promise.resolve(mockGalleryResponse) });
  });
}

describe('Gallery selection mode', () => {
  beforeEach(() => {
    mockFetch();
    URL.createObjectURL = jest.fn(() => 'blob:fake');
    URL.revokeObjectURL = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('the select button toggles selection mode', async () => {
    render(<Gallery />);
    await waitFor(() => expect(screen.getByText('Ma Galerie Test')).toBeInTheDocument());

    expect(mosaicProps.selectionMode).toBe(false);
    expect(screen.queryByText('Télécharger la sélection')).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId('ChecklistIcon'));
    expect(mosaicProps.selectionMode).toBe(true);
    expect(screen.getByText('Télécharger la sélection')).toBeInTheDocument();

    fireEvent.click(screen.getByTestId('ChecklistIcon'));
    expect(mosaicProps.selectionMode).toBe(false);
    expect(screen.queryByText('Télécharger la sélection')).not.toBeInTheDocument();
  });

  test('download button is disabled with an empty selection', async () => {
    render(<Gallery />);
    await waitFor(() => expect(screen.getByText('Ma Galerie Test')).toBeInTheDocument());

    fireEvent.click(screen.getByTestId('ChecklistIcon'));
    expect(screen.getByText('Télécharger la sélection')).toBeDisabled();
    expect(screen.getByText('0 photo(s) sélectionnée(s)')).toBeInTheDocument();
  });

  test('downloading the selection calls the API with the selected names', async () => {
    mockFetch(true);
    render(<Gallery />);
    await waitFor(() => expect(screen.getByText('Ma Galerie Test')).toBeInTheDocument());

    fireEvent.click(screen.getByTestId('ChecklistIcon'));
    mosaicProps.onToggleSelect('photo1.jpg');
    mosaicProps.onToggleSelect('photo2.jpg');
    await waitFor(() => expect(screen.getByText('2 photo(s) sélectionnée(s)')).toBeInTheDocument());

    fireEvent.click(screen.getByText('Télécharger la sélection'));
    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/gallery/pics/download/',
        expect.objectContaining({ method: 'POST' })
      )
    );
    const [url, options] = global.fetch.mock.calls.find(
      ([u]) => u === '/api/gallery/pics/download/'
    );
    expect(JSON.parse(options.body)).toEqual({
      slug: 'test-gallery',
      file_full_names: ['photo1.jpg', 'photo2.jpg'],
    });
  });

  test('a refused download shows the reason given by the server', async () => {
    mockFetch();
    const baseFetch = global.fetch;
    global.fetch = jest.fn((url, options) => {
      if (url.includes('/api/gallery/pics/download/')) {
        return Promise.resolve({
          ok: false,
          status: 400,
          json: () => Promise.resolve({
            status: 'error',
            message: 'Sélection trop grande : 100 photos au maximum par téléchargement.',
          }),
        });
      }
      return baseFetch(url, options);
    });
    window.alert = jest.fn();
    render(<Gallery />);
    await waitFor(() => expect(screen.getByText('Ma Galerie Test')).toBeInTheDocument());

    fireEvent.click(screen.getByTestId('ChecklistIcon'));
    mosaicProps.onToggleSelect('photo1.jpg');
    await waitFor(() => expect(screen.getByText('1 photo(s) sélectionnée(s)')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Télécharger la sélection'));

    await waitFor(() =>
      expect(window.alert).toHaveBeenCalledWith(
        'Sélection trop grande : 100 photos au maximum par téléchargement.'
      )
    );
    expect(URL.createObjectURL).not.toHaveBeenCalled();
  });

  test('leaving selection mode clears the selection', async () => {
    render(<Gallery />);
    await waitFor(() => expect(screen.getByText('Ma Galerie Test')).toBeInTheDocument());

    fireEvent.click(screen.getByTestId('ChecklistIcon'));
    mosaicProps.onToggleSelect('photo1.jpg');
    await waitFor(() => expect(screen.getByText('1 photo(s) sélectionnée(s)')).toBeInTheDocument());

    fireEvent.click(screen.getByTestId('ChecklistIcon'));
    fireEvent.click(screen.getByTestId('ChecklistIcon'));
    expect(screen.getByText('0 photo(s) sélectionnée(s)')).toBeInTheDocument();
  });

  test('App.css reserves room for the select-toggle button next to the title', () => {
    const fs = require('fs');
    const path = require('path');
    const css = fs.readFileSync(path.join(__dirname, '..', 'App.css'), 'utf8');
    expect(css).toMatch(/@media[^{]*min-width:\s*576px[^}]*\.gallery-title\s*\{[^}]*max-width:\s*60%/);
  });
});
