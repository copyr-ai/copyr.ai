'use client';

import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, X } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';

export default function SearchBar({ 
  searchQuery, 
  setSearchQuery, 
  onSearch, 
  isLoading,
  suggestions = [],
  onClearAll
}) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // Filter suggestions based on current query and organize by sections
  const getFilteredSuggestions = () => {
    if (!searchQuery.trim()) return { sections: [], totalCount: 0 };

    const queryLower = searchQuery.toLowerCase();
    const filteredSections = [];
    let totalCount = 0;

    // If suggestions has sections (new format)
    if (suggestions?.sections) {
      suggestions.sections.forEach(section => {
        const matchingItems = section.items
          .filter(item => 
            item.toLowerCase().includes(queryLower) && 
            item.toLowerCase() !== queryLower
          )
          .slice(0, 4); // Limit items per section

        if (matchingItems.length > 0) {
          filteredSections.push({
            ...section,
            items: matchingItems
          });
          totalCount += matchingItems.length;
        }
      });
    } else {
      // Fallback for legacy flat array format
      const flatSuggestions = (suggestions || [])
        .filter(suggestion => 
          suggestion.toLowerCase().includes(queryLower) && 
          suggestion.toLowerCase() !== queryLower
        )
        .slice(0, 5);
      
      if (flatSuggestions.length > 0) {
        filteredSections.push({
          title: "Suggestions",
          icon: "🔍",
          items: flatSuggestions
        });
        totalCount = flatSuggestions.length;
      }
    }

    return { sections: filteredSections, totalCount };
  };

  const filteredSuggestions = getFilteredSuggestions();

  // Flatten suggestions for keyboard navigation
  const getFlatSuggestions = () => {
    const flat = [];
    filteredSuggestions.sections?.forEach(section => {
      section.items?.forEach(item => flat.push(item));
    });
    return flat;
  };

  const flatSuggestions = getFlatSuggestions();

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (!showSuggestions || filteredSuggestions.totalCount === 0) {
      if (e.key === 'Enter') {
        onSearch();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < flatSuggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : flatSuggestions.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && flatSuggestions[selectedIndex]) {
          setSearchQuery(flatSuggestions[selectedIndex]);
          setShowSuggestions(false);
          setSelectedIndex(-1);
        } else {
          onSearch();
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedIndex(-1);
        inputRef.current?.blur();
        break;
    }
  };

  // Handle input change
  const handleInputChange = (e) => {
    const value = e.target.value;
    setSearchQuery(value);
    setShowSuggestions(value.length > 0);
    setSelectedIndex(-1);
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion) => {
    setSearchQuery(suggestion);
    setShowSuggestions(false);
    setSelectedIndex(-1);
    inputRef.current?.focus();
  };

  // Handle input focus/blur
  const handleFocus = () => {
    if (searchQuery.length > 0) {
      setShowSuggestions(true);
    }
  };

  const handleBlur = () => {
    // Delay hiding suggestions to allow for clicks
    setTimeout(() => {
      setShowSuggestions(false);
      setSelectedIndex(-1);
    }, 150);
  };

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target)) {
        setShowSuggestions(false);
        setSelectedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.6 }}
      className="relative mb-8"
      ref={suggestionsRef}
    >
      <div className="relative group max-w-2xl mx-auto">
        <div className="absolute inset-0 bg-gradient-to-r from-brand-pink/20 to-brand-purple/20 rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-300 opacity-50"></div>
        <div className="relative bg-white border-2 border-gray-200 focus-within:border-brand-pink/50 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 h-[72px] flex items-center">
          <Search className="absolute left-6 text-gray-400 h-6 w-6 transition-colors group-focus-within:text-brand-pink" />
          <Input
            ref={inputRef}
            placeholder="Search for books, music, films, artwork..."
            value={searchQuery}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={handleFocus}
            onBlur={handleBlur}
            className="pl-16 pr-40 h-full w-full text-lg border-0 bg-transparent text-brand-dark placeholder:text-gray-500 focus:ring-0 focus:outline-none rounded-xl"
            autoComplete="off"
          />
          
          {/* Clear All Button */}
          {searchQuery && (
            <button
              onClick={onClearAll}
              className="absolute right-[120px] top-1/2 transform -translate-y-1/2 p-2 text-gray-400 hover:text-red-500 transition-colors duration-200 rounded-full hover:bg-red-50"
            >
              <X className="h-4 w-4" />
            </button>
          )}
          
          <Button 
            onClick={() => onSearch()}
            disabled={isLoading}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 px-4 h-[40px] text-sm bg-gradient-to-r from-brand-pink to-brand-purple hover:from-brand-pink/90 hover:to-brand-purple/90 text-white border-0 rounded-lg font-medium transition-all duration-300 flex items-center justify-center shrink-0"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Searching...
              </>
            ) : (
              <>
                <Search className="h-5 w-5 mr-2" />
                Search
              </>
            )}
          </Button>
        </div>

        {/* Autocomplete Suggestions */}
        {showSuggestions && filteredSuggestions.totalCount > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-xl shadow-xl z-50 overflow-hidden max-h-96 overflow-y-auto"
          >
            {filteredSuggestions.sections?.map((section, sectionIndex) => (
              <div key={section.title}>
                {/* Section Header */}
                <div className="px-4 py-2 bg-gray-50 border-b border-gray-100 sticky top-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{section.icon}</span>
                    <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                      {section.title}
                    </span>
                    <span className="text-xs text-gray-400">
                      ({section.items.length})
                    </span>
                  </div>
                </div>
                
                {/* Section Items */}
                {section.items.map((item, itemIndex) => {
                  const globalIndex = flatSuggestions.indexOf(item);
                  return (
                    <div
                      key={`${section.title}-${item}`}
                      onClick={() => handleSuggestionClick(item)}
                      className={`px-6 py-3 cursor-pointer transition-colors duration-150 flex items-center ${
                        globalIndex === selectedIndex 
                          ? 'bg-brand-pink/10 text-brand-pink' 
                          : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <Search className="h-4 w-4 mr-3 text-gray-400" />
                      <span className="text-sm">{item}</span>
                    </div>
                  );
                })}
                
                {/* Divider between sections (except last) */}
                {sectionIndex < filteredSuggestions.sections.length - 1 && (
                  <div className="border-b border-gray-100"></div>
                )}
              </div>
            ))}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}