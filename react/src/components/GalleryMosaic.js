import React, { useEffect, useState, useRef } from 'react';
import './../App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import GalleryLink from './GalleryLink';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

const GalleryMosaic = (props) => {

    const [galleriesComp, setGalleriesComp] = useState([]);

    useEffect(() => {
        let galleriesTemp = []
        let compTemp = []
        for (const pic in props.result) {
            if (props.result[pic].year == props.year)
                galleriesTemp.push(props.result[pic])
        }
        galleriesTemp.forEach((gal, index) => {
            compTemp.push(<GalleryLink key={gal.slug} link={'/gallery/' + gal.slug} sticker={gal.sticker_url} title={gal.name} />)
        })
        setGalleriesComp(compTemp)
    }, [props.year])

    return (
        <>
            <Container fluid>
                <Row className="g-2 g-sm-4">
                    {galleriesComp}
                </Row>
            </Container>
        </>
    );
};

export default GalleryMosaic;
