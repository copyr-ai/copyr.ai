'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../components/ui/button';
import WorkCard from './WorkCard';

export default function SearchPagination({ 
  searchResults, 
  isLoading, 
  hasSearched, 
  searchQuery, 
  onClearSearch,
  setSearchQuery,
  performSearch,
  performSearchWithValues,
  searchWithClearedFilters,
  selectedCategory,
  selectedCountry,
  selectedStatus
}) {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 6;
  
  // Calculate pagination
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentResults = searchResults.slice(startIndex, endIndex);
  const totalPages = Math.ceil(searchResults.length / itemsPerPage);
  const hasMorePages = currentPage < totalPages;

  // Reset pagination when search results change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchResults]);

  const scrollToResults = () => {
    setTimeout(() => {
      const resultsElement = document.querySelector('[data-search-results]');
      if (resultsElement) {
        resultsElement.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start',
          inline: 'nearest'
        });
      }
    }, 100);
  };

  const handleNext = () => {
    setCurrentPage(prev => prev + 1);
    scrollToResults();
  };

  const handlePrevious = () => {
    setCurrentPage(prev => prev - 1);
    scrollToResults();
  };

  if (!hasSearched) return null;

  return (
    <div className="px-4 max-w-7xl mx-auto mb-20">
      <AnimatePresence mode="wait">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.5 }}
          className="mb-6 flex items-center justify-between"
        >
          <p className="text-sm text-gray-600">
            {isLoading ? 'Searching...' : (
              <>
                {searchResults.length > 0 && (
                  <>
                    Showing {startIndex + 1}-{Math.min(endIndex, searchResults.length)} of {searchResults.length} results
                    {searchQuery && ` for "${searchQuery}"`}
                  </>
                )}
                {searchResults.length === 0 && !isLoading && (
                  <>Found 0 results{searchQuery && ` for "${searchQuery}"`}</>
                )}
              </>
            )}
          </p>
          <Button 
            variant="outline" 
            size="sm"
            onClick={onClearSearch}
            className="text-xs"
          >
            Clear Search
          </Button>
        </motion.div>
      </AnimatePresence>

      {/* Results List */}
      <AnimatePresence>
        {currentResults.length > 0 && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8"
          >
            {currentResults.map((work, index) => (
              <WorkCard 
                key={work.id || work.slug || `search-result-${startIndex + index}-${work.title?.slice(0, 20) || 'untitled'}`} 
                work={work} 
                variant="full" 
                index={startIndex + index} 
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Pagination Controls */}
      {searchResults.length > itemsPerPage && (
        <div className="flex justify-center items-center gap-4">
          {currentPage > 1 && (
            <Button 
              variant="outline"
              onClick={handlePrevious}
              className="text-sm"
            >
              Previous
            </Button>
          )}
          
          <span className="text-sm text-gray-500">
            Page {currentPage} of {totalPages}
          </span>
          
          {hasMorePages && (
            <Button 
              onClick={handleNext}
              className="bg-gradient-to-r from-brand-pink to-brand-purple hover:from-brand-pink/90 hover:to-brand-purple/90 text-white text-sm"
            >
              {currentPage === 1 ? 'Show More' : 'Next'}
            </Button>
          )}
        </div>
      )}

      {/* No Results State */}
      {hasSearched && !isLoading && searchResults.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4 opacity-20">🔍</div>
          <h3 className="text-lg font-semibold text-brand-dark mb-2">No results found</h3>
          <p className="text-gray-600 mb-4">
            We couldn&apos;t find any works matching your search. Try different keywords or adjust your filters.
          </p>
          <div className="flex gap-3 justify-center">
            <Button 
              variant="outline" 
              onClick={onClearSearch}
            >
              Clear Search
            </Button>
            <Button 
              onClick={() => {
                if (searchWithClearedFilters) {
                  searchWithClearedFilters('gatsby');
                } else {
                  // Fallback
                  setSearchQuery('gatsby');
                  performSearchWithValues('gatsby', 'All', 'All', 'All', true);
                }
              }}
              className="bg-gradient-to-r from-brand-pink to-brand-purple hover:from-brand-pink/90 hover:to-brand-purple/90 text-white"
            >
              Try &quot;gatsby&quot;
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}