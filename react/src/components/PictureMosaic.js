import React, { useEffect, useState, useRef} from 'react';
import './../App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import GallerySticker from './GallerySticker'
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import DownloadIcon from '@mui/icons-material/Download';
import FlagIcon from '@mui/icons-material/Flag';
import Cookies from 'js-cookie';
import ReportDialog from './ReportDialog';

const PictureMosaic = (props) => {

    const [state, setState] = useState(false);
    //Current loaded picture in modal
    const [current, setCurrent] = useState(null);
    // Derived from the props at each render: kept in state, every picture was
    // rebuilt each time one was ticked.
    const files = Object.values(props.result || {});
    const pics = files.map(file => file.link + '/uploads/' + file.file_full_name);
    // Report dialog open state
    const [reportOpen, setReportOpen] = useState(false);

    //Open image in full screen when vignette is clicked
    const toggleModal = (e, img) => {
        setCurrent(img)
        setState(true)
    };

    //Close image modal
    const closeModal = () => {
        setState(false)
    };

    //Goto next picture in modal
    const nextPicture = () => {
        console.log(pics)
        let nextId = pics.indexOf(current) + 1;
        if (nextId == pics.length) nextId = 0
        setCurrent(pics[nextId]);
    };

    //Goto previous picture in modal
    const previousPicture = () => {
        let nextId = pics.indexOf(current) - 1;
        if (nextId == -1) nextId = pics.length - 1
        setCurrent(pics[nextId]);
    };

    // Send a report for the picture currently displayed
    const reportCurrent = (category, message) => {
        const array = current.split('/');
        const reportOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': Cookies.get('csrftoken') },
            body: JSON.stringify({
                slug: gallery_slug,
                file_full_name: array[array.length - 1],
                category: category,
                message: message,
            })
        };
        fetch('/api/gallery/pics/report/', reportOptions)
            .then(res => res.json())
            .then(
                (result) => {
                    if (result.status === 'error') {
                        alert(result.message)
                    } else {
                        alert('Merci, votre signalement a été transmis.')
                    }
                },
                (error) => {
                    alert("Impossible d'envoyer le signalement, réessayez plus tard.")
                }
            );
    };

    // Swipe detection
    const [touchStart, setTouchStart] = useState(null)
    const [touchEnd, setTouchEnd] = useState(null)

    // the required distance between touchStart and touchEnd to be detected as a swipe
    const minSwipeDistance = 50

    const onTouchStart = (e) => {
        setTouchEnd(null) // otherwise the swipe is fired even with usual touch events
        setTouchStart(e.targetTouches[0].clientX)
    }

    const onTouchMove = (e) => setTouchEnd(e.targetTouches[0].clientX)

    const onTouchEnd = () => {
        if (!touchStart || !touchEnd) return
        const distance = touchStart - touchEnd
        const isLeftSwipe = distance > minSwipeDistance
        const isRightSwipe = distance < -minSwipeDistance
        if (isLeftSwipe){
        nextPicture()
        } else if (isRightSwipe){
        previousPicture()
        }
    }

    useEffect(() => {
        const handleClickOutside = (event) => {
          if (ref.current && !ref.current.contains(event.target)
            && ref2.current && !ref2.current.contains(event.target)
            && ref3.current && !ref3.current.contains(event.target)
            && ref4.current && !ref4.current.contains(event.target)
            && (ref5.current ? !ref5.current.contains(event.target) : true)
            && !(event.target.closest && event.target.closest('.modal, .modal-backdrop'))) {
            closeModal()
          }
        };
        document.addEventListener('click', handleClickOutside, true);
        return () => {
          document.removeEventListener('click', handleClickOutside, true);
        };
      },[]);

    useEffect(() => {
        const handleKeyDown = (event) => {
            // Ignore keyboard shortcuts while the report dialog is open
            if (reportOpen || (event.target.closest && event.target.closest('.modal'))) return
            if (event.key === 'ArrowRight') {
                nextPicture()
            } else if (event.key === 'ArrowLeft') {
                previousPicture()
            } else if (event.key === 'Escape') {
                closeModal()
            }
        }
        document.addEventListener('keydown', handleKeyDown, true);
        return () => {
            document.removeEventListener('keydown', handleKeyDown, true);
        };
    }, [current, reportOpen]);

    const ref = useRef(null);
    const ref2 = useRef(null);
    const ref3 = useRef(null)
    const ref4 = useRef(null)
    const ref5 = useRef(null)

    return (
        <>
            <Container fluid>
                <Row className='g-1'>
                    {files.map((file, index) => (
                        <Col key={index} xs="4" sm="3" lg="2">
                            <GallerySticker img={file.link + '/uploads/' + file.file_full_name}
                                thumb={file.link + '/thumbnails/' + file.file_full_name}
                                modal_func={toggleModal}
                                selectionMode={props.selectionMode}
                                selected={props.selected && props.selected.has(file.file_full_name)}
                                onToggleSelect={props.onToggleSelect}
                                fileFullName={file.file_full_name} />
                        </Col>
                    ))}
                </Row>
            </Container>
            {state && (
                <div className='pic-modal'>
                    <ArrowBackIcon ref={ref2} onClick={previousPicture} className='arrow left-arrow' />
                    <ArrowForwardIcon ref={ref3} onClick={nextPicture} className='arrow right-arrow' />
                    <div className="pic-modal-nav">
                        <span className='close' onClick={closeModal}>&times;</span>
                        <a href={current} download={current}><span ref={ref4}><DownloadIcon className="download" /></span></a>
                        {is_authenticated && (
                            <span ref={ref5}><FlagIcon className="download report-flag" onClick={() => setReportOpen(true)} /></span>
                        )}
                    </div>
                    <div className='pic-modal-content' onTouchStart={onTouchStart} onTouchMove={onTouchMove} onTouchEnd={onTouchEnd}>
                        <div ref={ref} className="img-browser">
                            <img src={current} className='img-modal' />
                        </div>
                    </div>
                    <ReportDialog
                        open={reportOpen}
                        onClose={() => setReportOpen(false)}
                        onSubmit={reportCurrent}
                    />
                </div>
            )
            }
        </>
    );
};

export default PictureMosaic;
