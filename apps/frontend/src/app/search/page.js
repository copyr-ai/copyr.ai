'use client';

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import SearchBar from '../components/search/SearchBar';
import SearchFilters from '../components/search/SearchFilters';
import SearchResults from '../components/search/SearchResults';
import WorkCard from '../components/search/WorkCard';
import useSearch from '../../hooks/useSearch';
import mockData from '../../data/mockWorks.json';

// Custom cursor hook with performance optimization
const useCustomCursor = () => {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);
  const [isOverFooter, setIsOverFooter] = useState(false);
  const rafRef = useRef(null);
  const lastUpdate = useRef(0);

  useEffect(() => {
    const updateMousePosition = (e) => {
      // Throttle updates using requestAnimationFrame
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      
      rafRef.current = requestAnimationFrame(() => {
        const now = Date.now();
        // Limit updates to 60fps max
        if (now - lastUpdate.current > 16) {
          setMousePosition({ x: e.clientX, y: e.clientY });
          
          // Check footer less frequently to improve performance
          if (now - lastUpdate.current > 50) {
            const footerElement = document.querySelector('footer');
            if (footerElement) {
              const footerRect = footerElement.getBoundingClientRect();
              const isInFooter = e.clientY >= footerRect.top && 
                                e.clientY <= footerRect.bottom &&
                                e.clientX >= footerRect.left && 
                                e.clientX <= footerRect.right;
              setIsOverFooter(isInFooter);
            }
          }
          lastUpdate.current = now;
        }
      });
    };
    
    const handleMouseEnter = () => setIsHovering(true);
    const handleMouseLeave = () => setIsHovering(false);
    
    // Use passive listeners for better performance
    window.addEventListener('mousemove', updateMousePosition, { passive: true });
    
    const interactiveElements = document.querySelectorAll('button, a, [role="button"]');
    interactiveElements.forEach(el => {
      el.addEventListener('mouseenter', handleMouseEnter, { passive: true });
      el.addEventListener('mouseleave', handleMouseLeave, { passive: true });
    });
    
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      window.removeEventListener('mousemove', updateMousePosition);
      interactiveElements.forEach(el => {
        el.removeEventListener('mouseenter', handleMouseEnter);
        el.removeEventListener('mouseleave', handleMouseLeave);
      });
    };
  }, []);

  return { mousePosition, isHovering, isOverFooter };
};

export default function SearchPage() {
  const { mousePosition, isHovering, isOverFooter } = useCustomCursor();
  const {
    searchQuery,
    selectedCategory,
    selectedCountry,
    selectedStatus,
    searchResults,
    isLoading,
    hasSearched,
    setSearchQuery,
    performSearch,
    handleFilterChange,
    clearSearch
  } = useSearch(mockData);

  // Generate suggestions from work titles and authors
  const suggestions = [
    ...mockData.works.map(work => work.title),
    ...mockData.works.map(work => work.author_name),
    ...Array.from(new Set(mockData.works.map(work => work.category))),
    // Add some common search terms
    'American Gothic', 'Shakespeare', 'Mozart', 'Van Gogh', 'Beethoven',
    'Pride and Prejudice', 'The Starry Night', 'Swan Lake', 'The Godfather'
  ].filter((item, index, arr) => arr.indexOf(item) === index); // Remove duplicates

  return (
    <div className="grainy-bg min-h-screen overflow-x-hidden relative">
      {/* Custom Cursor & Effects */}
      <div 
        className={`custom-cursor ${isHovering ? 'hover' : ''} ${isOverFooter ? 'footer' : ''}`}
        style={{
          left: mousePosition.x,
          top: mousePosition.y,
        }}
      />
      
      <div 
        className="mouse-blur"
        style={{
          left: mousePosition.x - 100,
          top: mousePosition.y - 100,
          width: '200px',
          height: '200px',
        }}
      />

      <Navbar />

      {/* Header Section */}
      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="pt-32 pb-20 px-4 max-w-7xl mx-auto"
      >
        <div className="max-w-4xl mx-auto text-center">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-4xl md:text-5xl lg:text-6xl font-bold text-brand-dark mb-6"
          >
            <span className="gradient-text-copyright">Copyright</span>{" "}
            <span className="gradient-text-clarity">Search</span>
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-xl md:text-2xl text-gray-600 leading-relaxed max-w-3xl mx-auto mb-12"
          >
            Search our comprehensive database to determine the copyright status of creative works.
          </motion.p>
            
          <SearchBar 
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            onSearch={performSearch}
            isLoading={isLoading}
            suggestions={suggestions}
          />
            
          <SearchFilters 
            categories={mockData.categories}
            countries={mockData.countries}
            statuses={mockData.statuses}
            selectedCategory={selectedCategory}
            selectedCountry={selectedCountry}
            selectedStatus={selectedStatus}
            onFilterChange={handleFilterChange}
          />
        </div>
      </motion.div>

      {/* Recently Analyzed Works - Only when not searching */}
      {!hasSearched && (
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 1.0 }}
          className="px-4 max-w-7xl mx-auto mb-20"
        >
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-brand-dark mb-4">Recently Analyzed Works</h2>
            <p className="text-gray-600">Explore some of the latest copyright analyses from our database</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {mockData.works.slice(0, 6).map((work, index) => (
              <WorkCard 
                key={work.id} 
                work={work} 
                variant="preview" 
                index={index} 
              />
            ))}
          </div>
        </motion.div>
      )}

      {/* Search Results Section */}
      <div data-search-results>
        <SearchResults 
          searchResults={searchResults}
          isLoading={isLoading}
          hasSearched={hasSearched}
          searchQuery={searchQuery}
          onClearSearch={clearSearch}
        />
      </div>

      {/* Browse More Section - Only when searching */}
      {hasSearched && (
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="px-4 max-w-7xl mx-auto mb-20"
        >
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-brand-dark mb-4">Browse More Works</h2>
            <p className="text-gray-600">Discover other works in our copyright database</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {mockData.works.slice(0, 6).map((work, index) => (
              <WorkCard 
                key={`browse-${work.id}`} 
                work={work} 
                variant="preview" 
                index={index} 
              />
            ))}
          </div>
        </motion.div>
      )}

      {/* Database Showcase - Only when not searching */}
      {!hasSearched && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 1.8 }}
          className="px-4 max-w-7xl mx-auto mb-20 space-y-16"
        >
          {/* Database Introduction */}
          <div className="text-center">
            <motion.h2 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 2.0 }}
              className="text-3xl md:text-4xl font-bold text-brand-dark mb-4"
            >
              Explore Our <span className="gradient-text-primary">Database</span>
            </motion.h2>
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 2.2 }}
              className="text-xl text-gray-600 max-w-2xl mx-auto mb-8"
            >
              Browse through thousands of analyzed works across literature, music, film, and art.
            </motion.p>
          </div>

          {/* Database Statistics */}
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 2.4 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-6"
          >
            {[
              { number: "12,547", label: "Literary Works" },
              { number: "8,329", label: "Musical Compositions" },
              { number: "3,142", label: "Films & Videos" },
              { number: "5,891", label: "Artworks" }
            ].map((stat, index) => (
              <motion.div 
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 2.6 + index * 0.1 }}
                className="bg-white/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-200 text-center hover:shadow-lg transition-all duration-300 hover:-translate-y-1"
              >
                <div className="text-3xl font-bold gradient-text-primary mb-2">{stat.number}</div>
                <div className="text-sm text-gray-600">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      )}

      <Footer />
    </div>
  );
}