'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import SearchBar from './SearchBar';
import SearchFilters from './SearchFilters';
import SearchResults from './SearchResults';
import WorkCard from './WorkCard';
import useSearchWithAPI from '../../hooks/useSearchWithAPI';
import mockData from '../../data/mockWorks.json';
import { apiClient } from '../../lib/api';
import SearchHistorySidebar from '../components/SearchHistorySidebar';
import { useWork } from '@/contexts/WorkContext';

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
  const { addToSearchHistory, storeWork, searchHistory, storeSearchResults, getCurrentSearchResults } = useWork();
  const router = useRouter();
  const [popularWorks, setPopularWorks] = useState([]);
  const [popularWorksLoading, setPopularWorksLoading] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  
  const {
    searchQuery,
    selectedCategory,
    selectedCountry,
    selectedStatus,
    searchResults,
    isLoading,
    hasSearched,
    error,
    setSearchQuery,
    setSearchResults,
    setHasSearched,
    performSearch,
    performSearchWithValues,
    handleFilterChange,
    clearFilters,
    searchWithClearedFilters,
    clearSearch
  } = useSearchWithAPI();

  // Store search results in work context when they change
  useEffect(() => {
    if (searchResults && searchResults.length > 0 && hasSearched) {
      // Store both individual works and complete search results
      addToSearchHistory(searchResults);
      storeSearchResults(searchResults);
    }
  }, [searchResults, addToSearchHistory, storeSearchResults, hasSearched]);

  // Auto-scroll to search animation when search starts
  useEffect(() => {
    if (hasSearched && isLoading) {
      // Small delay to ensure the animation element is rendered
      const timer = setTimeout(() => {
        const animationElement = document.getElementById('search-progress-animation');
        if (animationElement) {
          animationElement.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
          });
        }
      }, 100); // 100ms delay to ensure DOM is updated

      return () => clearTimeout(timer);
    }
  }, [hasSearched, isLoading]);

  // Note: Page refresh and back navigation caching is now handled in useSearchWithAPI hook

  // Fetch popular works from database with caching
  useEffect(() => {
    const fetchPopularWorks = async () => {
      try {
        setPopularWorksLoading(true);
        
        // Check cache first (10 minute cache)
        const cacheKey = 'copyr-popular-works';
        const cacheExpiry = 10 * 60 * 1000; // 10 minutes in milliseconds
        const cached = localStorage.getItem(cacheKey);
        
        if (cached) {
          try {
            const { data, timestamp } = JSON.parse(cached);
            const isExpired = Date.now() - timestamp > cacheExpiry;
            
            if (!isExpired && data?.works) {
              setPopularWorks(data.works);
              setPopularWorksLoading(false);
              return; // Use cached data
            }
          } catch (e) {
            // Invalid cache, continue to fetch
          }
        }
        
        // Fetch fresh data
        const response = await apiClient.getPopularWorks(6);
        if (response?.works) {
          setPopularWorks(response.works);
          
          // Cache the response
          try {
            localStorage.setItem(cacheKey, JSON.stringify({
              data: response,
              timestamp: Date.now()
            }));
          } catch (e) {
            // Storage full or disabled, continue without caching
          }
        }
      } catch (error) {
        console.error('Failed to fetch popular works:', error);
        // Fallback to mock data if API fails
        setPopularWorks(mockData.works.slice(0, 6));
      } finally {
        setPopularWorksLoading(false);
      }
    };

    fetchPopularWorks();
  }, []);

  // Clear all search and filters
  const clearAll = () => {
    clearSearch(); // This already clears search query and all filters
  };

  // State for autocomplete suggestions
  const [suggestions, setSuggestions] = useState({ sections: [] });
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);

  // Debounced autocomplete suggestions
  useEffect(() => {
    if (!searchQuery || searchQuery.length < 2) {
      setSuggestions({ sections: [] });
      return;
    }

    setIsLoadingSuggestions(true);
    
    // Debounce API calls - wait 250ms (1/4 second) after user stops typing
    const timeoutId = setTimeout(async () => {
      try {
        const suggestionData = await apiClient.getAutocompleteSuggestions(searchQuery, 15);
        setSuggestions(suggestionData);
      } catch (error) {
        console.error('Failed to fetch autocomplete suggestions:', error);
        setSuggestions({ sections: [] });
      } finally {
        setIsLoadingSuggestions(false);
      }
    }, 250);

    return () => {
      clearTimeout(timeoutId);
      setIsLoadingSuggestions(false);
    };
  }, [searchQuery]);

  // Handle sidebar collapse state
  const handleSidebarToggle = (collapsed) => {
    setSidebarCollapsed(collapsed);
  };

  // Handle search history click
  const handleSearchHistoryClick = (historyItem) => {
    console.log('Search history item clicked:', historyItem); // Debug log
    
    // If the history item has cached results, restore them and show the search results
    if (historyItem.results && historyItem.results.length > 0) {
      console.log(`Restoring ${historyItem.results.length} cached results from history`);
      
      // Set the search results directly from history
      setSearchResults(historyItem.results);
      setHasSearched(true);
      
      // Clean the query text from any prefixes before setting
      const cleanQuery = historyItem.query_text?.replace(/^(title:\s*|author:\s*)+/gi, '').trim() || historyItem.query_text;
      
      // Set the search query and filters to match the history
      setSearchQuery(cleanQuery);
      
      // Update the URL to reflect the search parameters
      const params = new URLSearchParams();
      if (cleanQuery && cleanQuery.trim()) {
        params.set('q', cleanQuery);
      }
      if (historyItem.filters?.category && historyItem.filters.category !== 'All') {
        params.set('category', historyItem.filters.category);
      }
      if (historyItem.filters?.country && historyItem.filters.country !== 'All') {
        params.set('country', historyItem.filters.country);
      }
      if (historyItem.filters?.status && historyItem.filters.status !== 'All') {
        params.set('status', historyItem.filters.status);
      }
      
      const newURL = params.toString() ? `/search?${params.toString()}` : '/search';
      router.push(newURL, { scroll: false });
      
      // Store the results in work context for potential work page navigation
      addToSearchHistory(historyItem.results);
      
      return;
    }
    
    // If no cached results, perform the search
    console.log('No cached results, performing search');
    const cleanQueryForSearch = historyItem.query_text?.replace(/^(title:\s*|author:\s*)+/gi, '').trim() || historyItem.query_text;
    performSearchWithValues(
      cleanQueryForSearch,
      historyItem.filters?.category || 'All',
      historyItem.filters?.country || 'All', 
      historyItem.filters?.status || 'All',
      true
    );
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

      {/* Search History Sidebar */}
      <SearchHistorySidebar 
        onSearchHistoryClick={handleSearchHistoryClick} 
        onToggleCollapse={handleSidebarToggle}
        isMobileOpen={isMobileOpen}
        onMobileToggle={setIsMobileOpen}
      />
      
      {/* Main content area */}
      <div 
        className={`min-h-screen overflow-y-auto transition-all duration-300 ${
          sidebarCollapsed ? 'md:ml-12' : 'md:ml-80'
        }`}
      >
        <Navbar sidebarCollapsed={sidebarCollapsed} isMobileSidebarOpen={isMobileOpen} />
        
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
          
          {popularWorksLoading ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, index) => (
                <motion.div
                  key={`skeleton-${index}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 1.2 + index * 0.1 }}
                  className="bg-white/50 backdrop-blur-sm rounded-2xl border border-gray-200 p-6 animate-pulse"
                >
                  <div className="h-6 bg-gray-200 rounded mb-4"></div>
                  <div className="h-4 bg-gray-200 rounded mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {popularWorks.length > 0 ? (
                popularWorks.map((work, index) => (
                  <WorkCard 
                    key={work.id} 
                    work={work} 
                    variant="preview" 
                    index={index} 
                  />
                ))
              ) : (
                <div className="col-span-full text-center py-8">
                  <p className="text-gray-500">No works available in database yet.</p>
                  <p className="text-sm text-gray-400 mt-2">Try searching for some works to populate the database!</p>
                </div>
              )}
            </div>
            )}
          </motion.div>
        )}

        {/* Search Results Section */}
        <div data-search-results>
          {error && (
            <div className="px-4 max-w-7xl mx-auto mb-8">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                <p className="text-red-600">Search error: {error}</p>
                <p className="text-sm text-red-500 mt-2">Please try again or check your connection.</p>
              </div>
            </div>
          )}
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

        {/* Search Progress Animation - Only when searching and loading */}
        {hasSearched && isLoading && (
          <motion.div 
            id="search-progress-animation"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -30 }}
            transition={{ duration: 0.6 }}
            className="px-4 max-w-7xl mx-auto mb-20"
          >
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-8 h-60">
              <div className="flex flex-col items-center justify-center h-full space-y-8">
                
                {/* Thinking Animation */}
                <div className="flex items-center space-x-3">
                  <motion.div
                    animate={{ 
                      scale: [1, 1.3, 1]
                    }}
                    transition={{ 
                      duration: 2, 
                      repeat: Infinity, 
                      ease: "easeInOut"
                    }}
                    className="text-4xl"
                  >
                    🧠
                  </motion.div>
                  
                  <div className="text-center">
                    <h3 className="text-xl font-semibold text-brand-dark mb-1">
                      Analyzing Copyright Status
                    </h3>
                    <motion.div 
                      className="text-gray-600 flex items-center justify-center"
                      initial={{ opacity: 0.6 }}
                    >
                      <span>Thinking</span>
                      <motion.span
                        animate={{ opacity: [0, 1, 0] }}
                        transition={{ 
                          duration: 1.2, 
                          repeat: Infinity,
                          delay: 0
                        }}
                      >
                        .
                      </motion.span>
                      <motion.span
                        animate={{ opacity: [0, 1, 0] }}
                        transition={{ 
                          duration: 1.2, 
                          repeat: Infinity,
                          delay: 0.4
                        }}
                      >
                        .
                      </motion.span>
                      <motion.span
                        animate={{ opacity: [0, 1, 0] }}
                        transition={{ 
                          duration: 1.2, 
                          repeat: Infinity,
                          delay: 0.8
                        }}
                      >
                        .
                      </motion.span>
                    </motion.div>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full max-w-md">
                  <div className="relative h-3 bg-gray-200 rounded-full overflow-hidden">
                    <motion.div
                      className="absolute inset-y-0 left-0 bg-gradient-to-r from-brand-pink via-brand-purple to-blue-500 rounded-full"
                      initial={{ width: "0%" }}
                      animate={{ width: "100%" }}
                      transition={{
                        duration: 12,
                        ease: "easeInOut"
                      }}
                    />
                    
                    {/* Shimmer effect */}
                    <motion.div
                      className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                      animate={{
                        x: ["-100%", "200%"]
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "easeInOut"
                      }}
                      style={{ width: "50%" }}
                    />
                  </div>
                  
                  {/* Changing Step Text */}
                  <motion.div 
                    className="text-center mt-2 text-sm text-gray-500 h-5"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                  >
                    {[
                      "Searching comprehensive database...",
                      "Analyzing copyright metadata...",
                      "Cross-referencing sources...",
                      "Calculating confidence scores...",
                      "Preparing results..."
                    ].map((step, index) => (
                      <motion.span
                        key={index}
                        className="absolute left-1/2 transform -translate-x-1/2"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ 
                          opacity: [0, 1, 1, 0],
                          y: [10, 0, 0, -10]
                        }}
                        transition={{
                          duration: 2.4,
                          delay: index * 2.4,
                          repeat: Infinity,
                          repeatDelay: 9.6, // 4 other steps * 2.4s
                          ease: "easeInOut",
                          times: [0, 0.1, 0.8, 1]
                        }}
                      >
                        {step}
                      </motion.span>
                    ))}
                  </motion.div>
                </div>

                {/* Floating Elements */}
                <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-2xl">
                  {[...Array(3)].map((_, index) => (
                    <motion.div
                      key={index}
                      className="absolute text-2xl opacity-10"
                      initial={{ 
                        x: Math.random() * 400,
                        y: Math.random() * 200,
                        scale: 0
                      }}
                      animate={{
                        y: [
                          Math.random() * 200,
                          Math.random() * 200 + 50,
                          Math.random() * 200
                        ],
                        x: [
                          Math.random() * 400,
                          Math.random() * 400 + 30,
                          Math.random() * 400
                        ],
                        scale: [0, 1, 0],
                        rotate: [0, 180, 360]
                      }}
                      transition={{
                        duration: 4 + index,
                        repeat: Infinity,
                        delay: index * 1.5,
                        ease: "easeInOut"
                      }}
                    >
                      {['©', '📚', '🔍'][index]}
                    </motion.div>
                  ))}
                </div>

              </div>
            </div>
          </motion.div>
        )}

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
              {(popularWorks.length > 0 ? popularWorks : mockData.works).slice(0, 6).map((work, index) => (
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
    </div>
  );
}