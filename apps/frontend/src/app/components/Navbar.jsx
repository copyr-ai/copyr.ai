'use client'

import Image from "next/image"
import { motion } from "framer-motion"
import { Button } from "../components/ui/button"
import { useEffect, useState } from "react"

export default function Navbar() {
  const [isHidden, setIsHidden] = useState(false)
  
  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY
      const viewportHeight = window.innerHeight
      
      // Check if we're on any search page (including with query parameters)
      const isSearchPage = window.location.pathname.startsWith('/search')
      
      if (isSearchPage) {
        // On search page, hide navbar much earlier - before searchbar area
        // Search bar area starts around 32 (pt-32) which is ~128px from top
        // Hide navbar when we scroll past 80px on search page
        setIsHidden(scrollY > 80)
        return
      }
      
      // For other pages, use the original logic
      // Check if any main content is overlapping with navbar area (top 100px)
      const contentElements = document.querySelectorAll('main, [data-main-content], .search-content, .work-content')
      let hasOverlap = false
      
      contentElements.forEach(element => {
        if (element) {
          const rect = element.getBoundingClientRect()
          // Check if content is in the navbar area (top 100px of viewport)
          if (rect.top < 100 && rect.bottom > 0) {
            hasOverlap = true
          }
        }
      })
      
      // Also check for specific containers that might indicate main content
      const searchContainer = document.querySelector('[data-search-results]')
      const workContainer = document.querySelector('.work-detail-content')
      
      if (searchContainer) {
        const rect = searchContainer.getBoundingClientRect()
        if (rect.top < 100 && rect.bottom > 0) {
          hasOverlap = true
        }
      }
      
      if (workContainer) {
        const rect = workContainer.getBoundingClientRect()
        if (rect.top < 100 && rect.bottom > 0) {
          hasOverlap = true
        }
      }
      
      // Only hide navbar when:
      // 1. We've scrolled past initial section (scrollY > 150)
      // 2. AND content is overlapping with navbar area
      const pastInitialSection = scrollY > 150
      
      setIsHidden(pastInitialSection && hasOverlap)
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    // Run once on mount to set initial state
    handleScroll()
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const scrollToTop = () => {
    window.scrollTo({ 
      top: 0, 
      behavior: 'smooth' 
    })
  }

  const goToHomepage = () => {
    window.location.href = '/'
  }

  const goToSearch = () => {
    window.location.href = '/search'
  }

  return (
    <motion.nav 
      initial={{ opacity: 0, y: -20 }}
      animate={{ 
        opacity: isHidden ? 0 : 1, 
        y: isHidden ? -20 : 0 
      }}
      transition={{ duration: 0.3 }}
      className="fixed top-6 left-1/2 transform -translate-x-1/2 z-50 bg-white/90 backdrop-blur-md rounded-full shadow-lg border border-gray-200 overflow-visible"
    >
      <div className="flex items-center justify-between px-8 py-4">
        {/* Logo */}
        <div className="flex items-center cursor-pointer hover:opacity-80 transition-opacity" onClick={goToHomepage}>
          <Image
            src="/brand-copyr.ai-light.svg"
            alt="copyr.ai"
            width={120}
            height={36}
            className="h-10 w-auto sm:h-12 md:h-10 lg:h-8"
            priority
          />
        </div>

        {/* Navigation Links */}
        <div className="hidden md:flex items-center space-x-8 mx-12">
          <a href="#features" className="text-gray-600 hover:text-gray-900 hover:font-semibold font-medium transition-all duration-200">Features</a>
          <a href="#about" className="text-gray-600 hover:text-gray-900 hover:font-semibold font-medium transition-all duration-200">About</a>
          <a 
            href="https://linkedin.com/company/copyr-ai" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-gray-600 hover:text-gray-900 hover:font-semibold font-medium transition-all duration-200"
          >
            Connect
          </a>
          <Button
            onClick={goToSearch}
            className="px-4 py-2 bg-gradient-to-r from-brand-pink to-brand-purple hover:from-brand-pink/90 hover:to-brand-purple/90 text-white font-semibold text-xs tracking-wide rounded-full shadow-md hover:shadow-lg transition-all duration-300 transform hover:-translate-y-0.5 h-auto group"
          >
            <span>Try It Now</span>
            <svg 
              className="w-3 h-3 ml-1.5 animate-arrow transition-transform duration-300" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </Button>
        </div>

      </div>
    </motion.nav>
  )
}
