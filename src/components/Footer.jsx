import React from 'react';

const Footer = () => {
    return (
        <footer className="bg-black text-white py-12 border-t border-white/10">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <div>
                        <h3 className="text-xl font-bold mb-4 tracking-widest">EDO SUSHI BAR</h3>
                        <p className="text-gray-400 text-sm">
                            La mejor experiencia de sushi en Lima.
                        </p>
                    </div>
                    <div>
                        <h3 className="text-lg font-bold mb-4 uppercase tracking-wider text-primary">Enlaces</h3>
                        <ul className="space-y-2 text-gray-400 text-sm">
                            <li><a href="#" className="hover:text-white transition-colors">Inicio</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Carta</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Locales</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Nosotros</a></li>
                        </ul>
                    </div>
                    <div>
                        <h3 className="text-lg font-bold mb-4 uppercase tracking-wider text-primary">Contacto</h3>
                        <ul className="space-y-2 text-gray-400 text-sm">
                            <li>info@edosushibar.com</li>
                            <li>Lima, Perú</li>
                        </ul>
                        <div className="flex space-x-4 mt-4">
                            {/* Social Icons placeholders */}
                            <div className="w-8 h-8 bg-gray-800 rounded-full hover:bg-primary transition-colors cursor-pointer"></div>
                            <div className="w-8 h-8 bg-gray-800 rounded-full hover:bg-primary transition-colors cursor-pointer"></div>
                            <div className="w-8 h-8 bg-gray-800 rounded-full hover:bg-primary transition-colors cursor-pointer"></div>
                        </div>
                    </div>
                </div>
                <div className="mt-8 pt-8 border-t border-gray-800 text-center text-gray-500 text-xs">
                    &copy; {new Date().getFullYear()} Edo Sushi Bar Clone. Todos los derechos reservados.
                </div>
            </div>
        </footer>
    );
};

export default Footer;
