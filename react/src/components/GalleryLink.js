import React from 'react';
import './../App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import Col from 'react-bootstrap/Col';

const GalleryLink = (props) => {
    return(
          <Col xs="6" lg="4" xl="3">
            <a className="gallery-card-affiche" href={props.link}>
              <div className="gallery-image-container">
                <img className="galleries-img" src={props.sticker} alt={props.title}/>
              </div>
              <div className="gallery-card-footer-strip"></div>
              <h3 className="gallery-title-label">{props.title}</h3>
            </a>
          </Col>
    );
};

export default GalleryLink;
