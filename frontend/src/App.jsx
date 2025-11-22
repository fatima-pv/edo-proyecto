import React from 'react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Hero from './components/Hero';
import Favorites from './components/Favorites';

function App() {
  return (
    <div className="min-h-screen bg-dark text-light font-sans flex flex-col">
      <Navbar />
      <main className="flex-grow">
        <Hero />
        <Favorites />
      </main>
      <Footer />
    </div>
  );
}

export default App;
