'use client';

import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { 
  Calendar, User, Globe, Clock, ExternalLink, Eye,
  CheckCircle, XCircle, AlertCircle, Book, Music, Video, Image 
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { useWork } from '@/contexts/WorkContext';
import { useSearchLimit } from '@/contexts/SearchLimitContext';

// Utility functions
const getStatusIcon = (status) => {
  switch (status) {
    case 'Public Domain':
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case 'Under Copyright':
      return <XCircle className="h-5 w-5 text-red-500" />;
    default:
      return <AlertCircle className="h-5 w-5 text-yellow-500" />;
  }
};

const getCategoryIcon = (category) => {
  switch (category) {
    case 'Literature':
      return <Book className="h-5 w-5" />;
    case 'Music':
      return <Music className="h-5 w-5" />;
    case 'Film':
      return <Video className="h-5 w-5" />;
    case 'Art':
    case 'Photography':
      return <Image className="h-5 w-5" />;
    case 'Unknown':
      return <AlertCircle className="h-5 w-5" />;
    default:
      return <AlertCircle className="h-5 w-5" />;
  }
};

const getStatusColor = (status) => {
  switch (status) {
    case 'Public Domain':
      return 'bg-green-100 text-green-700';
    case 'Under Copyright':
      return 'bg-red-100 text-red-700';
    default:
      return 'bg-yellow-100 text-yellow-700';
  }
};

export default function WorkCard({ work, variant = 'full', index = 0 }) {
  const router = useRouter();
  const { storeWork } = useWork();
  const { handleSearchAttemptAtLimit } = useSearchLimit();

  const handleWorkClick = () => {
    // Check search limit and handle modal display
    const canProceed = handleSearchAttemptAtLimit();
    if (!canProceed) {
      return; // This will show the login modal if at limit
    }
    // Create a shareable URL that includes search parameters
    const createShareableUrl = () => {
      const searchParams = new URLSearchParams({
        title: work.title || '',
        author: work.author_name || '',
        year: work.publication_year || '',
        country: work.country || 'US'
      });
      
      return `/work?${searchParams.toString()}`;
    };

    // Store work data in context for immediate navigation
    storeWork(work);
    
    // Navigate to shareable URL with search parameters
    const shareableUrl = createShareableUrl();
    console.log('WorkCard - Navigating to shareable URL:', shareableUrl);
    router.push(shareableUrl);
  };

  if (variant === 'compact') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: index * 0.05 }}
        onClick={handleWorkClick}
      >
        <Card className="bg-white/50 backdrop-blur-sm rounded-lg border border-gray-200 hover:shadow-lg transition-all duration-300 hover:-translate-y-1 cursor-pointer group">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-gradient-to-r from-brand-pink/10 to-brand-purple/10 rounded-lg">
                {getCategoryIcon(work.category)}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-sm text-brand-dark group-hover:text-brand-pink transition-colors line-clamp-2">
                  {work.title}
                </h3>
                <p className="text-xs text-gray-600 mt-1 truncate">{work.author_name}</p>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-gray-500">{work.publication_year}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(work.status)}`}>
                    {work.status === 'Public Domain' ? 'PD' : work.status === 'Under Copyright' ? 'UC' : 'UK'}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  if (variant === 'preview') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 1.2 + index * 0.1 }}
      >
        <Card className="bg-white/50 backdrop-blur-sm rounded-2xl border border-gray-200 hover:shadow-lg transition-all duration-300 hover:-translate-y-1 cursor-pointer group h-[180px] flex flex-col overflow-hidden"
              onClick={handleWorkClick}>
          <CardHeader className="pb-3 flex-shrink-0">
            <div className="flex items-start gap-3 w-full overflow-hidden">
              <div className="p-2 bg-gradient-to-r from-brand-pink/10 to-brand-purple/10 rounded-lg flex-shrink-0">
                {getCategoryIcon(work.category)}
              </div>
              <div className="flex-1 min-w-0 overflow-hidden">
                <CardTitle className="text-lg text-brand-dark group-hover:text-brand-pink transition-colors leading-tight overflow-hidden">
                  <div 
                    className="break-words"
                    style={{
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}
                  >
                    {work.title}
                  </div>
                </CardTitle>
                <p className="text-sm text-gray-600 mt-1 overflow-hidden text-ellipsis whitespace-nowrap">{work.author_name}</p>
              </div>
              <div className="flex-shrink-0">
                {getStatusIcon(work.status)}
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-0 flex-1 flex flex-col justify-end overflow-hidden">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2 text-gray-600 min-w-0 flex-1">
                <Calendar className="h-3 w-3 flex-shrink-0" />
                <span className="overflow-hidden text-ellipsis whitespace-nowrap">{work.publication_year}</span>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap ml-2 flex-shrink-0 ${getStatusColor(work.status)}`}>
                {work.status}
              </span>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  // Full variant (default)
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
    >
      <Card className="bg-white/50 backdrop-blur-sm rounded-2xl border border-gray-200 hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4 flex-1">
              <div className="p-3 bg-gradient-to-r from-brand-pink/10 to-brand-purple/10 rounded-lg">
                {getCategoryIcon(work.category)}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <CardTitle className="text-xl text-brand-dark">{work.title}</CardTitle>
                  {getStatusIcon(work.status)}
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                  <div className="flex items-center gap-1">
                    <User className="h-4 w-4" />
                    {work.author_name}
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {work.publication_year}
                  </div>
                  <div className="flex items-center gap-1">
                    <Globe className="h-4 w-4" />
                    {work.country}
                  </div>
                </div>
                <div className="flex items-center gap-2 mb-3">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(work.status)}`}>
                    {work.status}
                  </span>
                  {work.confidence_score && (
                    <span className="text-sm text-gray-600">
                      Confidence: {(work.confidence_score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Copyright Analysis */}
          <div className="bg-gray-50/80 p-4 rounded-lg">
            <h4 className="font-semibold text-brand-dark mb-2">Copyright Analysis</h4>
            {work.notes && <p className="text-sm text-gray-600 mb-3">{work.notes}</p>}
            
            {work.enters_public_domain && (
              <div className="flex items-center gap-2 text-sm">
                <Clock className="h-4 w-4" />
                <span>
                  {work.status === 'Public Domain' 
                    ? `Entered public domain: ${work.enters_public_domain}`
                    : `Enters public domain: ${work.enters_public_domain}`
                  }
                </span>
              </div>
            )}
          </div>
          
          {/* Source Links */}
          {(work.source_links || work.source) && (
            <div>
              <h4 className="font-semibold text-brand-dark mb-2">Sources</h4>
              <div className="flex flex-wrap gap-2">
                {/* Handle legacy source_links object format */}
                {work.source_links && typeof work.source_links === 'object' && Object.keys(work.source_links).length > 0 && 
                  Object.entries(work.source_links).map(([source, url]) => (
                    <Button
                      key={source}
                      variant="outline"
                      size="sm"
                      className="h-8 text-xs"
                      onClick={() => window.open(url, '_blank')}
                    >
                      <ExternalLink className="h-3 w-3 mr-1" />
                      {source.toUpperCase()}
                    </Button>
                  ))
                }
                {/* Handle new comma-separated source URLs */}
                {work.source && typeof work.source === 'string' && work.source.trim() && 
                  work.source.split(',').filter(url => {
                    const trimmedUrl = url.trim();
                    return trimmedUrl && trimmedUrl.startsWith('http');
                  }).map((url, index) => {
                    const trimmedUrl = url.trim();
                    
                    // Extract source name from URL with more specific labeling
                    let sourceName = 'Source';
                    if (trimmedUrl.includes('musicbrainz.org')) {
                      sourceName = 'MusicBrainz';
                    } else if (trimmedUrl.includes('lccn.loc.gov')) {
                      // Extract LCCN number for better labeling
                      const lccnMatch = trimmedUrl.match(/lccn\.loc\.gov\/(\w+)/);
                      sourceName = lccnMatch ? `LOC (${lccnMatch[1]})` : 'Library of Congress';
                    } else if (trimmedUrl.includes('loc.gov') || trimmedUrl.includes('catalog.loc.gov')) {
                      sourceName = 'Library of Congress';
                    } else if (trimmedUrl.includes('hathitrust.org')) {
                      sourceName = 'HathiTrust';
                    }
                    
                    return (
                      <Button
                        key={`card-source-${index}-${trimmedUrl.slice(0, 20)}`}
                        variant="outline"
                        size="sm"
                        className="h-8 text-xs"
                        onClick={() => window.open(trimmedUrl, '_blank')}
                      >
                        <ExternalLink className="h-3 w-3 mr-1" />
                        {sourceName}
                      </Button>
                    );
                  })
                }
              </div>
            </div>
          )}
          
          {/* Action Button */}
          <div className="pt-4 border-t border-gray-200">
            <Button
              onClick={handleWorkClick}
              className="w-full bg-gradient-to-r from-brand-pink to-brand-purple hover:from-brand-pink/90 hover:to-brand-purple/90 text-white"
            >
              <Eye className="h-4 w-4 mr-2" />
              View Details
            </Button>
          </div>
          
          {/* Metadata */}
          {work.queried_at && (
            <div className="text-xs text-gray-500 pt-2">
              Last analyzed: {new Date(work.queried_at).toLocaleString()}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}