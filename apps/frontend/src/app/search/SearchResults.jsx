'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../components/ui/button';
import WorkCard from './WorkCard';

export default function SearchResults({ 
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
            {isLoading ? 'Searching...' : `Found ${searchResults.length} results`}
            {searchQuery && ` for "${searchQuery}"`}
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
        <div className="space-y-6">
          {searchResults.map((work, index) => (
            <WorkCard 
              key={work.id} 
              work={work} 
              variant="full" 
              index={index} 
            />
          ))}
        </div>
      </AnimatePresence>

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