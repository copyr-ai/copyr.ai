'use client';

import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Calendar, User, Globe, Clock, ExternalLink, Eye } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { getStatusIcon, getCategoryIcon, getStatusColor } from '../../lib/workUtils';

export default function WorkCard({ work, variant = 'full', index = 0 }) {
  const router = useRouter();

  if (variant === 'compact') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: index * 0.05 }}
        onClick={() => router.push(`/work/${work.slug}`)}
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
        <Card className="bg-white/50 backdrop-blur-sm rounded-2xl border border-gray-200 hover:shadow-lg transition-all duration-300 hover:-translate-y-1 cursor-pointer group"
              onClick={() => router.push(`/work/${work.slug}`)}>
          <CardHeader className="pb-3">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-gradient-to-r from-brand-pink/10 to-brand-purple/10 rounded-lg">
                {getCategoryIcon(work.category)}
              </div>
              <div className="flex-1">
                <CardTitle className="text-lg text-brand-dark group-hover:text-brand-pink transition-colors line-clamp-2">
                  {work.title}
                </CardTitle>
                <p className="text-sm text-gray-600 mt-1">{work.author_name}</p>
              </div>
              {getStatusIcon(work.status)}
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2 text-gray-600">
                <Calendar className="h-3 w-3" />
                {work.publication_year}
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(work.status)}`}>
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
                  <span className="text-sm text-gray-600">
                    Confidence: {(work.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Copyright Analysis */}
          <div className="bg-gray-50/80 p-4 rounded-lg">
            <h4 className="font-semibold text-brand-dark mb-2">Copyright Analysis</h4>
            <p className="text-sm text-gray-600 mb-3">{work.notes}</p>
            
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
          {work.source_links && Object.keys(work.source_links).length > 0 && (
            <div>
              <h4 className="font-semibold text-brand-dark mb-2">Sources</h4>
              <div className="flex flex-wrap gap-2">
                {Object.entries(work.source_links).map(([source, url]) => (
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
                ))}
              </div>
            </div>
          )}
          
          {/* Action Button */}
          <div className="pt-4 border-t border-gray-200">
            <Button
              onClick={() => router.push(`/work/${work.slug}`)}
              className="w-full bg-gradient-to-r from-brand-pink to-brand-purple hover:from-brand-pink/90 hover:to-brand-purple/90 text-white"
            >
              <Eye className="h-4 w-4 mr-2" />
              View Details
            </Button>
          </div>
          
          {/* Metadata */}
          <div className="text-xs text-gray-500 pt-2">
            Last analyzed: {new Date(work.queried_at).toLocaleString()}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}