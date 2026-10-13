import React from 'react';
import './../App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import Cookies from 'js-cookie';

export default function Login() {

    const cookie = Cookies.get('csrftoken')

    return (
        <main className="login-page">
            <div className="login-container">
                <a href="/"><img className="login-logo" src="/static/assets/img/logo-ponthe.png" alt="Ponthé"/></a>
                <h1 className="login-title">Connexion</h1>
                <p className="login-lead">Les galeries de l'École sont réservées à ses élèves.</p>
                <a href="/accounts/login" className="login-button">Se connecter avec le SSO de l'École</a>
                <div className="login-separator">ou avec un compte Ponthé</div>
                <form className="login-form" method="post" action="/login/">
                    <input type="hidden" name="csrfmiddlewaretoken" value={cookie} />
                    <input type="email" className="login-input" placeholder="prenom.nom@eleves.enpc.fr" name="username"
                        aria-label="Adresse e-mail" autoComplete="username" required/>
                    <input type="password" className="login-input" placeholder="Mot de passe" name="password"
                        aria-label="Mot de passe" autoComplete="current-password" required/>
                    {error && <p className="login-error" role="alert">Mauvais identifiants</p>}
                    <button type="submit" className="login-button login-button-quiet">Se connecter</button>
                </form>
                <a href="/" className="login-link">Retour à l'accueil</a>
            </div>
        </main>
    )

}
