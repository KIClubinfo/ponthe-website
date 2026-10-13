import React from 'react'
import CustomNavbar from './Navbar'
import Footer from './Footer'
import KeyboardDoubleArrowDownIcon from '@mui/icons-material/KeyboardDoubleArrowDown';
import './../App.css';

export default function HomePage (){

    return (
        <>
            <CustomNavbar/>
            <main>
                {/* The picture is an element, not a background: on a wide
                    screen it fills the section behind the text, on a phone
                    it sits above it, whole. The stylesheet does the rest. */}
                <section className="hero-section">
                    <img className="hero-photo" src="/static/assets/img/028_group.jpg" alt="L'équipe du Ponthé 028"/>
                    <div className="hero-content">
                        <p className="hero-eyebrow">
                            Équipe <span className="badge-hero-yellow">028</span>
                        </p>
                        <h1 className="poster-title">Ponthé</h1>
                        <p className="hero-subtitle">Club photo &amp; vidéo de l'École des Ponts</p>
                        <div className="hero-pills">
                            <a className="pill-btn pill-yellow" href="/galleries">Accéder aux galeries</a>
                            <a className="pill-btn pill-white" href="https://www.youtube.com/@ponthe-ecoledesponts7542">Chaîne Youtube</a>
                        </div>
                        <a className="scroll-chevron" href="#team" aria-label="Voir l'équipe">
                            <KeyboardDoubleArrowDownIcon/>
                        </a>
                    </div>
                </section>

                <section className="team-section" id="team">
                    <div className="team-section-inner">
                        <h2 className="team-section-title">L'équipe</h2>
                        <div className="roster-grid">
                            <div className="roster-column">
                                <h3 className="roster-group-title">Le Bureau</h3>
                                <div className="roster-card-item">
                                    <p><strong>Présidente :</strong> Alice Dubreux</p>
                                    <p><strong>V-Prez Photo :</strong> Romain Soulabail</p>
                                    <p><strong>V-Prez Vidéo :</strong> Louis Cussoneau</p>
                                    <p><strong>Trez :</strong> Émilie Duccini</p>
                                </div>
                                <h3 className="roster-group-title">Responsables</h3>
                                <div className="roster-card-item">
                                    <p><strong>Respo Matos :</strong> Paul Lemeunier</p>
                                    <p><strong>Respo Galeries :</strong> Maxime Novo-Frelicot</p>
                                    <p><strong>Respo Comm :</strong> Vincent Huynh</p>
                                </div>
                            </div>
                            <div className="roster-column">
                                <h3 className="roster-group-title">Pôle Création</h3>
                                <div className="roster-card-item">
                                    <p className="roster-subtitle">Vidéastes</p>
                                    <p className="roster-names">Océane Chia, Louis Laverrière, Clovis Vialard, Sophie Balmitgère</p>
                                    <p className="roster-subtitle">Photographes</p>
                                    <p className="roster-names">Maxime Préel, Pétronille Sylvestre, Juliette Houriez, Mathilde David, Sélène Baudoux, Saül Buchwald, Lucie Agnese, Maxence Brechon</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </main>
            <Footer/>
        </>
    )
}
