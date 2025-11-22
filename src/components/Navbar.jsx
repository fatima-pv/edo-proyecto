import React, { useState } from 'react';

const Navbar = () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <nav className="bg-black/90 text-white fixed w-full z-50 top-0 left-0 border-b border-white/10 backdrop-blur-sm">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-20">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <span className="text-2xl font-bold tracking-widest">EDO</span>
                        </div>
                        <div className="hidden md:block">
                            <div className="ml-10 flex items-baseline space-x-8">
                                <a href="#" className="hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors duration-300">INICIO</a>
                                <a href="#" className="hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors duration-300">CARTA</a>
                                <a href="#" className="hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors duration-300">LOCALES</a>
                                <a href="#" className="hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors duration-300">ZONAS DE REPARTO</a>
                                <a href="#" className="hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors duration-300">NOSOTROS</a>
                            </div>
                        </div>
                    </div>
                    <div className="hidden md:block">
                        <button className="bg-primary hover:bg-orange-600 text-white px-6 py-2 rounded-full font-bold transition-colors duration-300 uppercase text-sm tracking-wider">
                            Pide Online
                        </button>
                    </div>
                    <div className="-mr-2 flex md:hidden">
                        <button
                            onClick={() => setIsOpen(!isOpen)}
                            type="button"
                            className="bg-gray-900 inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-800 focus:outline-none"
                            aria-controls="mobile-menu"
                            aria-expanded="false"
                        >
                            <span className="sr-only">Open main menu</span>
                            {!isOpen ? (
                                <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                                </svg>
                            ) : (
                                <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {isOpen && (
                <div className="md:hidden" id="mobile-menu">
                    <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-black">
                        <a href="#" className="hover:text-primary block px-3 py-2 rounded-md text-base font-medium">INICIO</a>
                        <a href="#" className="hover:text-primary block px-3 py-2 rounded-md text-base font-medium">CARTA</a>
                        <a href="#" className="hover:text-primary block px-3 py-2 rounded-md text-base font-medium">LOCALES</a>
                        <a href="#" className="hover:text-primary block px-3 py-2 rounded-md text-base font-medium">ZONAS DE REPARTO</a>
                        <a href="#" className="hover:text-primary block px-3 py-2 rounded-md text-base font-medium">NOSOTROS</a>
                        <button className="w-full text-left bg-primary hover:bg-orange-600 text-white px-3 py-2 rounded-md font-bold transition-colors duration-300 uppercase text-base tracking-wider mt-4">
                            Pide Online
                        </button>
                    </div>
                </div>
            )}
        </nav>
    );
};

export default Navbar;
