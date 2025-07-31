import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import lunr from 'lunr';

export default function useSearch(data) {
  const router = useRouter();
  
  // Initialize state - will be updated from URL params after hydration
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedCountry, setSelectedCountry] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchIndex, setSearchIndex] = useState(null);

  // Initialize Lunr.js search index
  useEffect(() => {
    if (!data?.works) return;
    
    const idx = lunr(function () {
      this.ref('id');
      this.field('title', { boost: 10 });
      this.field('author_name', { boost: 5 });
      this.field('category');
      this.field('notes');

      data.works.forEach((work) => {
        this.add(work);
      });
    });
    setSearchIndex(idx);
  }, [data]);

  // Handle URL params on initial load (client-side only)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('q');
    const category = urlParams.get('category');
    const country = urlParams.get('country');
    const status = urlParams.get('status');
    
    if (query || category || country || status) {
      // Properly decode the query parameter (handle double encoding)
      if (query) {
        try {
          let decodedQuery = decodeURIComponent(query);
          // If it still contains encoded characters, decode again
          if (decodedQuery.includes('%')) {
            decodedQuery = decodeURIComponent(decodedQuery);
          }
          const finalQuery = decodedQuery.replace(/\+/g, ' ');
          setSearchQuery(finalQuery);
        } catch (error) {
          // Fallback if decoding fails
          const fallbackQuery = query.replace(/\+/g, ' ');
          setSearchQuery(fallbackQuery);
        }
      }
      
      // Set filters from URL
      if (category) setSelectedCategory(category);
      if (country) setSelectedCountry(country);
      if (status) setSelectedStatus(status);
      
      setHasSearched(true);
      
      // Delay the search to ensure searchIndex is ready
      setTimeout(() => {
        performSearch(false); // Don't scroll on initial load
      }, 100);
    }
  }, [searchIndex]); // Added searchIndex dependency

  // Update URL when search params change
  const updateURL = (query, category, country, status) => {
    const params = new URLSearchParams();
    if (query && query.trim()) params.set('q', encodeURIComponent(query));
    if (category && category !== 'All') params.set('category', category);
    if (country && country !== 'All') params.set('country', country);
    if (status && status !== 'All') params.set('status', status);
    
    const newURL = params.toString() ? `/search?${params.toString()}` : '/search';
    router.push(newURL, { scroll: false });
  };

  // Search function with explicit values (to avoid stale closure issues)
  const performSearchWithValues = (query, category, country, status, scrollToResults = true) => {
    // Only return early if there's truly nothing to search for
    if (!query.trim() && category === 'All' && country === 'All' && status === 'All') {
      if (hasSearched) {
        clearSearch();
      }
      return;
    }
    
    setIsLoading(true);
    setHasSearched(true);
    
    // Update URL with search parameters
    updateURL(query, category, country, status);
    
    // Fast search with Lunr.js
    setTimeout(() => {
      let results = [];
      
      
      if (query.trim() && searchIndex) {
        // Use Lunr.js for text search
        try {
          const searchResults = searchIndex.search(query);
          const searchIds = searchResults.map(result => parseInt(result.ref));
          results = data.works.filter(work => searchIds.includes(work.id));
          
          // If no results from Lunr, try a fallback search
          if (results.length === 0) {
            results = data.works.filter(work => 
              work.title.toLowerCase().includes(query.toLowerCase()) ||
              work.author_name.toLowerCase().includes(query.toLowerCase()) ||
              work.category.toLowerCase().includes(query.toLowerCase())
            );
          }
        } catch (error) {
          console.warn('Lunr search failed, using fallback:', error);
          // Fallback to simple text search
          results = data.works.filter(work => 
            work.title.toLowerCase().includes(query.toLowerCase()) ||
            work.author_name.toLowerCase().includes(query.toLowerCase()) ||
            work.category.toLowerCase().includes(query.toLowerCase())
          );
        }
      } else if (!query.trim()) {
        // No text query, use all results
        results = [...data.works];
      }
      
      // Apply additional filters
      const filteredResults = results.filter(work => {
        const matchesCategory = category === 'All' || work.category === category;
        const matchesCountry = country === 'All' || work.country === country;
        const matchesStatus = status === 'All' || work.status === status;
        
        return matchesCategory && matchesCountry && matchesStatus;
      });
      
      setSearchResults(filteredResults);
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
    }, 300);
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
    
    // Trigger search immediately with the new values
    setTimeout(() => performSearchWithValues(searchQuery, newCategory, newCountry, newStatus, false), 100);
  };

  // Clear all search and filters
  const clearSearch = () => {
    setSearchQuery('');
    setSelectedCategory('All');
    setSelectedCountry('All');
    setSelectedStatus('All');
    setSearchResults([]);
    setHasSearched(false);
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
    
    // Actions
    setSearchQuery,
    performSearch,
    performSearchWithValues,
    handleFilterChange,
    clearSearch
  };
}