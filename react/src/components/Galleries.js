import React, {useState, useEffect} from 'react';
import './../App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import Cookies from 'js-cookie';
import CustomNavbar from './Navbar';
import GalleryMosaic from './GalleryMosaic';
import Footer from './Footer';

export default function Galleries(props) {
  const [years, setYears] = useState([]);
  const [year, setYear] = useState('');
  const [result, setResult] = useState([]);

  const requestOptions = {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': Cookies.get('csrftoken')
    },
  };

  useEffect(() => {
    fetch('/api/get_view?view=' + props.view, requestOptions)
      .then(res => res.json())
      .then(
        (result) => {
          setResult(result)
          fetch('/api/years', requestOptions)
            .then(res => res.json())
            .then(
              (result) => {
                setYears(result.map(y => y.name))
                setYear(result.length > 0 ? result[0].name : '')
              },
              (error) => {
                console.log(error)
              }
            );
        },
        (error) => {
          console.log(error)
        }
      );
  }, [])

  const title = props.view === 'exposition' ? 'Expositions' : 'Galeries';
  const count = Object.values(result || {}).filter(gallery => gallery.year == year).length;

  return (
      <>
        <CustomNavbar/>
        <div className="hero-banner">
          <div className="hero-banner-inner">
            <div>
              <h1 className="hero-title">{title}</h1>
              {year && (
                <p className="hero-count">
                  {count} {props.view === 'exposition' ? 'exposition' : 'galerie'}{count > 1 ? 's' : ''} en {year}
                </p>
              )}
            </div>
            <div className="year-pills">
              {years.map(y => (
                <button key={y} type="button"
                  className={'year-pill' + (y === year ? ' active' : '')}
                  aria-pressed={y === year}
                  onClick={() => setYear(y)}>
                  {y}
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="gallery-grid-overlap">
          {year && <GalleryMosaic result={result} year={year}/>}
        </div>
        <Footer/>
      </>
    )
}
