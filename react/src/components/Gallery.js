import React, {useState, useEffect} from 'react';
import './../App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import Cookies from 'js-cookie';
import CustomNavbar from './Navbar';
import PictureMosaic from './PictureMosaic';
import useSelection from './useSelection';
import ChecklistIcon from '@mui/icons-material/Checklist';

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

    return (
      <>
      <CustomNavbar/>
        <div className="introductive-content">
          <h2 className="gallery-title">{name}</h2>
          <ChecklistIcon className="select-toggle-icon" onClick={toggleSelectionMode}
            titleAccess={selectionMode ? 'Quitter le mode sélection' : 'Sélectionner des photos'}/>
        </div>
        {selectionMode && (
          <div className="selection-bar">
            <span aria-live="polite">{selected.size} photo(s) sélectionnée(s)</span>
            <button type="button" className="login-button" onClick={downloadSelected}
              disabled={selected.size === 0}>
              Télécharger la sélection
            </button>
          </div>
        )}
        <PictureMosaic result={result} selectionMode={selectionMode}
          selected={selected} onToggleSelect={toggleSelect}/>
      </>


      );
    }
