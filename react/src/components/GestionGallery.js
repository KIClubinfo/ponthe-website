import React, {useState, useEffect, useRef} from 'react';
import './../App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import DownloadIcon from '@mui/icons-material/Download';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import DeleteIcon from '@mui/icons-material/Delete';
import FlagIcon from '@mui/icons-material/Flag';
import ReportList from './ReportList';
import GallerySticker from './GallerySticker'
import Cookies from 'js-cookie';
import CustomNavbar from './Navbar';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import ChecklistIcon from '@mui/icons-material/Checklist';
import ListIcon from '@mui/icons-material/List';
import {Stack, Select, MenuItem} from '@mui/material';

export default function Gallery({props}){

    //Modal open state
    const [state, setState] = useState(false);
    //Current loaded picture in modal
    const [current, setCurrent] = useState(null);
    const [picsData, setPicsData] = useState([]);
    const [pics, setPics] = useState([]);
    const [name, setName] = useState('');
    const [addModalState, setaddModalState] = useState(false);
    const [visibility, setVisibility] = useState('privée');
    const [view, setView] = useState('gallery');
    //Reports received state
    const [reports, setReports] = useState(null);
    const [uploadError, setUploadError] = useState('');
    const [uploading, setUploading] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    const [isCompact, setIsCompact] = useState(false);
    // Mode sélection multiple
    const [selectionMode, setSelectionMode] = useState(false);
    const [selected, setSelected] = useState(new Set());

    // Filtre « photos signalées » : actif ou non
    const [reportsOnly, setReportsOnly] = useState(false);
    const [reportedNames, setReportedNames] = useState(new Set());

    const requestOptions = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': Cookies.get('csrftoken') },
      body: JSON.stringify({ slug: gallery_slug })
    };

    //Open image in full screen when vignette is clicked
    const toggleModal = (e, img) => {
      setCurrent(img)
      setState(true)
    };

    //Close image modal
    const closeModal = () => {
      setState(false)
    };

    const openAddModal = () => {
      setUploadError('');
      setSelectedFile(null);
      setaddModalState(true)
    }

    const closeAddModal = () => {
      setaddModalState(false)
    }

    const handleUpload = async (e) => {
      e.preventDefault();
      setUploadError('');

      if (!selectedFile) {
        setUploadError('Veuillez sélectionner un fichier .zip.');
        return;
      }

      setUploading(true);

      const formData = new FormData();
      formData.append('zipfile', selectedFile);

      try {
        const response = await fetch('/gestion/gallery/' + gallery_slug, {
          method: 'POST',
          headers: {
            'X-CSRFToken': Cookies.get('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: formData,
        });

        let data = {};
        try {
          data = await response.json();
        } catch (parseError) {
          // Réponse non JSON (page d'erreur d'un proxy, ...) : data reste vide
        }

        if (response.status === 413) {
          // Refused by nginx before it reaches the application
          setUploadError('Le fichier dépasse la taille maximale autorisée (2 Go).');
        } else if (!response.ok || data.status === 'error') {
          setUploadError(data.message || 'Une erreur est survenue lors de l\'envoi.');
        } else {
          // Succès : fermer le modal et recharger la page
          closeAddModal();
          window.location.reload(false);
        }
      } catch (err) {
        console.log(err)
        setUploadError('Erreur réseau : impossible de contacter le serveur.');
      } finally {
        setUploading(false);
      }
    };

    const toggleCompact = () => {
      setIsCompact(prev => !prev);
    }

    //Enter/leave the multi-selection mode; leaving clears the selection
    const toggleSelectionMode = () => {
      setSelectionMode(prev => !prev);
      setSelected(new Set());
    }

    //Add/remove one picture from the selection
    const toggleSelect = (fileFullName) => {
      setSelected(prev => {
        const next = new Set(prev);
        if (next.has(fileFullName)) {
          next.delete(fileFullName);
        } else {
          next.add(fileFullName);
        }
        return next;
      });
    }

    //Download the selection as a single zip built by the backend
    const downloadSelected = async () => {
      if (selected.size === 0) return;
      const downloadOptions = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': Cookies.get('csrftoken') },
        body: JSON.stringify({ slug: gallery_slug, file_full_names: Array.from(selected) })
      };
      try {
        const response = await fetch('/api/gallery/pics/download/', downloadOptions);
        if (!response.ok) {
          alert('Impossible de télécharger les photos sélectionnées.');
          return;
        }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = gallery_slug + '-selection.zip';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      } catch (err) {
        console.log(err);
        alert('Erreur réseau : impossible de contacter le serveur.');
      }
    }

    //Delete every selected picture after a confirmation
    const deleteSelected = () => {
      if (selected.size === 0) return;
      if (!window.confirm('Supprimer ' + selected.size + ' photo(s) ?')) return;
      const deleteOptions = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': Cookies.get('csrftoken') },
        body: JSON.stringify({ slug: gallery_slug, file_full_names: Array.from(selected) })
      };
      fetch('/api/gallery/pics/delete_many/', deleteOptions)
            .then(res => res.json())
            .then(
              (result) => {
                if (result.status === 'error') {
                  alert(result.message)
                  return
                }
                window.location.reload(false)
              },
              (error) => {
                console.log(error)
                alert('Impossible de supprimer les photos sélectionnées.')
              }
            );
    }

    //Goto next picture in modal
    const nextPicture = () => {
      console.log(pics)
      let nextId = pics.indexOf(current)+1;
      if(nextId == pics.length) nextId = 0
      setCurrent(pics[nextId]);
    };

    const deleteCurrent = () => {
      const array = current.split('/')
      const deleteOptions = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': Cookies.get('csrftoken') },
        body: JSON.stringify({ name: name, file_full_name: array[array.length-1] })
      };
      fetch('/api/gallery/pics/delete/', deleteOptions)
            .then(res => res.json())
            .then(
              (result) => {
                window.location.reload(false)
              },
              (error) => {
                console.log(error)
              }
            );
    };

    const deleteGallery = () => {
      if (!window.confirm('Supprimer la galerie « ' + name + ' » et toutes ses photos ?')) return
      const deleteOptions = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': Cookies.get('csrftoken') },
        body: JSON.stringify({ name: name})
      };
      fetch('/api/gallery/delete/', deleteOptions)
            .then(res => res.json())
            .then(
              (result) => {
                window.location.href = '/gestion/'
              },
              (error) => {
                console.log(error)
              }
            );
    };
    //Goto previous picture in modal
    const previousPicture = () => {
      let nextId = pics.indexOf(current)-1;
      if(nextId == -1) nextId = pics.length-1
      setCurrent(pics[nextId]);
    };

    useEffect(() => {
      let picsTemp = []
      fetch('/api/gallery/pics/', requestOptions)
      .then(res => res.json())
      .then(
        (result) => {
          for(const pic in result){
            picsTemp.push(result[pic].link + '/uploads/' + result[pic].file_full_name)
          }
          setPicsData(result)
          setPics(picsTemp)
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
                  setVisibility(result.visibility)
                  setView(result.view)
                },
                (error) => {
                  console.log(error)
                }
              );

    }, [])


    const ref = useRef(null);
    const ref2 = useRef(null);
    const ref3 = useRef(null)
    const ref4 = useRef(null)
    const ref5 = useRef(null)

          useEffect(() => {
            const handleClickOutside = (event) => {
              if (ref.current && !ref.current.contains(event.target)
                && ref2.current && !ref2.current.contains(event.target)
                && ref3.current && !ref3.current.contains(event.target)
                && ref4.current && !ref4.current.contains(event.target)
                && ref5.current && !ref5.current.contains(event.target)) {
                closeModal()
              }
            };
            document.addEventListener('click', handleClickOutside, true);
            return () => {
              document.removeEventListener('click', handleClickOutside, true);
            };
          },[]);


    const changeVisibility = (visibility) => {
      const visibilityOptions = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': Cookies.get('csrftoken') },
        body: JSON.stringify({ slug: gallery_slug, visibility: visibility})
      };

      fetch('/api/gallery/change_visibility/', visibilityOptions)
            .then(res => res.json())
            .then(
              (result) => {
                setVisibility(result.visibility)
              },
              (error) => {
                console.log(error)
              }
          );
    }
    // A report has been dealt with, or was groundless: take it off the list.
    // The picture leaves the "reported" filter once its last report is gone.
    const dismissReport = (reportId) => {
      const dismissOptions = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': Cookies.get('csrftoken') },
        body: JSON.stringify({ id: reportId })
      };
      fetch('/api/gallery/reports/dismiss/', dismissOptions)
            .then(res => {
              if (!res.ok) {
                alert("Impossible de classer ce signalement.")
                return
              }
              const remaining = reports.filter(r => r.id !== reportId)
              setReports(remaining)
              setReportedNames(new Set(remaining.map(r => r.file_full_name)))
            })
            .catch((error) => {
              console.log(error)
              alert("Impossible de classer ce signalement.")
            });
    }


    const changeView = (view) => {
      const visibilityOptions = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': Cookies.get('csrftoken') },
        body: JSON.stringify({ slug: gallery_slug, view: view})
      };

      fetch('/api/gallery/change_view/', visibilityOptions)
            .then(res => res.json())
            .then(
              (result) => {
                setVisibility(result.visibility)
              },
              (error) => {
                console.log(error)
              }
          );
    }

    const loadReports = () => {
      const reportOptions = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': Cookies.get('csrftoken') },
        body: JSON.stringify({ slug: gallery_slug })
      };
      fetch('/api/gallery/reports/', reportOptions)
            .then(res => {
              if (!res.ok) {
                alert("Impossible de charger les signalements.")
                return null
              }
              return res.json()
            })
            .then(
              (result) => {
                if (Array.isArray(result)) {
                  setReports(result)
                }
              },
              (error) => {
                console.log(error)
              }
            );
    }

    // The flag is a toggle: only reported pictures, then back to normal
    const toggleReportsOnly = () => {
      if (reportsOnly) {
        setReportsOnly(false)
        return
      }
      const reportOptions = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': Cookies.get('csrftoken') },
        body: JSON.stringify({ slug: gallery_slug })
      };
      fetch('/api/gallery/reports/', reportOptions)
            .then(res => {
              if (!res.ok) {
                alert("Impossible de charger les signalements.")
                return null
              }
              return res.json()
            })
            .then(
              (result) => {
                if (Array.isArray(result)) {
                  setReportedNames(new Set(result.map(r => r.file_full_name)))
                  setReportsOnly(true)
                }
              },
              (error) => {
                console.log(error)
              }
            );
    }

    const displayedPics = reportsOnly
      ? picsData.filter(pic => reportedNames.has(pic.file_full_name))
      : picsData;
    return (
      <>
      <CustomNavbar/>
      <div className="introductive-content">
        <h1 className="gallery-title">{name}</h1>
          <Stack direction="row" alignItems="center" gap={1}>
            <span className='centered-button'>
              <AddCircleOutlineIcon className="icon" onClick={openAddModal}/>
              <DeleteIcon onClick={deleteGallery} className="icon"/>
              <FlagIcon onClick={toggleReportsOnly}
                className={'icon' + (reportsOnly ? ' icon-active' : '')}
                titleAccess={reportsOnly ? 'Afficher toutes les photos' : 'Photos signalées'}/>
              {reportsOnly && (
                <ListIcon className="icon" onClick={loadReports} titleAccess="Détails des signalements"/>
              )}
              <ChecklistIcon className="icon" onClick={toggleSelectionMode}
                titleAccess={selectionMode ? 'Quitter le mode sélection' : 'Sélectionner des photos'}/>
              {isCompact
                ? <ZoomInIcon className="icon" onClick={toggleCompact} titleAccess="Vue normale"/>
                : <ZoomOutIcon className="icon" onClick={toggleCompact} titleAccess="Vue dézoomée"/>
              }
              <Select style={{padding:0, height: "40px"}}value={visibility} onChange={e =>
              {
                setVisibility(e.target.value)
                changeVisibility(e.target.value)
              }} label="Visibilité">
                  <MenuItem value={'privée'}>Privée</MenuItem>
                  <MenuItem value={'école'}>École</MenuItem>
                  <MenuItem value={'publique'}>Publique</MenuItem>
                </Select>
                <Select style={{padding:0, height: "40px"}}value={view} onChange={e =>
              {
                setView(e.target.value)
                changeView(e.target.value)
              }} label="Vue">
                  <MenuItem value={'galerie'}>Galerie</MenuItem>
                  <MenuItem value={'exposition'}>Exposition</MenuItem>
                </Select>
              </span>
          </Stack>
        {selectionMode && (
          <div className="selection-bar">
            <span aria-live="polite">{selected.size} photo(s) sélectionnée(s)</span>
            <button type="button" className="login-button" onClick={downloadSelected}
              disabled={selected.size === 0}>
              Télécharger la sélection
            </button>
            <button type="button" className="login-button" onClick={deleteSelected}
              disabled={selected.size === 0}>
              Supprimer la sélection
            </button>
          </div>
        )}
        </div>
        <Container fluid>
          <Row className='g-1'>
            {displayedPics.map((pic, index) => (
              <Col key={index} xs={isCompact ? "3" : "4"} sm={isCompact ? "2" : "3"} lg={isCompact ? "1" : "2"}>
                <GallerySticker img={pic.link + '/uploads/' + pic.file_full_name}
                                thumb={pic.link + '/thumbnails/' + pic.file_full_name}
                                modal_func={toggleModal}
                                compact={isCompact}
                                selectionMode={selectionMode}
                                selected={selected.has(pic.file_full_name)}
                                onToggleSelect={toggleSelect}
                                fileFullName={pic.file_full_name}/>
              </Col>
            ))}
          </Row>
        </Container>

        {state && (
          <div className='pic-modal'>
            <ArrowBackIcon ref={ref2} onClick={previousPicture} className='arrow left-arrow'/>
            <ArrowForwardIcon ref={ref3} onClick={nextPicture} className='arrow right-arrow'/>
            <div className="pic-modal-nav">
              <span className='close' onClick={closeModal}>&times;</span>
              <a href={current} download={current}><span ref={ref4}><DownloadIcon className="download"/></span></a>
              <span ref={ref5}><DeleteIcon onClick={deleteCurrent} className="download" /></span>
            </div>
            <div className='pic-modal-content'>
              <div ref={ref} className="img-browser">
                <img src={current} className='img-modal'/>
              </div>
            </div>
          </div>
          )
        }

        {addModalState && (
          <div className='pic-modal'>
            <div ref={ref} className='add-modal-content'>
              <span className='close-white-modal' onClick={closeAddModal}>&times;</span>
              <form className="post-form" onSubmit={handleUpload}>
                  <input
                    type='file'
                    name='zipfile'
                    accept='.zip'
                    onChange={(e) => setSelectedFile(e.target.files[0] || null)}
                  />
                  {uploadError && <p className="upload-error" role="alert">{uploadError}</p>}
                  <button
                    type="submit"
                    className="login-button"
                    disabled={uploading}
                  >
                    {uploading ? 'Envoi en cours...' : "Lancer l'envoi"}
                  </button>
                </form>
            </div>
          </div>
          )
        }

        {/* ref est partagé entre les modals : un seul est ouvert à la fois, comme l'add-modal. */}
        {reports !== null && (
          <div className='pic-modal'>
            <div ref={ref} className='add-modal-content'>
              <span className='close-white-modal' onClick={() => setReports(null)}>&times;</span>
              <h3>Signalements</h3>
              <ReportList reports={reports} onDismiss={dismissReport}/>
            </div>
          </div>
          )
        }
      </>


      );
    }
