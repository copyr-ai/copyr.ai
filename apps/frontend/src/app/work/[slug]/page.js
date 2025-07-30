'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { 
  ArrowLeft, Share2, Download, ExternalLink, 
  Calendar, User, Globe, Clock, CheckCircle, 
  XCircle, AlertCircle, Copy
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import Navbar from '../../components/Navbar';
import Footer from '../../components/Footer';

import mockData from '../../../data/mockWorks.json';

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
      // Throttle updates using requestAnimationFrame
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      
      rafRef.current = requestAnimationFrame(() => {
        const now = Date.now();
        // Limit updates to 60fps max
        if (now - lastUpdate.current > 16) {
          setMousePosition({ x: e.clientX, y: e.clientY });
          
          // Check footer less frequently to improve performance
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
    
    // Use passive listeners for better performance
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

export default function WorkDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { mousePosition, isHovering, isOverFooter } = useCustomCursor();
  const [work, setWork] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [copySuccess, setCopySuccess] = useState(false);

  useEffect(() => {
    // Find work by slug
    const foundWork = mockSearchResults.find(w => w.slug === params.slug);
    if (foundWork) {
      setWork(foundWork);
    }
    setIsLoading(false);
  }, [params.slug]);

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
        {/* Custom Cursor & Effects */}
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
            left: mousePosition.x - 100,
            top: mousePosition.y - 100,
            width: '200px',
            height: '200px',
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
        {/* Custom Cursor & Effects */}
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
            left: mousePosition.x - 100,
            top: mousePosition.y - 100,
            width: '200px',
            height: '200px',
          }}
        />

        <Navbar />
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-brand-dark mb-4">Work Not Found</h1>
            <p className="text-gray-600 mb-6">The work you&apos;re looking for doesn&apos;t exist.</p>
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
      {/* Custom Cursor & Effects */}
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
          left: mousePosition.x - 100,
          top: mousePosition.y - 100,
          width: '200px',
          height: '200px',
        }}
      />

      <Navbar />
      
      <div className="pt-32 pb-20 px-4 max-w-4xl mx-auto work-detail-content">
        {/* Back Button */}
        <Button 
          variant="ghost" 
          onClick={() => router.back()}
          className="mb-6 hover:bg-brand-pink/10"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Search
        </Button>

        {/* Main Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-8">
            <div className="flex-1">
              <h1 className="text-4xl font-bold text-brand-dark mb-4">{work.title}</h1>
              <div className="flex items-center gap-4 text-lg text-gray-600 mb-4">
                <div className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  {work.author_name}
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  {work.publication_year}
                </div>
                <div className="flex items-center gap-2">
                  <Globe className="h-5 w-5" />
                  {work.country}
                </div>
              </div>
              <div className="flex items-center gap-3">
                {getStatusIcon(work.status)}
                <span className={`px-4 py-2 rounded-full text-lg font-medium ${
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

            {/* Share Buttons */}
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={copyToClipboard}>
                <Copy className="h-4 w-4 mr-2" />
                {copySuccess ? 'Copied!' : 'Copy Link'}
              </Button>
            </div>
          </div>

          {/* Copyright Analysis */}
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="text-xl text-brand-dark">Copyright Analysis</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-gray-700 leading-relaxed">{work.notes}</p>
              
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

              <div className="flex items-center gap-2 text-gray-600">
                <span>Confidence Score: {(work.confidence_score * 100).toFixed(0)}%</span>
              </div>
            </CardContent>
          </Card>

          {/* Source Links */}
          {work.source_links && Object.keys(work.source_links).length > 0 && (
            <Card className="mb-8">
              <CardHeader>
                <CardTitle className="text-xl text-brand-dark">Sources & References</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3">
                  {Object.entries(work.source_links).map(([source, url]) => (
                    <Button
                      key={source}
                      variant="outline"
                      className="justify-start h-auto p-4"
                      onClick={() => window.open(url, '_blank')}
                    >
                      <ExternalLink className="h-4 w-4 mr-3" />
                      <div className="text-left">
                        <div className="font-medium">{source.toUpperCase()}</div>
                        <div className="text-sm text-gray-600 truncate">{url}</div>
                      </div>
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Analysis Metadata */}
          <Card>
            <CardHeader>
              <CardTitle className="text-xl text-brand-dark">Analysis Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Work Type:</span>
                  <span className="ml-2 capitalize">{work.work_type}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Category:</span>
                  <span className="ml-2">{work.category}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Published:</span>
                  <span className="ml-2">{work.published ? 'Yes' : 'No'}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Last Analyzed:</span>
                  <span className="ml-2">{new Date(work.queried_at).toLocaleDateString()}</span>
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