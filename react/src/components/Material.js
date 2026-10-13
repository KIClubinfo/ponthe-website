import React from 'react'
import CustomNavbar from './Navbar'
import Footer from './Footer'
import './../App.css';

export default function Material (){

    return (
        <>
            <CustomNavbar/>
            <div className="page-header">
                <h1 className="page-header-title">Matériel</h1>
            </div>
            <Footer/>
        </>
    )
}
