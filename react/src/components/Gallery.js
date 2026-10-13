import React, {useState, useEffect} from 'react';
import './../App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import Cookies from 'js-cookie';
import CustomNavbar from './Navbar';
import PictureMosaic from './PictureMosaic';
import useSelection from './useSelection';
import ChecklistIcon from '@mui/icons-material/Checklist';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import Footer from './Footer';

export default function Gallery({props}){

    const [name, setName] = useState('');
    //List of picture in the gallery
    const [result, setResult] = useState([]);
    const {selectionMode, selected, toggleSelectionMode, toggleSelect, downloadSelected} = useSelection(gallery_slug);

    const requestOptions = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': Cookies.get('csrftoken') },
      body: JSON.stringify({ slug: gallery_slug })
    };

    useEffect(() => {
      fetch('/api/gallery/pics/', requestOptions)
            .then(res => res.json())
            .then(
              (result) => {
                setResult(result)
              },
              (error) => {
                console.log(error)
              }
            );
          fetch('/api/gallery/', requestOptions)
            .then(res => res.json())
            .then(
              (result) => {
                setName(result.name)
              },
              (error) => {
                console.log(error)
              }
            );
    }, [])

    const count = Object.keys(result || {}).length;

    return (
      <>
      <CustomNavbar/>
        <div className="page-head">
          <div className="page-head-text">
            <a className="page-back" href="/galleries"><ArrowBackIcon/>Galeries</a>
            <h1 className="gallery-title">{name}</h1>
            {count > 0 && <p className="page-meta">{count} photo{count > 1 ? 's' : ''}</p>}
          </div>
          <div className="page-head-actions">
            <button type="button" className={'p-btn p-btn-ghost' + (selectionMode ? ' is-on' : '')}
              aria-pressed={selectionMode} onClick={toggleSelectionMode}>
              <ChecklistIcon/>
              {selectionMode ? 'Terminer' : 'Sélectionner'}
            </button>
          </div>
        </div>
        {selectionMode && (
          <div className="selection-bar">
            <span className="selection-bar-count" aria-live="polite">{selected.size} photo(s) sélectionnée(s)</span>
            <button type="button" className="p-btn p-btn-primary" onClick={downloadSelected}
              disabled={selected.size === 0}>
              Télécharger la sélection
            </button>
          </div>
        )}
        <PictureMosaic result={result} selectionMode={selectionMode}
          selected={selected} onToggleSelect={toggleSelect}/>
        <Footer/>
      </>
      );
    }
