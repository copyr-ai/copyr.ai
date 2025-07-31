'use client';

import { motion } from 'framer-motion';
import { 
  Book, Music, Video, Image, Globe, 
  CheckCircle, XCircle, AlertCircle 
} from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

const FilterIcon = ({ category, type }) => {
  if (type === 'category') {
    switch (category) {
      case 'Literature':
        return <Book className="h-4 w-4 text-brand-pink" />;
      case 'Music':
        return <Music className="h-4 w-4 text-brand-pink" />;
      case 'Film':
        return <Video className="h-4 w-4 text-brand-pink" />;
      case 'Art':
      case 'Photography':
        return <Image className="h-4 w-4 text-brand-pink" />;
      default:
        return <Globe className="h-4 w-4 text-brand-pink" />;
    }
  }
  
  if (type === 'status') {
    switch (category) {
      case 'Public Domain':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'Under Copyright':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'Unknown':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default:
        return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
  }
  
  if (type === 'country') {
    switch (category) {
      case 'US':
        return <span className="text-base">🇺🇸</span>;
      case 'UK':
        return <span className="text-base">🇬🇧</span>;
      case 'CA':
        return <span className="text-base">🇨🇦</span>;
      case 'DE':
        return <span className="text-base">🇩🇪</span>;
      case 'All':
      default:
        return <Globe className="h-4 w-4 text-brand-purple" />;
    }
  }
  
  return <Globe className="h-4 w-4 text-brand-purple" />;
};

export default function SearchFilters({ 
  categories, 
  countries, 
  statuses, 
  selectedCategory, 
  selectedCountry, 
  selectedStatus, 
  onFilterChange,
  onClearFilters
}) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.8 }}
      className="flex flex-wrap gap-4 justify-center mb-8"
    >
      {/* Category Filter */}
      <div className="relative">
        <Select 
          key="category-select"
          value={selectedCategory} 
          onValueChange={(value) => onFilterChange('category', value)}
        >
          <SelectTrigger className="w-[150px] h-12 bg-white/90 backdrop-blur-sm border-2 border-brand-pink/20 hover:border-brand-pink/40 focus:border-brand-pink/60 focus:ring-0 focus:outline-none rounded-lg shadow-sm hover:shadow-md transition-all duration-300">
            <div className="flex items-center gap-2">
              <Book className="h-4 w-4 text-brand-pink" />
              <span className="text-sm text-gray-700">
                {selectedCategory === 'All' ? 'Content Type' : selectedCategory}
              </span>
            </div>
          </SelectTrigger>
          <SelectContent className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-lg shadow-xl">
            {categories.map((category, index) => (
              <SelectItem 
                key={`category-${index}-${category}`} 
                value={category} 
                className="hover:bg-brand-pink/10 focus:bg-brand-pink/10"
              >
                <div className="flex items-center gap-2">
                  <FilterIcon category={category} type="category" />
                  {category}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      
      {/* Country Filter */}
      <div className="relative">
        <Select 
          value={selectedCountry} 
          onValueChange={(value) => onFilterChange('country', value)}
        >
          <SelectTrigger className="w-[130px] h-12 bg-white/90 backdrop-blur-sm border-2 border-brand-purple/20 hover:border-brand-purple/40 focus:border-brand-purple/60 focus:ring-0 focus:outline-none rounded-lg shadow-sm hover:shadow-md transition-all duration-300">
            <div className="flex items-center gap-2">
              <Globe className="h-4 w-4 text-brand-purple" />
              <span className="text-sm text-gray-700">
                {selectedCountry === 'All' ? 'Country' : selectedCountry}
              </span>
            </div>
          </SelectTrigger>
          <SelectContent className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-lg shadow-xl">
            {countries.map(country => (
              <SelectItem 
                key={country} 
                value={country} 
                className="hover:bg-brand-purple/10 focus:bg-brand-purple/10"
              >
                <div className="flex items-center gap-2">
                  <FilterIcon category={country} type="country" />
                  {country}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      
      {/* Status Filter */}
      <div className="relative">
        <Select 
          value={selectedStatus} 
          onValueChange={(value) => onFilterChange('status', value)}
        >
          <SelectTrigger className={`w-[170px] h-12 bg-white/90 backdrop-blur-sm border-2 rounded-lg shadow-sm hover:shadow-md transition-all duration-300 focus:ring-0 focus:outline-none ${
            selectedStatus === 'Public Domain' 
              ? 'border-green-400/40 hover:border-green-400/60 focus:border-green-400/80' 
              : selectedStatus === 'Under Copyright'
              ? 'border-red-400/40 hover:border-red-400/60 focus:border-red-400/80'
              : selectedStatus === 'Unknown'
              ? 'border-yellow-400/40 hover:border-yellow-400/60 focus:border-yellow-400/80'
              : 'border-gray-300/40 hover:border-gray-300/60 focus:border-gray-300/80'
          }`}>
            <div className="flex items-center gap-2">
              <FilterIcon category={selectedStatus} type="status" />
              <span className="text-sm text-gray-700">
                {selectedStatus === 'All' ? 'Copyright Status' : selectedStatus}
              </span>
            </div>
          </SelectTrigger>
          <SelectContent className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-lg shadow-xl">
            {statuses.map(status => (
              <SelectItem 
                key={status} 
                value={status} 
                className={`${
                  status === 'Public Domain' 
                    ? 'hover:bg-green-50 focus:bg-green-50' 
                    : status === 'Under Copyright'
                    ? 'hover:bg-red-50 focus:bg-red-50'
                    : status === 'Unknown'
                    ? 'hover:bg-yellow-50 focus:bg-yellow-50'
                    : 'hover:bg-gray-50 focus:bg-gray-50'
                }`}
              >
                <div className="flex items-center gap-2">
                  <FilterIcon category={status} type="status" />
                  {status}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      
      {/* Clear Filters Button */}
      {(selectedCategory !== 'All' || selectedCountry !== 'All' || selectedStatus !== 'All') && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          transition={{ duration: 0.2 }}
        >
          <button
            onClick={() => {
              if (onClearFilters) {
                onClearFilters();
              } else {
                // Fallback to individual filter changes
                onFilterChange('category', 'All');
                onFilterChange('country', 'All');
                onFilterChange('status', 'All');
              }
            }}
            className="h-9 px-4 bg-red-50 hover:bg-red-100 border-2 border-red-300 hover:border-red-400 focus:border-red-500 focus:ring-0 focus:outline-none rounded-lg shadow-sm hover:shadow-md transition-all duration-300 text-sm text-red-700 hover:text-red-800 font-semibold"
          >
            ✕ Clear Filters
          </button>
        </motion.div>
      )}
    </motion.div>
  );
}