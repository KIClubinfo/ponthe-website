import React from 'react';
import './../App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import GalleryLink from './GalleryLink';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

const GalleryMosaic = (props) => {
    const galleries = Object.values(props.result || {}).filter(gal => gal.year == props.year);

    if (galleries.length === 0) {
        return <p className="gallery-grid-empty">Aucune galerie pour cette année.</p>;
    }
    return (
        <Container fluid>
            <Row className="g-2 g-sm-3 g-lg-4">
                {galleries.map(gal => (
                    <GalleryLink key={gal.slug} link={'/gallery/' + gal.slug} sticker={gal.sticker_url} title={gal.name} />
                ))}
            </Row>
        </Container>
    );
};

export default GalleryMosaic;
