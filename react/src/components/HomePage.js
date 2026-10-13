import React from 'react'
import CustomNavbar from './Navbar'
import Footer from './Footer'
import KeyboardDoubleArrowDownIcon from '@mui/icons-material/KeyboardDoubleArrowDown';
import './../App.css';

// The team of a photo and video club, set as the end credits of a film: a
// role on one side of an axis, whoever holds it on the other, a heading over
// each department. A role shared by several lists them one under the other.
function TeamSection({team}) {
    return (
        <section className="team-section" id="team">
            <div className="team-section-inner">
                <h2 className="team-section-title">L'équipe <span>{team.name}</span></h2>
                {team.sections.map(section => (
                    <div className="credits-group" key={section.title}>
                        <h3 className="credits-group-title">{section.title}</h3>
                        <dl className="credits-list">
                            {section.roles.filter(role => role.people.length > 0).map(role => (
                                <div className="credits-line" key={role.title + role.people[0]}>
                                    <dt>{role.title}</dt>
                                    <dd>
                                        {role.people.map(name => <span key={name}>{name}</span>)}
                                    </dd>
                                </div>
                            ))}
                        </dl>
                    </div>
                ))}
            </div>
        </section>
    );
}

// `team` is what the admin holds for the team on display: its promotion, its
// picture and its members. Nothing here names a year or a person.
export default function HomePage ({team}){
    const photo = team && team.photo;

    return (
        <>
            <CustomNavbar/>
            <main>
                {/* The picture is an element, not a background: on a wide
                    screen it fills the section behind the text, on a phone
                    it sits above it, whole. The stylesheet does the rest. */}
                <section className={'hero-section' + (photo ? '' : ' hero-plain')}>
                    {photo && <img className="hero-photo" src={photo} alt={"L'équipe du Ponthé " + team.name}/>}
                    <div className="hero-content">
                        {team && (
                            <p className="hero-eyebrow">
                                Équipe <span className="badge-hero-yellow">{team.name}</span>
                            </p>
                        )}
                        <h1 className="poster-title">Ponthé</h1>
                        <p className="hero-subtitle">Club photo &amp; vidéo de l'École des Ponts</p>
                        <div className="hero-pills">
                            <a className="pill-btn pill-yellow" href="/galleries">Accéder aux galeries</a>
                            <a className="pill-btn pill-white" href="https://www.youtube.com/@ponthe-ecoledesponts7542">Chaîne Youtube</a>
                        </div>
                        {team && (
                            <a className="scroll-chevron" href="#team" aria-label="Voir l'équipe">
                                <KeyboardDoubleArrowDownIcon/>
                            </a>
                        )}
                    </div>
                </section>

                {team && <TeamSection team={team}/>}
            </main>
            <Footer dark={Boolean(team)}/>
        </>
    )
}
