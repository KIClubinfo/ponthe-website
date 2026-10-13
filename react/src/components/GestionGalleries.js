import React, {useState, useEffect, useRef} from 'react';
import './../App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Cookies from 'js-cookie';
import GalleryLink from './GalleryLink';
import CustomNavbar from './Navbar'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import GroupsIcon from '@mui/icons-material/Groups';
import { TextField, Select, MenuItem } from '@mui/material';

export default function Gallery(){
    const [addModalState, setaddModalState] = useState(false);
    const [galleriesComp, setGalleriesComp] = useState([]);

    const [name, setName] = useState('')
    const [description, setDescription] = useState('')
    const [visibility, setVisibility] = useState('privée')
    const [type, setType] = useState('photo')
    const [view, setView] = useState('galerie')
    const [error, setError] = useState('')

    const requestOptions = {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': Cookies.get('csrftoken') },
      };

      const openModal = () => {
        setaddModalState(true)
      };

      const closeModal = () => {
        setaddModalState(false)
      };

      const onSubmit = () => {
        const submitOptions = {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': Cookies.get('csrftoken') },
            body: JSON.stringify({name: name, description: description, visibility: visibility,  type: type, view: view})
        };
        fetch('/api/galleries/create/', submitOptions)
              .then(res => res.json())
              .then(
                (result) => {
                  if(result.name == undefined)
                    setError('Une erreur inconnue est survenue')
                  if(result.status != undefined && result.status == 'error'){
                    setError(result.message)
                  }else
                    window.location.reload(false)
                },
                (error) => {
                  console.log(error)
                }
              );
      }
    useEffect(() => {
        let galleriesTemp = []
        let compTemp = []
        fetch('/api/get_view', requestOptions)
              .then(res => res.json())
              .then(
                (result) => {
                  for(const pic in result){
                    galleriesTemp.push(result[pic])
                  }
                  galleriesTemp.forEach((gal, index) =>{
                    compTemp.push(<GalleryLink key={gal.slug} link={'/gestion/gallery/' + gal.slug} sticker={gal.sticker_url} title={gal.name}/>)
                  })
                  setGalleriesComp(compTemp)
                },
                (error) => {
                  console.log(error)
                }
              );
      }, [])


      const ref = useRef(null);
      const ref2 = useRef(null);

        /*  useEffect(() => {
            const handleClickOutside = (event) => {
              if (ref.current && !ref.current.contains(event.target)
                 && ref2.current && !ref2.current.contains(event.target)) {
                closeModal()
              }
            };
            document.addEventListener('click', handleClickOutside, true);
            return () => {
              document.removeEventListener('click', handleClickOutside, true);
            };
          },[]);*/

    return(
      <>
        <CustomNavbar/>
        <div className="page-head">
          <div className="page-head-text">
            <h1 className="gallery-title">Gestion des galeries</h1>
            <p className="page-meta">{galleriesComp.length} galerie{galleriesComp.length > 1 ? 's' : ''}, toutes visibilités confondues</p>
          </div>
          <div className="page-head-actions">
            {/* Photo de groupe, promotion et membres de la page d'accueil. */}
            <a className="p-btn p-btn-ghost" href="/admin/api/team/">
              <GroupsIcon/>
              Équipe du site
            </a>
            <button type="button" className="p-btn p-btn-primary" onClick={openModal}>
              <AddCircleOutlineIcon/>
              Nouvelle galerie
            </button>
          </div>
        </div>
        <div className="gallery-grid-plain">
          <Container fluid>
            <Row className="g-2 g-sm-3 g-lg-4">
                {galleriesComp}
            </Row>
          </Container>
        </div>
        {addModalState && (
          <div className='pic-modal'>
            <div ref={ref} className='add-modal-content'>
              <span className='close-white-modal' onClick={closeModal}>&times;</span>
              <h2 className="add-modal-title">Nouvelle galerie</h2>
              <form ref={ref2} onSubmit={onSubmit}>
                <label className="add-modal-field">
                  <span className="add-modal-label">Nom</span>
                  <TextField value={name} type="text" size="small" onChange={e =>  setName(e.target.value)} fullWidth/>
                </label>
                <label className="add-modal-field">
                  <span className="add-modal-label">Description</span>
                  <TextField value={description} type="text" size="small" onChange={e =>  setDescription(e.target.value)} fullWidth/>
                </label>
                <div className="add-modal-field">
                  <span className="add-modal-label">Visibilité</span>
                  <Select value={visibility} size="small" onChange={e => setVisibility(e.target.value)} fullWidth >
                    <MenuItem value={'privée'}>Privée</MenuItem>
                    <MenuItem value={'école'}>École</MenuItem>
                    <MenuItem value={'publique'}>Publique</MenuItem>
                  </Select>
                </div>
                <div className="add-modal-field">
                  <span className="add-modal-label">Contenu</span>
                  <Select value={type} size="small" onChange={e => setType(e.target.value)} fullWidth >
                    <MenuItem value={'photo'}>Photo</MenuItem>
                    <MenuItem value={'video'}>Vidéo</MenuItem>
                  </Select>
                </div>
                <div className="add-modal-field">
                  <span className="add-modal-label">Rangée parmi les</span>
                  <Select value={view} size="small" onChange={e => setView(e.target.value)} fullWidth >
                    <MenuItem value={'galerie'}>Galeries</MenuItem>
                    <MenuItem value={'exposition'}>Expositions</MenuItem>
                  </Select>
                </div>
                <p className="add-modal-error">{error}</p>
                <div className="add-modal-actions">
                  <button type="button" className="p-btn p-btn-primary" onClick={onSubmit}>Créer</button>
                </div>
              </form>
            </div>
          </div>
          )
        }
      </>
    )
}
