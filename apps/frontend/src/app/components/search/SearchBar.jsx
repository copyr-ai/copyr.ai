'use client';

import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';

export default function SearchBar({ 
  searchQuery, 
  setSearchQuery, 
  onSearch, 
  isLoading,
  suggestions = []
}) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // Filter suggestions based on current query
  const filteredSuggestions = suggestions
    .filter(suggestion => 
      suggestion.toLowerCase().includes(searchQuery.toLowerCase()) && 
      suggestion.toLowerCase() !== searchQuery.toLowerCase()
    )
    .slice(0, 5);

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (!showSuggestions || filteredSuggestions.length === 0) {
      if (e.key === 'Enter') {
        onSearch();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < filteredSuggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : filteredSuggestions.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          setSearchQuery(filteredSuggestions[selectedIndex]);
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
            className="pl-16 pr-32 h-full w-full text-lg border-0 bg-transparent text-brand-dark placeholder:text-gray-500 focus:ring-0 focus:outline-none rounded-xl"
            autoComplete="off"
          />
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
        {showSuggestions && filteredSuggestions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-xl shadow-xl z-50 overflow-hidden"
          >
            {filteredSuggestions.map((suggestion, index) => (
              <div
                key={suggestion}
                onClick={() => handleSuggestionClick(suggestion)}
                className={`px-6 py-3 cursor-pointer transition-colors duration-150 flex items-center ${
                  index === selectedIndex 
                    ? 'bg-brand-pink/10 text-brand-pink' 
                    : 'hover:bg-gray-50 text-gray-700'
                }`}
              >
                <Search className="h-4 w-4 mr-3 text-gray-400" />
                <span className="text-sm">{suggestion}</span>
              </div>
            ))}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}