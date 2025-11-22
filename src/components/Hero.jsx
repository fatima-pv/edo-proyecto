import React from 'react';

const Hero = () => {
    return (
        <div className="relative h-[80vh] w-full bg-gray-900 overflow-hidden">
            {/* Background Image Placeholder */}
            <div className="absolute inset-0 bg-gradient-to-r from-black/80 to-black/40 z-10"></div>
            <div
                className="absolute inset-0 bg-cover bg-center opacity-60"
                style={{
                    backgroundImage: "url('https://images.unsplash.com/photo-1579871494447-9811cf80d66c?q=80&w=2070&auto=format&fit=crop')"
                }}
            ></div>

            <div className="relative z-20 h-full flex flex-col justify-center items-start max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
                    EXPERIENCIA <br />
                    <span className="text-primary">EDO</span>
                </h1>
                <p className="text-xl md:text-2xl text-gray-200 mb-8 max-w-2xl">
                    Disfruta de la mejor fusión nikkei en la comodidad de tu hogar o en nuestros locales.
                </p>
                <button className="bg-primary hover:bg-orange-600 text-white px-8 py-4 rounded-full font-bold transition-all duration-300 uppercase text-lg tracking-widest shadow-lg hover:shadow-orange-500/30 transform hover:-translate-y-1">
                    Pide Online
                </button>
            </div>
        </div>
    );
};

export default Hero;
