import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import lunr from 'lunr';

export default function useSearch(data) {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Initialize state from URL params with proper decoding (handle double encoding)
  const [searchQuery, setSearchQuery] = useState(() => {
    const rawQuery = searchParams.get('q') || '';
    try {
      // Handle double encoding by decoding twice if needed
      let decoded = decodeURIComponent(rawQuery);
      // If it still contains encoded characters, decode again
      if (decoded.includes('%')) {
        decoded = decodeURIComponent(decoded);
      }
      return decoded.replace(/\+/g, ' ');
    } catch {
      // Fallback if decoding fails
      return rawQuery.replace(/\+/g, ' ');
    }
  });
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get('category') || 'All');
  const [selectedCountry, setSelectedCountry] = useState(searchParams.get('country') || 'All');
  const [selectedStatus, setSelectedStatus] = useState(searchParams.get('status') || 'All');
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

  // Handle URL params on initial load and when searchParams change
  useEffect(() => {
    const query = searchParams.get('q');
    const category = searchParams.get('category');
    const country = searchParams.get('country');
    const status = searchParams.get('status');
    
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
          console.log('URL search query decoded:', finalQuery); // Debug log
        } catch (error) {
          // Fallback if decoding fails
          const fallbackQuery = query.replace(/\+/g, ' ');
          setSearchQuery(fallbackQuery);
          console.log('URL search query fallback:', fallbackQuery); // Debug log
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
  }, [searchParams, searchIndex]); // Added searchIndex dependency

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

  // Main search function
  const performSearch = (scrollToResults = true) => {
    if (!searchQuery.trim() && selectedCategory === 'All' && selectedCountry === 'All' && selectedStatus === 'All') {
      if (hasSearched) {
        clearSearch();
      }
      return;
    }
    
    setIsLoading(true);
    setHasSearched(true);
    
    // Update URL with search parameters
    updateURL(searchQuery, selectedCategory, selectedCountry, selectedStatus);
    
    // Fast search with Lunr.js
    setTimeout(() => {
      let results = [];
      
      console.log('Performing search with query:', searchQuery.trim()); // Debug log
      console.log('Search index available:', !!searchIndex); // Debug log
      
      if (searchQuery.trim() && searchIndex) {
        // Use Lunr.js for text search
        try {
          const searchResults = searchIndex.search(searchQuery);
          console.log('Lunr search results:', searchResults); // Debug log
          const searchIds = searchResults.map(result => parseInt(result.ref));
          results = data.works.filter(work => searchIds.includes(work.id));
          console.log('Filtered results from Lunr:', results.length); // Debug log
          
          // If no results from Lunr, try a fallback search
          if (results.length === 0) {
            console.log('Lunr returned no results, trying fallback search'); // Debug log
            results = data.works.filter(work => 
              work.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
              work.author_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
              work.category.toLowerCase().includes(searchQuery.toLowerCase())
            );
            console.log('Fallback search results:', results.length); // Debug log
          }
        } catch (error) {
          console.warn('Lunr search failed, using fallback:', error);
          // Fallback to simple text search
          results = data.works.filter(work => 
            work.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            work.author_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            work.category.toLowerCase().includes(searchQuery.toLowerCase())
          );
        }
      } else if (!searchQuery.trim()) {
        console.log('No search query, showing all results'); // Debug log
        // No text query, use all results
        results = [...data.works];
      }
      
      // Apply additional filters
      const filteredResults = results.filter(work => {
        const matchesCategory = selectedCategory === 'All' || work.category === selectedCategory;
        const matchesCountry = selectedCountry === 'All' || work.country === selectedCountry;
        const matchesStatus = selectedStatus === 'All' || work.status === selectedStatus;
        
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

  // Handle filter changes
  const handleFilterChange = (filterType, value) => {
    switch (filterType) {
      case 'category':
        setSelectedCategory(value);
        break;
      case 'country':
        setSelectedCountry(value);
        break;
      case 'status':
        setSelectedStatus(value);
        break;
    }
    
    // Trigger search immediately when filter changes
    setTimeout(() => performSearch(false), 100);
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
    handleFilterChange,
    clearSearch
  };
}