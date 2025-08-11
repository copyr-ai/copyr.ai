import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useWork } from '@/contexts/WorkContext';
import { apiClient } from '../lib/api';

export default function useSearchWithAPI() {
  const router = useRouter();
  const { user, saveSearchToHistory } = useAuth();
  const { storeSearchResults } = useWork();
  
  // Initialize state - will be updated from URL params after hydration
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedCountry, setSelectedCountry] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState(null);

  // Handle URL params on initial load (client-side only)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('q');
    const category = urlParams.get('category');
    const country = urlParams.get('country');
    const status = urlParams.get('status');
    
    console.log('URL params detected:', { query, category, country, status });
    
    if (query || category || country || status) {
      let finalQuery = '';
      
      // Properly decode the query parameter (handle double encoding)
      if (query) {
        try {
          let decodedQuery = decodeURIComponent(query);
          // If it still contains encoded characters, decode again
          if (decodedQuery.includes('%')) {
            decodedQuery = decodeURIComponent(decodedQuery);
          }
          finalQuery = decodedQuery.replace(/\+/g, ' ');
          // Clean any title: author: prefixes from the query
          finalQuery = finalQuery.replace(/^(title:\s*|author:\s*)+/gi, '').trim();
          setSearchQuery(finalQuery);
          console.log('Setting search query from URL:', finalQuery);
        } catch (error) {
          // Fallback if decoding fails
          finalQuery = query.replace(/\+/g, ' ');
          // Clean any title: author: prefixes from the query
          finalQuery = finalQuery.replace(/^(title:\s*|author:\s*)+/gi, '').trim();
          setSearchQuery(finalQuery);
          console.log('Fallback search query from URL:', finalQuery);
        }
      }
      
      // Set filters from URL
      const urlCategory = category && category !== 'All' ? category : 'All';
      const urlCountry = country && country !== 'All' ? country : 'All';
      const urlStatus = status && status !== 'All' ? status : 'All';
      
      setSelectedCategory(urlCategory);
      setSelectedCountry(urlCountry);
      setSelectedStatus(urlStatus);
      
      console.log('Setting filters from URL:', { urlCategory, urlCountry, urlStatus });
      
      setHasSearched(true);
      
      // Check for cached results first, then search if needed
      setTimeout(() => {
        // Try to get cached results from sessionStorage
        const cacheKey = `search-cache-${finalQuery}-${urlCategory}-${urlCountry}-${urlStatus}`;
        const cachedResults = sessionStorage.getItem(cacheKey);
        
        if (cachedResults) {
          try {
            const parsed = JSON.parse(cachedResults);
            const cacheAge = Date.now() - parsed.timestamp;
            
            // Use cache if it's less than 5 minutes old
            if (cacheAge < 5 * 60 * 1000 && parsed.results && parsed.results.length > 0) {
              console.log('Using cached search results from sessionStorage');
              setSearchResults(parsed.results);
              setHasSearched(true);
              return;
            }
          } catch (e) {
            console.log('Failed to parse cached results');
          }
        }
        
        // No valid cache found, perform fresh search
        console.log('No valid cache found, performing fresh search');
        performSearchWithValues(finalQuery, urlCategory, urlCountry, urlStatus, false);
      }, 100);
    }
  }, []); // Only run once on mount

  // Update URL when search params change
  const updateURL = (query, category, country, status) => {
    const params = new URLSearchParams();
    if (query && query.trim()) params.set('q', query); // URLSearchParams already handles encoding
    if (category && category !== 'All') params.set('category', category);
    if (country && country !== 'All') params.set('country', country);
    if (status && status !== 'All') params.set('status', status);
    
    const newURL = params.toString() ? `/search?${params.toString()}` : '/search';
    router.push(newURL, { scroll: false });
  };

  // Search function with explicit values (to avoid stale closure issues)
  const performSearchWithValues = async (query, category, country, status, scrollToResults = true) => {
    // Only return early if there's truly nothing to search for
    if (!query.trim() && category === 'All' && country === 'All' && status === 'All') {
      if (hasSearched) {
        clearSearch();
      }
      return;
    }
    
    setIsLoading(true);
    setError(null);
    setHasSearched(true);
    
    // Update URL with search parameters
    updateURL(query, category, country, status);
    
    try {
      let results = [];
      
      // Always use search endpoint for both query and filter scenarios
      if (!query.trim() && (category !== 'All' || country !== 'All' || status !== 'All')) {
        // Map frontend category to backend work_type
        let work_type = null;
        if (category === 'Literature') work_type = 'literary';
        else if (category === 'Music') work_type = 'musical';
        
        // Use search endpoint with filters only (no title/author)
        const searchResult = await apiClient.searchWorks({
          title: null,
          author: null,
          work_type,
          limit: 50, // Increase limit for filter-only searches
          country: country !== 'All' ? country : 'US',
          user_id: user?.id || null
        });
        
        // Convert search results to expected format
        if (searchResult?.results) {
          results = searchResult.results.map((result, index) => {
            // Proper work type categorization - don't guess unknown types
            let category = 'Unknown';
            if (result.work_type === 'literary') {
              category = 'Literature';
            } else if (result.work_type === 'musical') {
              category = 'Music';
            } else if (!result.work_type || result.work_type === '') {
              category = 'Unknown';
            } else {
              // Log unknown work types for debugging
              console.log('Unknown work_type encountered:', result.work_type, 'for work:', result.title);
              category = 'Unknown';
            }
            
            return {
              id: index + 1,
              title: result.title,
              author_name: result.author_name,
              category: category,
              country: country !== 'All' ? country : 'US',
              status: result.status,
              publication_year: result.publication_year,
              enters_public_domain: result.enters_public_domain,
              confidence_score: result.confidence_score,
              source: result.source
            };
          });
        }
      } else if (query.trim()) {
        // Parse query intelligently to extract title and author
        let title, author;
        
        if (query.includes(' by ')) {
          // Format: "Title by Author"
          const parts = query.split(' by ');
          title = parts[0].trim();
          author = parts[1].trim();
        } else if (query.includes(' - ')) {
          // Format: "Title - Author" 
          const parts = query.split(' - ');
          title = parts[0].trim();
          author = parts[1].trim();
        } else {
          // Single query - could be title or author
          // Let backend handle flexible search
          title = query.trim();
          author = null;
        }
        
        // Map category filter to work_type
        let work_type = null;
        if (category === 'Literature') work_type = 'literary';
        else if (category === 'Music') work_type = 'musical';
        
        // Use new search endpoint with higher limit for pagination
        const searchResult = await apiClient.searchWorks({
          title: title || null,
          author: author || null,
          work_type,
          limit: 50, // Increased limit to support pagination
          country: country !== 'All' ? country : 'US',
          user_id: user?.id || null
        });
        
        // Convert search results to expected format
        if (searchResult?.results) {
          results = searchResult.results.map((result, index) => {
            // Proper work type categorization - don't guess unknown types
            let category = 'Unknown';
            if (result.work_type === 'literary') {
              category = 'Literature';
            } else if (result.work_type === 'musical') {
              category = 'Music';
            } else if (!result.work_type || result.work_type === '') {
              category = 'Unknown';
            } else {
              // Log unknown work types for debugging
              console.log('Unknown work_type encountered:', result.work_type, 'for work:', result.title);
              category = 'Unknown';
            }
            
            return {
              id: index + 1,
              title: result.title,
              author_name: result.author_name,
              category: category,
              country: country !== 'All' ? country : 'US', // Use filter country
              status: result.status,
              publication_year: result.publication_year,
              enters_public_domain: result.enters_public_domain,
              confidence_score: result.confidence_score,
              source: result.source // Direct source field for UI (comma-separated)
            };
          });
        }
      }
      
      // Apply additional filters if needed
      const filteredResults = results.filter(work => {
        const matchesCategory = category === 'All' || work.category === category;
        const matchesCountry = country === 'All' || work.country === country;
        const matchesStatus = status === 'All' || work.status === status;
        
        return matchesCategory && matchesCountry && matchesStatus;
      });
      
      setSearchResults(filteredResults);
      
      // Store search results in WorkContext for work page navigation
      storeSearchResults(filteredResults);
      
      // Cache the search results for page refresh
      if (filteredResults && filteredResults.length > 0) {
        const cacheKey = `search-cache-${query}-${category}-${country}-${status}`;
        const cacheData = {
          results: filteredResults,
          timestamp: Date.now()
        };
        try {
          sessionStorage.setItem(cacheKey, JSON.stringify(cacheData));
          console.log('Cached search results for:', cacheKey);
        } catch (e) {
          console.log('Failed to cache search results');
        }
      }
      
      // Note: Search history is now automatically saved by the backend when user_id is provided
      
    } catch (error) {
      console.error('Search failed:', error);
      setError('Search failed. Please try again.');
      setSearchResults([]);
    } finally {
      setIsLoading(false);
      
      // Scroll to results if requested
      if (scrollToResults) {
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
      }
    }
  };

  // Main search function (uses current state values)
  const performSearch = (scrollToResults = true) => {
    performSearchWithValues(searchQuery, selectedCategory, selectedCountry, selectedStatus, scrollToResults);
  };

  // Handle filter changes
  const handleFilterChange = (filterType, value) => {
    let newCategory = selectedCategory;
    let newCountry = selectedCountry;
    let newStatus = selectedStatus;
    
    switch (filterType) {
      case 'category':
        setSelectedCategory(value);
        newCategory = value;
        break;
      case 'country':
        setSelectedCountry(value);
        newCountry = value;
        break;
      case 'status':
        setSelectedStatus(value);
        newStatus = value;
        break;
    }
    
    // Check if all filters are cleared and search query is empty
    const allFiltersCleared = newCategory === 'All' && newCountry === 'All' && newStatus === 'All';
    const isSearchEmpty = !searchQuery.trim();
    
    if (allFiltersCleared && isSearchEmpty) {
      // Clear everything including search state
      clearSearch();
    } else {
      // Trigger search immediately with the new values
      setTimeout(() => performSearchWithValues(searchQuery, newCategory, newCountry, newStatus, false), 100);
    }
  };

  // Clear all filters (used by clear filters button)
  const clearFilters = () => {
    const newCategory = 'All';
    const newCountry = 'All';
    const newStatus = 'All';
    
    setSelectedCategory(newCategory);
    setSelectedCountry(newCountry);
    setSelectedStatus(newStatus);
    
    // Check if search query is empty too
    const isSearchEmpty = !searchQuery.trim();
    
    if (isSearchEmpty) {
      // Clear everything including search state
      clearSearch();
    } else {
      // Keep search query but clear filters
      setTimeout(() => performSearchWithValues(searchQuery, newCategory, newCountry, newStatus, false), 100);
    }
  };

  // Search with query and clear all filters
  const searchWithClearedFilters = (query) => {
    setSearchQuery(query);
    setSelectedCategory('All');
    setSelectedCountry('All');
    setSelectedStatus('All');
    
    // Perform search with cleared filters
    setTimeout(() => performSearchWithValues(query, 'All', 'All', 'All', true), 100);
  };

  // Clear all search and filters
  const clearSearch = () => {
    setSearchQuery('');
    setSelectedCategory('All');
    setSelectedCountry('All');
    setSelectedStatus('All');
    setSearchResults([]);
    setHasSearched(false);
    setError(null);
    updateURL('', 'All', 'All', 'All');
  };

  return {
    // State
    searchQuery,
    selectedCategory,
    selectedCountry,
    selectedStatus,
    searchResults,
    isLoading,
    hasSearched,
    error,
    
    // Actions
    setSearchQuery,
    setSearchResults,
    setHasSearched,
    performSearch,
    performSearchWithValues,
    handleFilterChange,
    clearFilters,
    searchWithClearedFilters,
    clearSearch
  };
}