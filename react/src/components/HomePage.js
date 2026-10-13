import React from 'react'
import CustomNavbar from './Navbar'
import Footer from './Footer'
import KeyboardDoubleArrowDownIcon from '@mui/icons-material/KeyboardDoubleArrowDown';
import './../App.css';

// "Maxime Novo-Frelicot" -> "MN": first and last word, as on a name tag.
const initials = (name) => {
    const words = name.trim().split(/\s+/);
    const last = words.length > 1 ? words[words.length - 1] : '';
    return (words[0].charAt(0) + last.charAt(0)).toUpperCase();
};

// A role held by one person is a card with that person; a role shared by
// several (photographers, video makers) is a list of names under its title.
function TeamSection({team}) {
    return (
        <section className="team-section" id="team">
            <div className="team-section-inner">
                <p className="team-section-eyebrow">Ponthé {team.name}</p>
                <h2 className="team-section-title">L'équipe</h2>
                {team.sections.map(section => {
                    const alone = section.roles.filter(role => role.people.length === 1);
                    const crews = section.roles.filter(role => role.people.length > 1);
                    return (
                        <div className="team-group" key={section.title}>
                            <h3 className="team-group-title">{section.title}</h3>
                            {alone.length > 0 && (
                                <ul className="team-people">
                                    {alone.map(role => (
                                        <li className="team-person" key={role.title + role.people[0]}>
                                            <span className="team-avatar" aria-hidden="true">{initials(role.people[0])}</span>
                                            <span className="team-person-text">
                                                <span className="team-person-name">{role.people[0]}</span>
                                                <span className="team-person-role">{role.title}</span>
                                            </span>
                                        </li>
                                    ))}
                                </ul>
                            )}
                            {crews.length > 0 && (
                                <div className="team-crews">
                                    {crews.map(role => (
                                        <div className="team-crew" key={role.title}>
                                            <h4 className="team-crew-title">
                                                {role.title}
                                                <span className="team-crew-count">{role.people.length}</span>
                                            </h4>
                                            <ul className="team-chips">
                                                {role.people.map(name => <li key={name}>{name}</li>)}
                                            </ul>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })}
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
            <Footer/>
        </>
    )
}
