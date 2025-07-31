'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { motion } from 'framer-motion';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import SearchBar from './SearchBar';
import SearchFilters from './SearchFilters';
import SearchResults from './SearchResults';
import WorkCard from './WorkCard';
import useSearch from '../../hooks/useSearch';
import mockData from '../../data/mockWorks.json';

// Simplified cursor hook for search page performance
const useCustomCursor = () => {
  const cursorRef = useRef(null);
  const blurRef = useRef(null);
  
  useEffect(() => {
    const updateMousePosition = (e) => {
      if (cursorRef.current) {
        cursorRef.current.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
      }
      if (blurRef.current) {
        blurRef.current.style.transform = `translate(${e.clientX - 60}px, ${e.clientY - 60}px)`;
      }
    };
    
    // Use passive listener for best performance
    window.addEventListener('mousemove', updateMousePosition, { passive: true });
    
    return () => {
      window.removeEventListener('mousemove', updateMousePosition);
    };
  }, []);

  return { cursorRef, blurRef };
};

export default function SearchPage() {
  const { cursorRef, blurRef } = useCustomCursor();
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
    performSearchWithValues,
    handleFilterChange,
    clearFilters,
    searchWithClearedFilters,
    clearSearch
  } = useSearch(mockData);

  // Clear all search and filters
  const clearAll = () => {
    clearSearch(); // This already clears search query and all filters
  };

  // Generate organized suggestions with sections
  const suggestions = {
    sections: [
      {
        title: "Work Titles",
        icon: "📖",
        items: [...new Set(mockData.works.map(work => work.title))].slice(0, 6)
      },
      {
        title: "Authors",
        icon: "👤", 
        items: [...new Set(mockData.works.map(work => work.author_name))].slice(0, 8)
      },
      {
        title: "Categories",
        icon: "🏷️",
        items: [...new Set(mockData.works.map(work => work.category))]
      }
    ]
  };

  return (
    <div className="grainy-bg min-h-screen overflow-x-hidden relative">
      {/* Custom Cursor & Effects */}
      <div 
        ref={cursorRef}
        className="custom-cursor"
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          pointerEvents: 'none',
          zIndex: 9999,
        }}
      />
      
      <div 
        ref={blurRef}
        className="mouse-blur"
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '120px',
          height: '120px',
          pointerEvents: 'none',
          zIndex: 60,
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
            onClearAll={clearAll}
          />
            
          <SearchFilters 
            categories={mockData.categories}
            countries={mockData.countries}
            statuses={mockData.statuses}
            selectedCategory={selectedCategory}
            selectedCountry={selectedCountry}
            selectedStatus={selectedStatus}
            onFilterChange={handleFilterChange}
            onClearFilters={clearFilters}
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
          setSearchQuery={setSearchQuery}
          performSearch={performSearch}
          performSearchWithValues={performSearchWithValues}
          searchWithClearedFilters={searchWithClearedFilters}
          selectedCategory={selectedCategory}
          selectedCountry={selectedCountry}
          selectedStatus={selectedStatus}
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