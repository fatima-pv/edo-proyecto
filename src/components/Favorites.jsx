import React from 'react';

const products = [
    {
        id: 1,
        name: 'ACEVICHADO',
        price: 'S/ 39.00',
        image: 'https://images.unsplash.com/photo-1558985250-27a406d64cb3?q=80&w=2070&auto=format&fit=crop',
        description: 'Langostino empanizado y palta. Cubierto con láminas de atún y salsa acevichada.'
    },
    {
        id: 2,
        name: 'PARRILLERO',
        price: 'S/ 35.00',
        image: 'https://images.unsplash.com/photo-1617196034496-64ac7960f271?q=80&w=2070&auto=format&fit=crop',
        description: 'Langostino furai y queso crema. Cubierto con carne flambeada y salsa parrillera.'
    },
    {
        id: 3,
        name: 'EDO MAKI',
        price: 'S/ 32.00',
        image: 'https://images.unsplash.com/photo-1611143669185-af224c5e3252?q=80&w=1932&auto=format&fit=crop',
        description: 'Salmón, queso crema y palta. Envuelto en ajonjolí negro.'
    },
    {
        id: 4,
        name: 'RAMEN EDO',
        price: 'S/ 42.00',
        image: 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?q=80&w=2070&auto=format&fit=crop',
        description: 'Fideos artesanales, caldo de cerdo, chashu, huevo y verduras.'
    }
];

const Favorites = () => {
    return (
        <section className="py-20 bg-dark">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                    <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 tracking-widest uppercase">
                        Nuestros <span className="text-primary">Favoritos</span>
                    </h2>
                    <div className="w-24 h-1 bg-primary mx-auto"></div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                    {products.map((product) => (
                        <div key={product.id} className="bg-gray-900 rounded-lg overflow-hidden shadow-lg hover:shadow-primary/20 transition-all duration-300 group">
                            <div className="relative h-64 overflow-hidden">
                                <img
                                    src={product.image}
                                    alt={product.name}
                                    className="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-500"
                                />
                                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                                    <button className="bg-primary text-white px-6 py-2 rounded-full font-bold uppercase text-sm tracking-wider transform translate-y-4 group-hover:translate-y-0 transition-transform duration-300">
                                        Ver Detalle
                                    </button>
                                </div>
                            </div>
                            <div className="p-6">
                                <h3 className="text-xl font-bold text-white mb-2 tracking-wide">{product.name}</h3>
                                <p className="text-gray-400 text-sm mb-4 line-clamp-2">{product.description}</p>
                                <div className="flex items-center justify-between mt-4">
                                    <span className="text-2xl font-bold text-primary">{product.price}</span>
                                    <button className="border border-white/20 hover:bg-white hover:text-black text-white px-4 py-1 rounded text-sm font-medium transition-colors duration-300 uppercase">
                                        Ordenar
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="text-center mt-12">
                    <button className="border-2 border-primary text-primary hover:bg-primary hover:text-white px-8 py-3 rounded-full font-bold transition-colors duration-300 uppercase tracking-widest">
                        Ver Carta Completa
                    </button>
                </div>
            </div>
        </section>
    );
};

export default Favorites;
