'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { useWork } from '@/contexts/WorkContext';
import { 
  ArrowLeft, Share2, Download, ExternalLink, 
  Calendar, User, Globe, Clock, CheckCircle, 
  XCircle, AlertCircle, Copy
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

import mockData from '../../data/mockWorks.json';
import { apiClient } from '../../lib/api';

// Use centralized mock data
const mockSearchResults = mockData.works;

// Custom cursor hook with performance optimization
const useCustomCursor = () => {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);
  const [isOverFooter, setIsOverFooter] = useState(false);
  const rafRef = useRef(null);
  const lastUpdate = useRef(0);

  useEffect(() => {
    const updateMousePosition = (e) => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      
      rafRef.current = requestAnimationFrame(() => {
        const now = Date.now();
        if (now - lastUpdate.current > 16) {
          setMousePosition({ x: e.clientX, y: e.clientY });
          
          if (now - lastUpdate.current > 50) {
            const footerElement = document.querySelector('footer');
            if (footerElement) {
              const footerRect = footerElement.getBoundingClientRect();
              const isInFooter = e.clientY >= footerRect.top && 
                                e.clientY <= footerRect.bottom &&
                                e.clientX >= footerRect.left && 
                                e.clientX <= footerRect.right;
              setIsOverFooter(isInFooter);
            }
          }
          lastUpdate.current = now;
        }
      });
    };
    
    const handleMouseEnter = () => setIsHovering(true);
    const handleMouseLeave = () => setIsHovering(false);
    
    window.addEventListener('mousemove', updateMousePosition, { passive: true });
    
    const interactiveElements = document.querySelectorAll('button, a, [role="button"]');
    interactiveElements.forEach(el => {
      el.addEventListener('mouseenter', handleMouseEnter, { passive: true });
      el.addEventListener('mouseleave', handleMouseLeave, { passive: true });
    });
    
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      window.removeEventListener('mousemove', updateMousePosition);
      interactiveElements.forEach(el => {
        el.removeEventListener('mouseenter', handleMouseEnter);
        el.removeEventListener('mouseleave', handleMouseLeave);
      });
    };
  }, []);

  return { mousePosition, isHovering, isOverFooter };
};

function WorkDetailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { mousePosition, isHovering, isOverFooter } = useCustomCursor();
  const { getCurrentSearchResults } = useWork();
  const [work, setWork] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [copySuccess, setCopySuccess] = useState(false);

  useEffect(() => {
    const findWork = async () => {
      console.log('Work page - Search params:', searchParams.toString());
      
      // Get search parameters and decode them
      const title = decodeURIComponent(searchParams.get('title') || '');
      const author = decodeURIComponent(searchParams.get('author') || '');
      const year = searchParams.get('year');
      const country = searchParams.get('country');
      
      console.log('Work page - Looking for work:', { title, author, year, country });
      
      let foundWork = null;
      
      // First try to find in current search results (for immediate navigation)
      const currentResults = getCurrentSearchResults();
      if (currentResults && currentResults.length > 0) {
        foundWork = currentResults.find(w => {
          const titleMatch = w.title?.toLowerCase().trim() === title.toLowerCase().trim();
          const authorMatch = !author || w.author_name?.toLowerCase().trim() === author.toLowerCase().trim();
          const yearMatch = !year || w.publication_year?.toString() === year;
          return titleMatch && authorMatch && yearMatch;
        });
        console.log('Work page - Found in current results:', foundWork);
      }
      
      // If not found in current results, try mock data
      if (!foundWork) {
        foundWork = mockSearchResults.find(w => {
          const titleMatch = w.title?.toLowerCase().trim() === title.toLowerCase().trim();
          const authorMatch = !author || w.author_name?.toLowerCase().trim() === author.toLowerCase().trim();
          const yearMatch = !year || w.publication_year?.toString() === year;
          return titleMatch && authorMatch && yearMatch;
        });
        console.log('Work page - Found in mock data:', foundWork);
      }
      
      // If still not found, try API search
      if (!foundWork && title) {
        try {
          console.log('Work page - Searching API for work');
          const searchResult = await apiClient.searchWorks({
            title: title,
            author: author || null,
            work_type: null,
            limit: 1,
            country: country || 'US',
            user_id: null
          });

          if (searchResult?.results && searchResult.results.length > 0) {
            const apiWork = searchResult.results[0];
            console.log('Work page - Found work via API search:', apiWork);
            
            foundWork = {
              id: `work-${Date.now()}`,
              slug: `work-${Date.now()}`,
              title: apiWork.title,
              author_name: apiWork.author_name,
              publication_year: apiWork.publication_year,
              country: country || 'US',
              status: apiWork.status,
              work_type: apiWork.work_type,
              category: apiWork.work_type === 'literary' ? 'Literature' : apiWork.work_type === 'musical' ? 'Music' : 'Unknown',
              confidence_score: apiWork.confidence_score,
              notes: apiWork.notes || 'No analysis available.',
              enters_public_domain: apiWork.enters_public_domain,
              source: apiWork.source,
              published: true,
              queried_at: new Date().toISOString()
            };
          }
        } catch (error) {
          console.error('Work page - API search failed:', error);
        }
      }
      
      if (foundWork) {
        const completeWork = {
          slug: foundWork.slug || `work-${Date.now()}`,
          id: foundWork.id || `work-${Date.now()}`,
          title: foundWork.title || 'Unknown Title',
          author_name: foundWork.author_name || 'Unknown Author',
          publication_year: foundWork.publication_year || 'Unknown',
          country: foundWork.country || 'Unknown',
          status: foundWork.status || 'Unknown',
          work_type: foundWork.work_type || foundWork.category || 'Unknown',
          category: foundWork.category || foundWork.work_type || 'Unknown',
          confidence_score: foundWork.confidence_score || 0,
          notes: foundWork.notes || 'No analysis available.',
          enters_public_domain: foundWork.enters_public_domain,
          source_links: foundWork.source_links || {},
          source: foundWork.source,
          published: foundWork.published !== undefined ? foundWork.published : true,
          queried_at: foundWork.queried_at || new Date().toISOString(),
          ...foundWork
        };
        setWork(completeWork);
      }
      setIsLoading(false);
    };

    findWork();
  }, [searchParams, getCurrentSearchResults]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'Public Domain':
        return <CheckCircle className="h-6 w-6 text-green-500" />;
      case 'Under Copyright':
        return <XCircle className="h-6 w-6 text-red-500" />;
      default:
        return <AlertCircle className="h-6 w-6 text-yellow-500" />;
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  if (isLoading) {
    return (
      <div className="grainy-bg min-h-screen overflow-x-hidden relative">
        <div 
          className={`custom-cursor ${isHovering ? 'hover' : ''} ${isOverFooter ? 'footer' : ''}`}
          style={{
            left: mousePosition.x,
            top: mousePosition.y,
          }}
        />
        
        <div 
          className="mouse-blur"
          style={{
            left: mousePosition.x - 60,
            top: mousePosition.y - 60,
            width: '120px',
            height: '120px',
          }}
        />

        <Navbar />
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-pink"></div>
        </div>
        <Footer />
      </div>
    );
  }

  if (!work) {
    return (
      <div className="grainy-bg min-h-screen overflow-x-hidden relative">
        <div 
          className={`custom-cursor ${isHovering ? 'hover' : ''} ${isOverFooter ? 'footer' : ''}`}
          style={{
            left: mousePosition.x,
            top: mousePosition.y,
          }}
        />
        
        <div 
          className="mouse-blur"
          style={{
            left: mousePosition.x - 60,
            top: mousePosition.y - 60,
            width: '120px',
            height: '120px',
          }}
        />

        <Navbar />
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-brand-dark mb-4">Work Not Found</h1>
            <p className="text-gray-600 mb-6">The work you&apos;re looking for doesn&apos;t exist or couldn&apos;t be found.</p>
            <Button onClick={() => router.push('/search')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Search
            </Button>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="grainy-bg min-h-screen overflow-x-hidden relative">
      <div 
        className={`custom-cursor ${isHovering ? 'hover' : ''} ${isOverFooter ? 'footer' : ''}`}
        style={{
          left: mousePosition.x,
          top: mousePosition.y,
        }}
      />
      
      <div 
        className="mouse-blur"
        style={{
          left: mousePosition.x - 60,
          top: mousePosition.y - 60,
          width: '120px',
          height: '120px',
        }}
      />

      <Navbar />
      
      <div className="pt-40 pb-20 px-4 max-w-4xl mx-auto work-detail-content">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          {/* Mobile Action Buttons - Show on small screens only */}
          <div className="flex flex-col sm:flex-row gap-2 mb-6 lg:hidden">
            <div className="gradient-border-simple w-full sm:w-auto">
              <button
                onClick={() => router.back()}
                className="gradient-border-simple-content text-brand-dark hover:text-brand-pink transition-colors duration-300 font-medium text-sm w-full"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Search
              </button>
            </div>
            <Button 
              size="sm" 
              onClick={copyToClipboard}
              className="bg-gradient-to-r from-brand-pink to-brand-purple hover:from-brand-pink/90 hover:to-brand-purple/90 text-white border-0 w-full sm:w-auto"
            >
              <Copy className="h-4 w-4 mr-2" />
              {copySuccess ? 'Copied!' : 'Copy Link'}
            </Button>
          </div>

          {/* Header */}
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between mb-8 gap-4">
            <div className="flex-1">
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-brand-dark mb-4">{work.title}</h1>
              <div className="flex flex-wrap items-center gap-3 sm:gap-4 text-sm sm:text-base lg:text-lg text-gray-600 mb-4">
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 sm:h-5 sm:w-5" />
                  <span className="break-words">{work.author_name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 sm:h-5 sm:w-5" />
                  {work.publication_year}
                </div>
                <div className="flex items-center gap-2">
                  <Globe className="h-4 w-4 sm:h-5 sm:w-5" />
                  {work.country}
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-4 w-4 sm:h-5 sm:w-5 flex items-center justify-center text-brand-purple font-bold">•</span>
                  <span className="capitalize">{work.work_type}</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {getStatusIcon(work.status)}
                <span className={`px-3 sm:px-4 py-2 rounded-full text-sm sm:text-base lg:text-lg font-medium ${
                  work.status === 'Public Domain' 
                    ? 'bg-green-100 text-green-700'
                    : work.status === 'Under Copyright'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {work.status}
                </span>
              </div>
            </div>

            {/* Desktop Action Buttons - Show on large screens only */}
            <div className="hidden lg:flex flex-col sm:flex-row gap-2 lg:mt-0">
              <div className="gradient-border-simple w-full sm:w-auto">
                <button
                  onClick={() => router.back()}
                  className="gradient-border-simple-content text-brand-dark hover:text-brand-pink transition-colors duration-300 font-medium text-sm w-full"
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Search
                </button>
              </div>
              <Button 
                size="sm" 
                onClick={copyToClipboard}
                className="bg-gradient-to-r from-brand-pink to-brand-purple hover:from-brand-pink/90 hover:to-brand-purple/90 text-white border-0 w-full sm:w-auto"
              >
                <Copy className="h-4 w-4 mr-2" />
                {copySuccess ? 'Copied!' : 'Copy Link'}
              </Button>
            </div>
          </div>

          {/* Copyright Analysis */}
          <Card className="mb-6 sm:mb-8">
            <CardHeader>
              <CardTitle className="text-lg sm:text-xl text-brand-dark">Copyright Analysis</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm sm:text-base text-gray-700 leading-relaxed">{work.notes}</p>
              
              {work.enters_public_domain && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Clock className="h-5 w-5" />
                  <span>
                    {work.status === 'Public Domain' 
                      ? `Entered public domain: ${work.enters_public_domain}`
                      : `Enters public domain: ${work.enters_public_domain}`
                    }
                  </span>
                </div>
              )}

              <div className="flex items-center gap-2 text-sm sm:text-base text-gray-600">
                <span>Confidence Score: {(work.confidence_score * 100).toFixed(0)}%</span>
              </div>
            </CardContent>
          </Card>

          {/* Source Links */}
          {((work.source_links && Object.keys(work.source_links).length > 0) || (work.source && work.source.trim())) && (
            <Card className="mb-6 sm:mb-8">
              <CardHeader>
                <CardTitle className="text-lg sm:text-xl text-brand-dark">Sources & References</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3">
                  {/* Handle legacy source_links object format */}
                  {work.source_links && Object.keys(work.source_links).length > 0 && 
                    Object.entries(work.source_links).map(([source, url]) => (
                      <Button
                        key={source}
                        variant="outline"
                        className="justify-start h-auto p-3 sm:p-4 text-left"
                        onClick={() => window.open(url, '_blank')}
                      >
                        <ExternalLink className="h-4 w-4 mr-3 flex-shrink-0" />
                        <div className="text-left min-w-0 flex-1">
                          <div className="font-medium text-sm sm:text-base">{source.toUpperCase()}</div>
                          <div className="text-xs sm:text-sm text-gray-600 truncate">{url}</div>
                        </div>
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
                        const lccnMatch = trimmedUrl.match(/lccn\.loc\.gov\/(\w+)/);
                        sourceName = lccnMatch ? `Library of Congress (${lccnMatch[1]})` : 'Library of Congress';
                      } else if (trimmedUrl.includes('loc.gov') || trimmedUrl.includes('catalog.loc.gov')) {
                        sourceName = 'Library of Congress';
                      } else if (trimmedUrl.includes('hathitrust.org')) {
                        sourceName = 'HathiTrust';
                      } else if (trimmedUrl.includes('archive.org')) {
                        sourceName = 'Internet Archive';
                      } else if (trimmedUrl.includes('gutenberg.org')) {
                        sourceName = 'Project Gutenberg';
                      }
                      
                      return (
                        <Button
                          key={`work-source-${index}-${trimmedUrl.slice(0, 20)}`}
                          variant="outline"
                          className="justify-start h-auto p-3 sm:p-4 text-left"
                          onClick={() => window.open(trimmedUrl, '_blank')}
                        >
                          <ExternalLink className="h-4 w-4 mr-3 flex-shrink-0" />
                          <div className="text-left min-w-0 flex-1">
                            <div className="font-medium text-sm sm:text-base">{sourceName}</div>
                            <div className="text-xs sm:text-sm text-gray-600 truncate">{trimmedUrl}</div>
                          </div>
                        </Button>
                      );
                    })
                  }
                </div>
              </CardContent>
            </Card>
          )}

          {/* Analysis Metadata */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg sm:text-xl text-brand-dark">Analysis Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid sm:grid-cols-2 gap-3 sm:gap-4 text-xs sm:text-sm">
                <div className="flex flex-col sm:flex-row sm:items-center">
                  <span className="font-medium text-gray-700 mb-1 sm:mb-0">Work Type:</span>
                  <span className="sm:ml-2 capitalize">{work.work_type}</span>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center">
                  <span className="font-medium text-gray-700 mb-1 sm:mb-0">Category:</span>
                  <span className="sm:ml-2">{work.category}</span>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center">
                  <span className="font-medium text-gray-700 mb-1 sm:mb-0">Published:</span>
                  <span className="sm:ml-2">{work.published ? 'Yes' : 'No'}</span>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center">
                  <span className="font-medium text-gray-700 mb-1 sm:mb-0">Last Analyzed:</span>
                  <span className="sm:ml-2">{new Date(work.queried_at).toLocaleDateString()}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <Footer />
    </div>
  );
}

export default function WorkDetailPage() {
  return (
    <Suspense fallback={
      <div className="grainy-bg min-h-screen overflow-x-hidden relative">
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-pink"></div>
        </div>
      </div>
    }>
      <WorkDetailContent />
    </Suspense>
  );
}